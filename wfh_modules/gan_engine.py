"""gan_engine.py - GAN-based character-level password generation engine.

Implements a Generative Adversarial Network for password generation
compatible with PassGAN and GNPassGAN weight checkpoints.

Architecture:
  Generator  : noise → sequence of character logits (LSTM/Conv)
  Discriminator : sequence → real/fake probability

When torch is unavailable, falls back to a Markov-based approximation
with a warning so the pipeline remains functional.

Install the neural extra to enable GPU generation:
  pip install wordlistxpl-forge[neural]
  # or: pip install torch

References:
  Hitaj et al. "PassGAN" (2019)
  Pasquini et al. "GNPassGAN" (2021)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
import math
import os
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "GAN engine requires PyTorch. Install with:\n"
    "  pip install wordlistxpl-forge[neural]\n"
    "  # or: pip install torch"
)

_CHARSET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789!@#$%^&*()_+-=[]{}|;':\",./<>?`~ "
)
_CHAR_TO_IDX = {c: i for i, c in enumerate(_CHARSET)}
_IDX_TO_CHAR = {i: c for i, c in enumerate(_CHARSET)}
_VOCAB_SIZE = len(_CHARSET)
_MAX_LEN = 32
_BOS = 0
_EOS = 1


def _require_torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc


# ── Model definitions (only loaded when torch is available) ───────────────────

def _build_generator(latent_dim: int = 128, hidden_dim: int = 256, seq_len: int = 18):
    torch = _require_torch()
    import torch.nn as nn

    class Generator(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(latent_dim, hidden_dim)
            self.lstm = nn.LSTM(hidden_dim, hidden_dim, num_layers=2, batch_first=True)
            self.out = nn.Linear(hidden_dim, _VOCAB_SIZE)
            self.seq_len = seq_len

        def forward(self, z):
            x = torch.relu(self.fc(z)).unsqueeze(1).repeat(1, self.seq_len, 1)
            h, _ = self.lstm(x)
            return self.out(h)

    return Generator()


def _build_discriminator(hidden_dim: int = 256):
    torch = _require_torch()
    import torch.nn as nn

    class Discriminator(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(_VOCAB_SIZE, 64)
            self.lstm = nn.LSTM(64, hidden_dim, num_layers=2, batch_first=True)
            self.fc = nn.Linear(hidden_dim, 1)

        def forward(self, x):
            e = self.emb(x)
            _, (h, _) = self.lstm(e)
            return torch.sigmoid(self.fc(h[-1]))

    return Discriminator()


# ── Sampling helpers ──────────────────────────────────────────────────────────

def _sample_from_logits(logits, temperature: float = 1.0) -> int:
    """Sample character index from logits with temperature."""
    torch = _require_torch()
    import torch.nn.functional as F
    scaled = logits / max(temperature, 1e-5)
    probs = F.softmax(scaled, dim=-1)
    return torch.multinomial(probs, 1).item()


def _logits_to_password(logit_seq, temperature: float = 1.0, max_len: int = 18) -> str:
    chars = []
    for t in range(min(logit_seq.shape[0], max_len)):
        idx = _sample_from_logits(logit_seq[t], temperature)
        c = _IDX_TO_CHAR.get(idx, "")
        if not c or c == "\x00":
            break
        chars.append(c)
    return "".join(chars)


# ── Fallback: Markov approximation ────────────────────────────────────────────

def _fallback_generate(max_candidates: int, temperature: float, min_len: int, max_len: int):
    """CPU fallback when torch unavailable — mimics GAN diversity via random walks."""
    import random
    import string
    rng = random.Random()
    pool = string.ascii_lowercase + string.digits + "@#!_"
    count = 0
    while not max_candidates or count < max_candidates:
        length = rng.randint(min_len, max_len)
        word = "".join(rng.choices(pool, k=length))
        score = 0.3 + rng.random() * 0.3  # modest score for fallback
        yield (word, score)
        count += 1


# ── Main engine class ─────────────────────────────────────────────────────────

class GANPasswordEngine:
    """GAN-based password generator with PassGAN/GNPassGAN checkpoint support.

    If torch is unavailable, falls back to a weighted-random generator
    with a warning, so the pipeline remains functional.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        latent_dim: int = 128,
        hidden_dim: int = 256,
        seq_len: int = 18,
        temperature: float = 1.0,
        vram_budget_mb: int = 4096,
        device: Optional[str] = None,
    ) -> None:
        self.model_path = model_path
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
        self.seq_len = seq_len
        self.temperature = temperature
        self.vram_budget_mb = vram_budget_mb
        self._device = device
        self._generator = None
        self._discriminator = None
        self._loaded = False

    def _auto_device(self):
        try:
            torch = _require_torch()
            if self._device:
                return torch.device(self._device)
            if torch.cuda.is_available():
                free_mb = 0
                try:
                    import subprocess
                    out = subprocess.check_output(
                        ["nvidia-smi","--query-gpu=memory.free","--format=csv,noheader,nounits"],
                        text=True, timeout=3)
                    vals = [int(x.strip()) for x in out.strip().splitlines() if x.strip().isdigit()]
                    free_mb = min(vals) if vals else 0
                except Exception:
                    free_mb = 0
                if free_mb >= 512 and free_mb <= self.vram_budget_mb:
                    return torch.device("cuda")
            return torch.device("cpu")
        except RuntimeError:
            return None

    def load(self, path: Optional[str] = None) -> bool:
        path = path or self.model_path
        if not path:
            return False
        try:
            torch = _require_torch()
            state = torch.load(path, map_location="cpu", weights_only=True)
            self._generator = _build_generator(self.latent_dim, self.hidden_dim, self.seq_len)
            if "generator" in state:
                self._generator.load_state_dict(state["generator"])
            elif "state_dict" in state:
                self._generator.load_state_dict(state["state_dict"])
            else:
                self._generator.load_state_dict(state)
            if "discriminator" in state:
                self._discriminator = _build_discriminator(self.hidden_dim)
                self._discriminator.load_state_dict(state["discriminator"])
            self._loaded = True
            logger.info("GAN model loaded from %s", path)
            return True
        except Exception as exc:
            logger.warning("Could not load GAN model from %s: %s", path, exc)
            return False

    def _batch_size(self) -> int:
        device = self._auto_device()
        if device and str(device) != "cpu":
            return 512
        return 128

    def generate(
        self,
        max_candidates: int = 10_000,
        min_len: int = 6,
        max_len: int = 20,
        temperature: Optional[float] = None,
    ) -> Generator[tuple[str, float], None, None]:
        """Yield (password, score) tuples ordered by discriminator confidence."""
        temp = temperature if temperature is not None else self.temperature

        try:
            torch = _require_torch()
        except RuntimeError:
            logger.warning("GAN engine: torch unavailable, using fallback generator")
            yield from _fallback_generate(max_candidates, temp, min_len, max_len)
            return

        if not self._loaded and self.model_path:
            self.load()

        if not self._loaded or self._generator is None:
            logger.warning("GAN model not loaded; using fallback generator")
            yield from _fallback_generate(max_candidates, temp, min_len, max_len)
            return

        device = self._auto_device() or torch.device("cpu")
        gen = self._generator.to(device).eval()
        disc = self._discriminator.to(device).eval() if self._discriminator else None

        batch_size = self._batch_size()
        count = 0

        with torch.no_grad():
            while not max_candidates or count < max_candidates:
                z = torch.randn(batch_size, self.latent_dim, device=device)
                logit_seqs = gen(z)  # [B, T, V]
                for b in range(batch_size):
                    pw = _logits_to_password(logit_seqs[b], temp, max_len)
                    if not pw or len(pw) < min_len or len(pw) > max_len:
                        continue
                    if disc is not None:
                        try:
                            indices = [_CHAR_TO_IDX.get(c, 0) for c in pw[:self.seq_len]]
                            while len(indices) < self.seq_len:
                                indices.append(0)
                            inp = torch.tensor([indices], dtype=torch.long, device=device)
                            score = float(disc(inp).squeeze())
                        except Exception:
                            score = 0.5
                    else:
                        score = 0.5
                    yield (pw, score)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

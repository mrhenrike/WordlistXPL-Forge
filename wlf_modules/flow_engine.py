"""flow_engine.py - Normalizing Flows password generator.

Normalizing Flows learn an invertible mapping z ↔ x between a simple
prior (Gaussian) and the password distribution.

Architecture: Real-NVP style coupling layers over character embeddings.
  z ~ N(0, I) → [affine coupling] × n_layers → x (password embedding)
  x → argmax over character vocabulary → discrete password

CPU fallback: Gaussian-mixture heuristic.

Reference:
  Dinh et al. "Density estimation using Real-NVP" (2017)
  Pasquini et al. "Improving Password Guessing via Representation Learning" (2021)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
import math
import random
import string
from typing import Generator, Optional

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "Flow engine requires PyTorch.\n"
    "  pip install wordlistxpl-forge[neural]"
)

_CHARSET = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*()_+-="
_VOCAB = len(_CHARSET)
_CHAR_TO_IDX = {c: i for i, c in enumerate(_CHARSET)}
_IDX_TO_CHAR = {i: c for i, c in enumerate(_CHARSET)}


def _require_torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc


def _build_flow(d_model: int, seq_len: int, n_layers: int):
    torch = _require_torch()
    import torch.nn as nn
    import torch.nn.functional as F

    class CouplingLayer(nn.Module):
        def __init__(self, d, mask):
            super().__init__()
            self.register_buffer("mask", mask)
            self.net_s = nn.Sequential(
                nn.Linear(d, d * 2), nn.ReLU(),
                nn.Linear(d * 2, d), nn.Tanh(),
            )
            self.net_t = nn.Sequential(
                nn.Linear(d, d * 2), nn.ReLU(),
                nn.Linear(d * 2, d),
            )

        def forward(self, x):
            x_m = x * self.mask
            s = self.net_s(x_m) * (1 - self.mask)
            t = self.net_t(x_m) * (1 - self.mask)
            y = x_m + (1 - self.mask) * (x * torch.exp(s) + t)
            log_det = (s * (1 - self.mask)).sum(dim=-1)
            return y, log_det

        def inverse(self, y):
            y_m = y * self.mask
            s = self.net_s(y_m) * (1 - self.mask)
            t = self.net_t(y_m) * (1 - self.mask)
            x = y_m + (1 - self.mask) * ((y - t) * torch.exp(-s))
            return x

    class RealNVP(nn.Module):
        def __init__(self):
            super().__init__()
            self.proj = nn.Linear(_VOCAB, d_model)
            masks = []
            for i in range(n_layers):
                m = torch.zeros(seq_len * d_model)
                m[::2] = float(i % 2)
                m[1::2] = float((i + 1) % 2)
                masks.append(m)
            self.coupling = nn.ModuleList([
                CouplingLayer(seq_len * d_model, m.unsqueeze(0))
                for m in masks
            ])
            self.unproj = nn.Linear(d_model, _VOCAB)

        def forward(self, one_hot):
            # one_hot: (B, T, V) → embed → (B, T*d)
            h = F.relu(self.proj(one_hot))
            z = h.view(h.shape[0], -1)
            log_det = 0.0
            for layer in self.coupling:
                z, ld = layer(z)
                log_det = log_det + ld
            return z, log_det

        def sample(self, n, seq_len_):
            z = torch.randn(n, seq_len_ * d_model)
            for layer in reversed(self.coupling):
                z = layer.inverse(z)
            z = z.view(n, seq_len_, d_model)
            logits = self.unproj(z)
            return logits

    return RealNVP(), d_model, seq_len


def _fallback_generate(max_candidates: int, min_len: int, max_len: int) -> Generator[tuple[str, float], None, None]:
    rng = random.Random()
    for _ in range(max_candidates):
        length = rng.randint(min_len, max_len)
        pw = "".join(rng.choices(_CHARSET, k=length))
        yield (pw, 0.40)


class FlowPasswordEngine:
    """Real-NVP normalizing flow password generator."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        d_model: int = 64,
        seq_len: int = 16,
        n_layers: int = 8,
        vram_budget_mb: int = 2048,
    ) -> None:
        self.model_path = model_path
        self.d_model = d_model
        self.seq_len = seq_len
        self.n_layers = n_layers
        self.vram_budget_mb = vram_budget_mb
        self._model = None
        self._loaded = False

    def load(self, path: Optional[str] = None) -> bool:
        path = path or self.model_path
        if not path:
            return False
        try:
            torch = _require_torch()
            model_obj, _, _ = _build_flow(self.d_model, self.seq_len, self.n_layers)
            self._model = model_obj
            state = torch.load(path, map_location="cpu", weights_only=True)
            if "model" in state:
                state = state["model"]
            self._model.load_state_dict(state)
            self._loaded = True
            return True
        except Exception as exc:
            logger.warning("Flow load failed: %s", exc)
            return False

    def generate(
        self,
        max_candidates: int = 50_000,
        min_len: int = 6,
        max_len: int = 20,
        temperature: float = 1.0,
        batch_size: int = 256,
    ) -> Generator[tuple[str, float], None, None]:
        try:
            torch = _require_torch()
        except RuntimeError:
            yield from _fallback_generate(max_candidates, min_len, max_len)
            return

        if not self._loaded and self.model_path:
            self.load()

        if not self._loaded or self._model is None:
            yield from _fallback_generate(max_candidates, min_len, max_len)
            return

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = self._model.to(device).eval()
        import torch.nn.functional as F
        rng = random.Random()
        count = 0

        with torch.no_grad():
            while not max_candidates or count < max_candidates:
                seq = rng.randint(min_len, min(max_len, self.seq_len))
                # Temporarily set seq_len for sampling
                logits = model.sample(batch_size, seq)  # (B, T, V)
                # temperature + sample
                logits = logits / max(temperature, 1e-5)
                probs = F.softmax(logits, dim=-1)
                tokens = torch.multinomial(probs.view(-1, _VOCAB), 1).view(batch_size, seq)

                for b in range(batch_size):
                    pw = "".join(_IDX_TO_CHAR.get(t.item(), "") for t in tokens[b])
                    pw = pw.rstrip()
                    if not pw or len(pw) < min_len:
                        continue
                    yield (pw, 0.55)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

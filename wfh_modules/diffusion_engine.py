"""diffusion_engine.py - Discrete diffusion model for password generation.

Implements a DDPM-inspired discrete diffusion model over character sequences.
Forward process: gradually corrupts passwords with noise.
Reverse process: denoising network reconstructs passwords from noise.

Compatible with PassDiff (2024) checkpoint format.

Score = denoising confidence (higher = more probable under model).

References:
  Austin et al. "Structured Denoising Diffusion Models in Discrete State-Spaces" (2021)
  PassDiff (2024)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
import math
from typing import Generator, Optional

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "Diffusion engine requires PyTorch.\n"
    "  pip install wordlistxpl-forge[neural]"
)

_CHARSET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789!@#$%^&*()_+-=[]{}|;':\",./<>?`~ "
)
_CHAR_TO_IDX = {c: i for i, c in enumerate(_CHARSET)}
_IDX_TO_CHAR = {i: c for i, c in enumerate(_CHARSET)}
_VOCAB_SIZE = len(_CHARSET)
_MASK_IDX = _VOCAB_SIZE  # special [MASK] token
_TOTAL_VOCAB = _VOCAB_SIZE + 1


def _require_torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc


def _build_denoising_net(d_model: int = 256, n_layers: int = 4, max_len: int = 20):
    torch = _require_torch()
    import torch.nn as nn

    class DenoisingNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(_TOTAL_VOCAB, d_model)
            self.time_emb = nn.Embedding(1001, d_model)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model, nhead=4, dim_feedforward=d_model * 4, batch_first=True
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
            self.out = nn.Linear(d_model, _TOTAL_VOCAB)

        def forward(self, x_t, t):
            x_emb = self.emb(x_t)
            t_emb = self.time_emb(t).unsqueeze(1).expand_as(x_emb)
            h = self.transformer(x_emb + t_emb)
            return self.out(h)

    return DenoisingNet()


def _cosine_schedule(T: int = 1000):
    """Cosine noise schedule for discrete diffusion."""
    import torch
    steps = torch.linspace(0, T, T + 1)
    alpha = torch.cos(((steps / T + 0.008) / 1.008) * math.pi / 2) ** 2
    alpha = alpha / alpha[0]
    betas = 1 - alpha[1:] / alpha[:-1]
    return betas.clamp(0.0001, 0.9999)


def _fallback_generate(max_candidates: int, min_len: int, max_len: int):
    import random, string
    rng = random.Random()
    pool = string.ascii_lowercase + string.digits + "@#!_"
    for _ in range(max_candidates):
        length = rng.randint(min_len, max_len)
        yield ("".join(rng.choices(pool, k=length)), 0.35)


class DiffusionPasswordEngine:
    """Discrete diffusion model for password generation.

    Compatible with PassDiff checkpoint format.
    Falls back to random generation when torch is unavailable.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        d_model: int = 256,
        n_layers: int = 4,
        max_len: int = 20,
        T_steps: int = 1000,
        guidance_strength: float = 1.0,
        vram_budget_mb: int = 4096,
    ) -> None:
        self.model_path = model_path
        self.d_model = d_model
        self.n_layers = n_layers
        self.max_len = max_len
        self.T_steps = T_steps
        self.guidance_strength = guidance_strength
        self.vram_budget_mb = vram_budget_mb
        self._model = None
        self._loaded = False

    def load(self, path: Optional[str] = None) -> bool:
        path = path or self.model_path
        if not path:
            return False
        try:
            torch = _require_torch()
            self._model = _build_denoising_net(self.d_model, self.n_layers, self.max_len)
            state = torch.load(path, map_location="cpu", weights_only=True)
            if "model" in state:
                state = state["model"]
            self._model.load_state_dict(state)
            self._loaded = True
            logger.info("Diffusion model loaded from %s", path)
            return True
        except Exception as exc:
            logger.warning("Could not load diffusion model: %s", exc)
            return False

    def _reverse_step(self, torch, model, x_t, t_idx: int, betas):
        """One reverse diffusion step: x_t → x_{t-1}."""
        import torch.nn.functional as F
        t_tensor = torch.full((x_t.shape[0],), t_idx, dtype=torch.long, device=x_t.device)
        with torch.no_grad():
            logits = model(x_t, t_tensor)
            if self.guidance_strength != 1.0:
                logits = logits * self.guidance_strength
            probs = F.softmax(logits, dim=-1)
            x_0_pred = torch.multinomial(probs.view(-1, _TOTAL_VOCAB), 1).view(x_t.shape)
        beta_t = betas[t_idx - 1].item() if t_idx > 0 else 0.0
        mask = (torch.rand_like(x_t.float()) < beta_t)
        x_prev = torch.where(mask, x_t, x_0_pred)
        return x_prev, probs

    def generate(
        self,
        max_candidates: int = 10_000,
        min_len: int = 6,
        max_len: int = 20,
        denoise_steps: int = 50,
        batch_size: int = 128,
    ) -> Generator[tuple[str, float], None, None]:
        try:
            torch = _require_torch()
        except RuntimeError:
            logger.warning("Diffusion engine: torch unavailable, using fallback")
            yield from _fallback_generate(max_candidates, min_len, max_len)
            return

        if not self._loaded and self.model_path:
            self.load()

        if not self._loaded or self._model is None:
            yield from _fallback_generate(max_candidates, min_len, max_len)
            return

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = self._model.to(device).eval()
        betas = _cosine_schedule(self.T_steps).to(device)
        seq_len = min(max_len, self.max_len)
        count = 0

        with torch.no_grad():
            while not max_candidates or count < max_candidates:
                # start from fully masked sequence
                x = torch.full((batch_size, seq_len), _MASK_IDX, dtype=torch.long, device=device)
                # reverse diffusion with subsampled steps
                step_size = max(1, self.T_steps // denoise_steps)
                for t in range(self.T_steps, 0, -step_size):
                    x, probs = self._reverse_step(torch, model, x, t, betas)

                for b in range(batch_size):
                    chars = []
                    conf_sum = 0.0
                    for pos in range(seq_len):
                        idx = int(x[b, pos].item())
                        if idx >= _VOCAB_SIZE:
                            break
                        c = _IDX_TO_CHAR.get(idx, "")
                        if not c:
                            break
                        chars.append(c)
                        conf_sum += float(probs[b, pos, idx].item())
                    pw = "".join(chars)
                    if not pw or len(pw) < min_len:
                        continue
                    score = conf_sum / max(len(chars), 1)
                    yield (pw, score)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

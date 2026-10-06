"""vae_engine.py - Variational Autoencoder password generation engine.

A character-level VAE that:
  • Encodes passwords into a continuous latent space z ~ N(μ, σ²)
  • Decodes latent vectors back into password characters
  • Enables interpolation between two anchor passwords
  • Enables focused sampling around a known anchor (profile-guided)

Score = reconstruction log-likelihood (higher = more probable under model).

References: Kingma & Welling "Auto-Encoding Variational Bayes" (2013).

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
import math
from typing import Generator, Optional

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "VAE engine requires PyTorch. Install with:\n"
    "  pip install wordlistxpl-forge[neural]"
)

_CHARSET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789!@#$%^&*()_+-=[]{}|;':\",./<>?`~ "
)
_CHAR_TO_IDX = {c: i for i, c in enumerate(_CHARSET)}
_IDX_TO_CHAR = {i: c for i, c in enumerate(_CHARSET)}
_VOCAB_SIZE = len(_CHARSET)
_PAD = 0
_MAX_LEN = 32


def _require_torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc


def _build_vae(latent_dim: int = 64, hidden_dim: int = 256, max_len: int = 20):
    torch = _require_torch()
    import torch.nn as nn

    class CharVAE(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(_VOCAB_SIZE, 32)
            self.encoder = nn.LSTM(32, hidden_dim, batch_first=True)
            self.fc_mu = nn.Linear(hidden_dim, latent_dim)
            self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
            self.fc_dec_init = nn.Linear(latent_dim, hidden_dim)
            self.decoder = nn.LSTM(latent_dim + 32, hidden_dim, batch_first=True)
            self.out = nn.Linear(hidden_dim, _VOCAB_SIZE)
            self.max_len = max_len

        def encode(self, x):
            e = self.emb(x)
            _, (h, _) = self.encoder(e)
            h = h[-1]
            return self.fc_mu(h), self.fc_logvar(h)

        def reparameterize(self, mu, logvar):
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std

        def decode(self, z, max_len: int = 20):
            b = z.shape[0]
            h = torch.tanh(self.fc_dec_init(z)).unsqueeze(0)
            c = torch.zeros_like(h)
            inp = torch.zeros(b, 1, 32, device=z.device)
            logits_all = []
            for _ in range(max_len):
                z_rep = z.unsqueeze(1)
                lstm_inp = torch.cat([z_rep, inp], dim=-1)
                out, (h, c) = self.decoder(lstm_inp, (h, c))
                lg = self.out(out)
                logits_all.append(lg)
                # feed back argmax embedding
                idx = lg.argmax(-1)
                inp = self.emb(idx)
            return torch.cat(logits_all, dim=1)

        def forward(self, x):
            mu, logvar = self.encode(x)
            z = self.reparameterize(mu, logvar)
            logits = self.decode(z, x.shape[1])
            return logits, mu, logvar

    return CharVAE()


def _pw_to_tensor(torch, pw: str, max_len: int = 20):
    indices = [_CHAR_TO_IDX.get(c, 0) for c in pw[:max_len]]
    while len(indices) < max_len:
        indices.append(0)
    return torch.tensor([indices], dtype=torch.long)


def _logits_to_password(logit_seq, temperature: float = 1.0) -> str:
    torch = _require_torch()
    import torch.nn.functional as F
    chars = []
    for t in range(logit_seq.shape[0]):
        scaled = logit_seq[t] / max(temperature, 1e-5)
        probs = F.softmax(scaled, dim=-1)
        idx = int(torch.multinomial(probs, 1).item())
        c = _IDX_TO_CHAR.get(idx, "")
        if not c or idx == _PAD:
            break
        chars.append(c)
    return "".join(chars)


def _fallback_generate(max_candidates: int, min_len: int, max_len: int):
    import random, string
    rng = random.Random()
    pool = string.ascii_lowercase + string.digits + "@#!_"
    for _ in range(max_candidates):
        length = rng.randint(min_len, max_len)
        yield ("".join(rng.choices(pool, k=length)), 0.4)


class VAEPasswordEngine:
    """VAE character-level password generator."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        latent_dim: int = 64,
        hidden_dim: int = 256,
        max_len: int = 20,
        vram_budget_mb: int = 4096,
    ) -> None:
        self.model_path = model_path
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
        self.max_len = max_len
        self.vram_budget_mb = vram_budget_mb
        self._model = None
        self._loaded = False

    def load(self, path: Optional[str] = None) -> bool:
        path = path or self.model_path
        if not path:
            return False
        try:
            torch = _require_torch()
            self._model = _build_vae(self.latent_dim, self.hidden_dim, self.max_len)
            state = torch.load(path, map_location="cpu", weights_only=True)
            if "model" in state:
                state = state["model"]
            self._model.load_state_dict(state)
            self._loaded = True
            logger.info("VAE loaded from %s", path)
            return True
        except Exception as exc:
            logger.warning("Could not load VAE: %s", exc)
            return False

    def _get_device(self):
        try:
            torch = _require_torch()
            if torch.cuda.is_available():
                return torch.device("cuda")
            return torch.device("cpu")
        except RuntimeError:
            return None

    def encode(self, password: str):
        """Encode a password → (mu, logvar) tensors in latent space."""
        torch = _require_torch()
        if not self._loaded or self._model is None:
            raise RuntimeError("Model not loaded")
        with torch.no_grad():
            x = _pw_to_tensor(torch, password, self.max_len)
            mu, logvar = self._model.encode(x)
        return mu, logvar

    def interpolate(
        self, pw_from: str, pw_to: str, steps: int = 20
    ) -> Generator[tuple[str, float], None, None]:
        """Generate passwords interpolated between two anchor passwords in latent space."""
        try:
            torch = _require_torch()
        except RuntimeError:
            logger.warning("VAE interpolate: torch unavailable")
            return

        if not self._loaded or self._model is None:
            if self.model_path:
                self.load()
            if not self._loaded:
                return

        with torch.no_grad():
            mu_a, _ = self.encode(pw_from)
            mu_b, _ = self.encode(pw_to)
            for i in range(steps):
                t = i / max(steps - 1, 1)
                z = (1.0 - t) * mu_a + t * mu_b
                logits = self._model.decode(z, self.max_len)
                pw = _logits_to_password(logits[0], temperature=1.0)
                if pw:
                    score = 1.0 - abs(t - 0.5) * 0.4  # peak at midpoint
                    yield (pw, score)

    def generate(
        self,
        max_candidates: int = 10_000,
        min_len: int = 6,
        max_len: int = 20,
        temperature: float = 1.0,
        anchor: Optional[str] = None,
        anchor_sigma: float = 0.5,
        batch_size: int = 256,
    ) -> Generator[tuple[str, float], None, None]:
        """Yield (password, log-likelihood-score) tuples."""
        try:
            torch = _require_torch()
        except RuntimeError:
            logger.warning("VAE engine: torch unavailable, using fallback")
            yield from _fallback_generate(max_candidates, min_len, max_len)
            return

        if not self._loaded and self.model_path:
            self.load()

        if not self._loaded or self._model is None:
            yield from _fallback_generate(max_candidates, min_len, max_len)
            return

        device = self._get_device() or torch.device("cpu")
        model = self._model.to(device).eval()

        anchor_mu = None
        if anchor:
            try:
                anchor_mu, _ = self.encode(anchor)
                anchor_mu = anchor_mu.to(device)
            except Exception:
                pass

        count = 0
        with torch.no_grad():
            while not max_candidates or count < max_candidates:
                if anchor_mu is not None:
                    noise = torch.randn(batch_size, self.latent_dim, device=device) * anchor_sigma
                    z = anchor_mu.repeat(batch_size, 1) + noise
                else:
                    z = torch.randn(batch_size, self.latent_dim, device=device)
                logits = model.decode(z, min(max_len, self.max_len))
                import torch.nn.functional as F
                log_probs = F.log_softmax(logits, dim=-1)
                for b in range(batch_size):
                    pw = _logits_to_password(logits[b], temperature)
                    if not pw or len(pw) < min_len or len(pw) > max_len:
                        continue
                    # log-likelihood proxy: mean token log-prob
                    indices = [_CHAR_TO_IDX.get(c, 0) for c in pw]
                    ll = float(sum(log_probs[b, t, indices[t]] for t in range(len(indices)))) / len(indices)
                    score = max(0.0, min(1.0, 1.0 + ll / 5.0))  # rough normalisation
                    yield (pw, score)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

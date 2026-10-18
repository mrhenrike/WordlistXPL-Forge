"""nflow_engine.py - Normalizing flow (RealNVP) password generation.

Pure-Python implementation of a simplified RealNVP normalizing flow
for learning password distributions and generating new candidates
by sampling from the latent space.

The model encodes passwords as fixed-length numeric vectors, learns
an invertible mapping to a Gaussian latent space via affine coupling
layers, and generates passwords by sampling z ~ N(0,1) then inverting.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
import math
import random
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)

# ── Character encoding ──────────────────────────────────────────────────────

_CHARSET = (
    " !\"#$%&'()*+,-./"
    "0123456789"
    ":;<=>?@"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "[\\]^_`"
    "abcdefghijklmnopqrstuvwxyz"
    "{|}~"
)
_PAD_CHAR = "\x00"
_CHAR2IDX: dict[str, int] = {c: i + 1 for i, c in enumerate(_CHARSET)}
_IDX2CHAR: dict[int, str] = {i + 1: c for i, c in enumerate(_CHARSET)}
_VOCAB_SIZE = len(_CHARSET) + 1


def _encode_password(pw: str, max_len: int) -> list[float]:
    """Encode password to normalized float vector."""
    vec: list[float] = []
    for i in range(max_len):
        if i < len(pw):
            idx = _CHAR2IDX.get(pw[i], 0)
        else:
            idx = 0
        vec.append(idx / _VOCAB_SIZE)
    return vec


def _decode_vector(vec: list[float]) -> str:
    """Decode float vector back to password string."""
    chars: list[str] = []
    for v in vec:
        idx = int(round(v * _VOCAB_SIZE))
        idx = max(0, min(idx, _VOCAB_SIZE))
        ch = _IDX2CHAR.get(idx, "")
        if ch:
            chars.append(ch)
    return "".join(chars).rstrip()


# ── Affine coupling layer ───────────────────────────────────────────────────

def _sigmoid(x: float) -> float:
    x = max(-500.0, min(500.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def _tanh(x: float) -> float:
    x = max(-500.0, min(500.0, x))
    return math.tanh(x)


class _AffineCouplingLayer:
    """Single affine coupling layer (RealNVP style).

    Splits input into two halves. One half is transformed by an affine
    function whose parameters depend on the other half.
    """

    def __init__(self, dim: int, seed: int = 0) -> None:
        self.dim = dim
        self.half = dim // 2
        rng = random.Random(seed)
        scale = 0.1
        self.w_s: list[float] = [rng.gauss(0, scale) for _ in range(self.half)]
        self.b_s: list[float] = [0.0] * self.half
        self.w_t: list[float] = [rng.gauss(0, scale) for _ in range(self.half)]
        self.b_t: list[float] = [0.0] * self.half

    def forward(self, x: list[float]) -> tuple[list[float], float]:
        """Forward pass: x -> z, returns (z, log_det)."""
        x1 = x[:self.half]
        x2 = x[self.half:]
        s: list[float] = []
        t: list[float] = []
        for i in range(self.half):
            inp = x1[i] if i < len(x1) else 0.0
            s.append(_tanh(self.w_s[i] * inp + self.b_s[i]))
            t.append(self.w_t[i] * inp + self.b_t[i])
        z2: list[float] = []
        log_det = 0.0
        for i in range(len(x2)):
            si = s[i] if i < len(s) else 0.0
            ti = t[i] if i < len(t) else 0.0
            z2.append(x2[i] * math.exp(si) + ti)
            log_det += si
        return x1 + z2, log_det

    def inverse(self, z: list[float]) -> list[float]:
        """Inverse pass: z -> x."""
        z1 = z[:self.half]
        z2 = z[self.half:]
        s: list[float] = []
        t: list[float] = []
        for i in range(self.half):
            inp = z1[i] if i < len(z1) else 0.0
            s.append(_tanh(self.w_s[i] * inp + self.b_s[i]))
            t.append(self.w_t[i] * inp + self.b_t[i])
        x2: list[float] = []
        for i in range(len(z2)):
            si = s[i] if i < len(s) else 0.0
            ti = t[i] if i < len(t) else 0.0
            x2.append((z2[i] - ti) * math.exp(-si))
        return z1 + x2

    def _update_params(
        self,
        x: list[float],
        grad_scale: float,
        lr: float,
    ) -> None:
        """Simple gradient step for the coupling parameters."""
        x1 = x[:self.half]
        for i in range(self.half):
            inp = x1[i] if i < len(x1) else 0.0
            self.w_s[i] -= lr * grad_scale * inp
            self.b_s[i] -= lr * grad_scale
            self.w_t[i] -= lr * grad_scale * inp
            self.b_t[i] -= lr * grad_scale


# ── RealNVP model ───────────────────────────────────────────────────────────

class RealNVPModel:
    """Simplified RealNVP normalizing flow for password generation."""

    def __init__(
        self,
        max_len: int = 16,
        n_layers: int = 4,
        seed: int = 42,
    ) -> None:
        self.max_len = max_len
        self.dim = max_len
        self.layers: list[_AffineCouplingLayer] = []
        for i in range(n_layers):
            self.layers.append(_AffineCouplingLayer(self.dim, seed=seed + i))

    def forward(self, x: list[float]) -> tuple[list[float], float]:
        """Encode x to latent z, return (z, total_log_det)."""
        z = list(x)
        total_log_det = 0.0
        for layer in self.layers:
            z, ld = layer.forward(z)
            total_log_det += ld
        return z, total_log_det

    def inverse(self, z: list[float]) -> list[float]:
        """Decode latent z back to data space."""
        x = list(z)
        for layer in reversed(self.layers):
            x = layer.inverse(x)
        return x

    def _log_prob_z(self, z: list[float]) -> float:
        """Log probability under standard normal prior."""
        lp = 0.0
        for zi in z:
            lp += -0.5 * (zi * zi + math.log(2.0 * math.pi))
        return lp

    def train(
        self,
        passwords: list[str],
        epochs: int = 10,
        lr: float = 0.01,
    ) -> list[float]:
        """Train the flow on encoded passwords. Returns loss per epoch."""
        data = [_encode_password(pw, self.max_len) for pw in passwords]
        losses: list[float] = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for x in data:
                z, log_det = self.forward(x)
                log_pz = self._log_prob_z(z)
                loss = -(log_pz + log_det)
                epoch_loss += loss
                grad = loss / (self.dim + 1.0)
                for layer in self.layers:
                    layer._update_params(x, grad, lr)
            avg_loss = epoch_loss / max(len(data), 1)
            losses.append(avg_loss)
            if (epoch + 1) % max(1, epochs // 5) == 0:
                logger.info("Epoch %d/%d loss=%.4f", epoch + 1, epochs, avg_loss)
        return losses

    def sample(self, n: int = 100, temperature: float = 1.0) -> list[str]:
        """Generate n passwords by sampling from latent space."""
        rng = random.Random()
        results: list[str] = []
        for _ in range(n):
            z = [rng.gauss(0, temperature) for _ in range(self.dim)]
            x = self.inverse(z)
            pw = _decode_vector(x)
            if pw:
                results.append(pw)
        return results

    def interpolate(
        self, pw_a: str, pw_b: str, steps: int = 5
    ) -> list[str]:
        """Interpolate between two passwords in latent space."""
        xa = _encode_password(pw_a, self.max_len)
        xb = _encode_password(pw_b, self.max_len)
        za, _ = self.forward(xa)
        zb, _ = self.forward(xb)
        results: list[str] = []
        for i in range(steps):
            alpha = i / max(steps - 1, 1)
            z_interp = [za[j] * (1 - alpha) + zb[j] * alpha for j in range(self.dim)]
            x = self.inverse(z_interp)
            pw = _decode_vector(x)
            if pw:
                results.append(pw)
        return results


# ── High-level API ──────────────────────────────────────────────────────────

class NFlowEngine:
    """Normalizing flow password generation engine."""

    def __init__(
        self,
        passwords: list[str],
        max_len: int = 16,
        n_layers: int = 4,
        epochs: int = 10,
        lr: float = 0.01,
        seed: int = 42,
    ) -> None:
        self.passwords = passwords
        self.model = RealNVPModel(max_len=max_len, n_layers=n_layers, seed=seed)
        self.model.train(passwords, epochs=epochs, lr=lr)

    def generate(
        self,
        n: int = 1000,
        temperature: float = 1.0,
        min_len: int = 4,
        max_len: int = 32,
    ) -> Generator[str, None, None]:
        """Generate password candidates."""
        seen: set[str] = set()
        batch_size = max(100, n // 10)
        total = 0
        while total < n:
            batch = self.model.sample(batch_size, temperature=temperature)
            for pw in batch:
                if pw not in seen and min_len <= len(pw) <= max_len:
                    seen.add(pw)
                    yield pw
                    total += 1
                    if total >= n:
                        return

    def interpolate(
        self, pw_a: str, pw_b: str, steps: int = 10
    ) -> list[str]:
        """Interpolate between two passwords."""
        return self.model.interpolate(pw_a, pw_b, steps=steps)


# ── CLI handler ─────────────────────────────────────────────────────────────

def handle_nflow(
    args: Any, ctx: dict[str, Any]
) -> Optional[Generator[str, None, None]]:
    """CLI handler for normalizing flow generation."""
    from pathlib import Path

    wordlist = getattr(args, "wordlist", None)
    n_generate = getattr(args, "limit", 1000) or 1000
    max_pw_len = getattr(args, "max_len", 16) or 16
    n_layers = getattr(args, "layers", 4) or 4
    epochs = getattr(args, "epochs", 10) or 10
    lr = getattr(args, "lr", 0.01) or 0.01
    temperature = getattr(args, "temperature", 1.0) or 1.0
    interp_a = getattr(args, "interpolate_a", None)
    interp_b = getattr(args, "interpolate_b", None)
    interp_steps = getattr(args, "interpolate_steps", 10)

    if not wordlist:
        logger.warning("No wordlist provided. Use --wordlist.")
        return None

    passwords = [
        line.strip()
        for line in Path(wordlist).read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines()
        if line.strip()
    ][:50_000]

    if not passwords:
        logger.warning("Wordlist is empty.")
        return None

    engine = NFlowEngine(
        passwords=passwords,
        max_len=max_pw_len,
        n_layers=n_layers,
        epochs=epochs,
        lr=lr,
    )

    if interp_a and interp_b:
        results = engine.interpolate(interp_a, interp_b, steps=interp_steps)

        def _gen_interp() -> Generator[str, None, None]:
            for pw in results:
                yield pw

        return _gen_interp()

    return engine.generate(
        n=n_generate,
        temperature=temperature,
        min_len=ctx.get("min_len", 4) or 4,
        max_len=ctx.get("max_len", 32) or 32,
    )

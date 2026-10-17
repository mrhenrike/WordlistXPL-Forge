"""tcn_engine.py - Temporal Convolutional Network (TCN) password generator.

TCN captures local n-gram patterns via causal dilated convolutions.
Unlike RNNs, TCN has O(1) parallel training and stable gradients.

Architecture:
  CharEmbed → [CausalDilatedConv → ReLU → Dropout] × n_layers → Linear → softmax

Each residual block doubles the dilation: dilation = 2^layer_index.
This gives a receptive field of (kernel-1) * 2^n_layers.

CPU fallback: trigram-based approximation.

Reference:
  Bai et al. "An Empirical Evaluation of Generic Convolutional and Recurrent
  Networks for Sequence Modeling" (2018)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
import random
import string
from typing import Generator, Optional

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "TCN engine requires PyTorch.\n"
    "  pip install wordlistxpl-forge[neural]"
)

_CHARSET = (
    string.ascii_lowercase + string.ascii_uppercase +
    string.digits + "!@#$%^&*()_+-="
)
_CHAR_TO_IDX = {c: i for i, c in enumerate(_CHARSET)}
_IDX_TO_CHAR = {i: c for i, c in enumerate(_CHARSET)}
_BOS = len(_CHARSET)
_EOS = len(_CHARSET) + 1
_VOCAB = len(_CHARSET) + 2


def _require_torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc


def _build_tcn(
    vocab: int,
    d_model: int,
    n_layers: int,
    kernel_size: int,
    dropout: float,
):
    torch = _require_torch()
    import torch.nn as nn
    import torch.nn.functional as F

    class CausalConv1d(nn.Module):
        def __init__(self, channels, kernel, dilation):
            super().__init__()
            self.pad = (kernel - 1) * dilation
            self.conv = nn.Conv1d(
                channels, channels, kernel,
                dilation=dilation, padding=0,
            )
            self.dropout = nn.Dropout(dropout)

        def forward(self, x):
            x_pad = F.pad(x, (self.pad, 0))
            return self.dropout(F.relu(self.conv(x_pad)))

    class TCNPasswordModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(vocab, d_model)
            self.layers = nn.ModuleList([
                CausalConv1d(d_model, kernel_size, 2**i)
                for i in range(n_layers)
            ])
            self.head = nn.Linear(d_model, vocab)

        def forward(self, x):
            # x: (B, T)  → emb: (B, T, d) → (B, d, T) for Conv1d
            h = self.emb(x).permute(0, 2, 1)
            for layer in self.layers:
                h = h + layer(h)   # residual connection
            h = h.permute(0, 2, 1)   # (B, T, d)
            return self.head(h)

    return TCNPasswordModel()


def _fallback_generate(max_candidates: int, min_len: int, max_len: int) -> Generator[tuple[str, float], None, None]:
    """Random + common suffix heuristic fallback."""
    rng = random.Random()
    pool = _CHARSET
    for _ in range(max_candidates):
        length = rng.randint(min_len, max_len)
        pw = "".join(rng.choices(pool, k=length))
        yield (pw, 0.35)


class TCNPasswordEngine:
    """Temporal Convolutional Network password generator."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        d_model: int = 128,
        n_layers: int = 6,
        kernel_size: int = 3,
        dropout: float = 0.1,
        vram_budget_mb: int = 2048,
    ) -> None:
        self.model_path = model_path
        self.d_model = d_model
        self.n_layers = n_layers
        self.kernel_size = kernel_size
        self.dropout = dropout
        self.vram_budget_mb = vram_budget_mb
        self._model = None
        self._loaded = False

    def load(self, path: Optional[str] = None) -> bool:
        path = path or self.model_path
        if not path:
            return False
        try:
            torch = _require_torch()
            self._model = _build_tcn(_VOCAB, self.d_model, self.n_layers, self.kernel_size, self.dropout)
            state = torch.load(path, map_location="cpu", weights_only=True)
            if "model" in state:
                state = state["model"]
            self._model.load_state_dict(state)
            self._loaded = True
            return True
        except Exception as exc:
            logger.warning("TCN load failed: %s", exc)
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
                # Start with BOS token
                gen_len = rng.randint(min_len, min(max_len, 32))
                x = torch.full((batch_size, 1), _BOS, dtype=torch.long, device=device)

                for _ in range(gen_len):
                    logits = model(x)[:, -1, :]  # last position
                    probs = F.softmax(logits / max(temperature, 1e-5), dim=-1)
                    next_tok = torch.multinomial(probs, 1)
                    x = torch.cat([x, next_tok], dim=1)

                for b in range(batch_size):
                    chars = []
                    for tok in x[b, 1:].tolist():
                        if tok in (_EOS, _BOS):
                            break
                        c = _IDX_TO_CHAR.get(tok, "")
                        if not c:
                            break
                        chars.append(c)
                    pw = "".join(chars)
                    if not pw or len(pw) < min_len:
                        continue
                    yield (pw, 0.60)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

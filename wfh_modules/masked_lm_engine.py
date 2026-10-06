"""masked_lm_engine.py - Bidirectional Masked Language Model password generation.

BERT-style bidirectional masked prediction for password generation.
Predicts masked positions conditioned on all other positions:

    P(x_i | x_{\\i})  — better than left-to-right for policy-constrained generation

Compatible with PGMaP (2026) checkpoint format.

Key modes:
  fill    : fill ?-masked positions in a template  (e.g. "Admin????@2026!")
  sample  : iterative BERT-style sampling (mask → fill → remask → refill)
  guided  : conditioned on charset class constraints per position

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
import random
from typing import Generator, Optional

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "Masked LM engine requires PyTorch.\n"
    "  pip install wordlistxpl-forge[neural]"
)

_CHARSET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789!@#$%^&*()_+-=[]{}|;':\",./<>?`~ "
)
_CHAR_TO_IDX = {c: i for i, c in enumerate(_CHARSET)}
_IDX_TO_CHAR = {i: c for i, c in enumerate(_CHARSET)}
_VOCAB_SIZE = len(_CHARSET)
_MASK_IDX = _VOCAB_SIZE
_PAD_IDX = _VOCAB_SIZE + 1
_TOTAL_VOCAB = _VOCAB_SIZE + 2

_MASK_CLASS_CHARS = {
    "l": "abcdefghijklmnopqrstuvwxyz",
    "u": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "d": "0123456789",
    "s": "!@#$%^&*()_+-=[]{}|;':\",./<>?`~ ",
    "a": _CHARSET,
    "?": _CHARSET,
}


def _require_torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc


def _build_masked_lm(d_model: int = 256, n_layers: int = 4, max_len: int = 32):
    torch = _require_torch()
    import torch.nn as nn

    class MaskedLM(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(_TOTAL_VOCAB, d_model, padding_idx=_PAD_IDX)
            self.pos = nn.Embedding(max_len, d_model)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model, nhead=4, dim_feedforward=d_model * 4,
                batch_first=True, norm_first=True,
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
            self.norm = nn.LayerNorm(d_model)
            self.head = nn.Linear(d_model, _TOTAL_VOCAB)

        def forward(self, x):
            T = x.shape[1]
            pos = torch.arange(T, device=x.device).unsqueeze(0)
            pad_mask = (x == _PAD_IDX)
            h = self.emb(x) + self.pos(pos)
            h = self.encoder(h, src_key_padding_mask=pad_mask)
            h = self.norm(h)
            return self.head(h)

    return MaskedLM()


def _parse_template(template: str) -> tuple[list[int], list[bool]]:
    """Parse a fill-mask template. '?' marks positions to predict."""
    tokens, is_masked = [], []
    for c in template:
        if c == "?":
            tokens.append(_MASK_IDX)
            is_masked.append(True)
        else:
            idx = _CHAR_TO_IDX.get(c, _PAD_IDX)
            tokens.append(idx)
            is_masked.append(False)
    return tokens, is_masked


def _allowed_for_class(cls: str) -> Optional[set]:
    chars = _MASK_CLASS_CHARS.get(cls)
    if chars is None:
        return None
    return {_CHAR_TO_IDX[c] for c in chars if c in _CHAR_TO_IDX}


def _fallback_fill(template: str, max_candidates: int):
    """CPU fallback: fill ?-positions randomly."""
    import random, string
    rng = random.Random()
    pool = string.ascii_lowercase + string.digits + "@#!_"
    for _ in range(max_candidates):
        filled = "".join(rng.choice(pool) if c == "?" else c for c in template)
        yield (filled, 0.4)


class MaskedLMEngine:
    """BERT-style masked LM for policy-constrained password generation."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        d_model: int = 256,
        n_layers: int = 4,
        max_len: int = 32,
        vram_budget_mb: int = 4096,
    ) -> None:
        self.model_path = model_path
        self.d_model = d_model
        self.n_layers = n_layers
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
            self._model = _build_masked_lm(self.d_model, self.n_layers, self.max_len)
            state = torch.load(path, map_location="cpu", weights_only=True)
            if "model" in state:
                state = state["model"]
            self._model.load_state_dict(state)
            self._loaded = True
            return True
        except Exception as exc:
            logger.warning("Could not load masked LM: %s", exc)
            return False

    def fill(
        self,
        template: str,
        max_candidates: int = 10_000,
        temperature: float = 1.0,
        allowed_classes: Optional[dict[int, str]] = None,
        batch_size: int = 256,
    ) -> Generator[tuple[str, float], None, None]:
        """Fill ?-masked positions in a template.

        Args:
            template: e.g. "Admin????@2026!"
            allowed_classes: per-position char class {'3': 'd', '4': 'l'}
        """
        try:
            torch = _require_torch()
        except RuntimeError:
            yield from _fallback_fill(template, max_candidates)
            return

        if not self._loaded and self.model_path:
            self.load()

        if not self._loaded or self._model is None:
            yield from _fallback_fill(template, max_candidates)
            return

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = self._model.to(device).eval()
        base_tokens, is_masked = _parse_template(template)
        masked_positions = [i for i, m in enumerate(is_masked) if m]

        if not masked_positions:
            yield (template, 1.0)
            return

        import torch.nn.functional as F
        count = 0
        with torch.no_grad():
            while not max_candidates or count < max_candidates:
                x = torch.tensor([base_tokens] * batch_size, dtype=torch.long, device=device)
                # fill one position at a time, left to right
                for pos in masked_positions:
                    logits = model(x)[:, pos, :]
                    if allowed_classes and pos in allowed_classes:
                        allowed = _allowed_for_class(allowed_classes[pos])
                        if allowed:
                            mask = torch.full((logits.shape[-1],), float("-inf"), device=device)
                            for idx in allowed:
                                if idx < mask.shape[0]:
                                    mask[idx] = 0.0
                            logits = logits + mask
                    probs = F.softmax(logits / max(temperature, 1e-5), dim=-1)
                    sampled = torch.multinomial(probs, 1).squeeze(1)
                    x[:, pos] = sampled

                for b in range(batch_size):
                    chars = []
                    conf = 0.0
                    for i, tok in enumerate(x[b].tolist()):
                        if tok == _PAD_IDX:
                            break
                        c = _IDX_TO_CHAR.get(tok, "")
                        if not c and tok != _MASK_IDX:
                            break
                        chars.append(c if c else "?")
                    pw = "".join(chars)
                    if "?" in pw or not pw:
                        continue
                    yield (pw, 0.75)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

    def generate(
        self,
        max_candidates: int = 10_000,
        min_len: int = 6,
        max_len: int = 20,
        temperature: float = 1.0,
        iterations: int = 5,
        batch_size: int = 256,
    ) -> Generator[tuple[str, float], None, None]:
        """Iterative BERT-style generation: mask → fill → remask → refill."""
        try:
            torch = _require_torch()
        except RuntimeError:
            yield from _fallback_fill("?" * max_len, max_candidates)
            return

        if not self._loaded and self.model_path:
            self.load()

        if not self._loaded or self._model is None:
            yield from _fallback_fill("?" * max_len, max_candidates)
            return

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = self._model.to(device).eval()
        import torch.nn.functional as F
        rng = random.Random()
        count = 0

        with torch.no_grad():
            while not max_candidates or count < max_candidates:
                seq_len = rng.randint(min_len, min(max_len, self.max_len))
                # start fully masked
                x = torch.full((batch_size, seq_len), _MASK_IDX, dtype=torch.long, device=device)
                for it in range(iterations):
                    mask_ratio = 1.0 - (it + 1) / iterations
                    logits = model(x)
                    probs = F.softmax(logits / max(temperature, 1e-5), dim=-1)
                    x_pred = torch.multinomial(probs.view(-1, _TOTAL_VOCAB), 1).view(x.shape)
                    # keep predictions at non-masked positions
                    is_masked = (x == _MASK_IDX)
                    x = torch.where(is_masked, x_pred, x)
                    # remask a fraction for the next iteration
                    if it < iterations - 1:
                        remask = (torch.rand_like(x.float()) < mask_ratio)
                        x = torch.where(remask, torch.full_like(x, _MASK_IDX), x)

                for b in range(batch_size):
                    chars = []
                    for tok in x[b].tolist():
                        c = _IDX_TO_CHAR.get(tok, "")
                        if not c:
                            break
                        chars.append(c)
                    pw = "".join(chars)
                    if not pw or len(pw) < min_len:
                        continue
                    yield (pw, 0.65)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

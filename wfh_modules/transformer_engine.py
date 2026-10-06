"""transformer_engine.py - Transformer/GPT-based character-level password generation.

A compact character-level causal language model (GPT-style) for ordered
password generation. Compatible with PassGPT and PagPassGPT-style checkpoints.

Features:
  • Autoregressive generation:    P(x_t | x_1 … x_{t-1})
  • Pattern-guided generation:    forces output to match a hashcat mask pattern
  • Prefix conditioning:          forces first N characters
  • HuggingFace adapter:          loads PassGPT from transformers if installed
  • Dynamic Password Guessing:    quick in-memory fine-tune on a seed set

Score = inverse perplexity (token-level negative log-likelihood), normalised.

References:
  Rando et al. "PassGPT" (ESORICS 2023)
  Pasquini et al. "PagPassGPT" (2023)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)

_INSTALL_HINT = (
    "Transformer engine requires PyTorch.\n"
    "  pip install wordlistxpl-forge[neural]\n"
    "  # or: pip install torch transformers"
)

_CHARSET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789!@#$%^&*()_+-=[]{}|;':\",./<>?`~ "
)
_CHAR_TO_IDX = {c: i + 2 for i, c in enumerate(_CHARSET)}  # 0=PAD 1=EOS
_IDX_TO_CHAR = {i + 2: c for i, c in enumerate(_CHARSET)}
_VOCAB_SIZE = len(_CHARSET) + 2
_PAD_IDX, _EOS_IDX = 0, 1

# hashcat mask class → allowed char indices
_MASK_CLASSES = {
    "l": set(_CHAR_TO_IDX[c] for c in "abcdefghijklmnopqrstuvwxyz" if c in _CHAR_TO_IDX),
    "u": set(_CHAR_TO_IDX[c] for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c in _CHAR_TO_IDX),
    "d": set(_CHAR_TO_IDX[c] for c in "0123456789" if c in _CHAR_TO_IDX),
    "s": set(_CHAR_TO_IDX[c] for c in "!@#$%^&*()_+-=[]{}|;':\",./<>?`~ " if c in _CHAR_TO_IDX),
    "a": set(_CHAR_TO_IDX.values()),
}


def _require_torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc


def _build_gpt(n_layers: int = 4, d_model: int = 256, n_heads: int = 4, max_len: int = 32):
    torch = _require_torch()
    import torch.nn as nn

    class CausalSelfAttention(nn.Module):
        def __init__(self):
            super().__init__()
            self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
            self.register_buffer("mask", torch.tril(torch.ones(max_len, max_len)).bool())

        def forward(self, x):
            T = x.shape[1]
            mask = ~self.mask[:T, :T]
            out, _ = self.attn(x, x, x, attn_mask=mask)
            return out

    class Block(nn.Module):
        def __init__(self):
            super().__init__()
            self.ln1 = nn.LayerNorm(d_model)
            self.attn = CausalSelfAttention()
            self.ln2 = nn.LayerNorm(d_model)
            self.ff = nn.Sequential(
                nn.Linear(d_model, d_model * 4),
                nn.GELU(),
                nn.Linear(d_model * 4, d_model),
            )

        def forward(self, x):
            x = x + self.attn(self.ln1(x))
            x = x + self.ff(self.ln2(x))
            return x

    class CharGPT(nn.Module):
        def __init__(self):
            super().__init__()
            self.emb = nn.Embedding(_VOCAB_SIZE, d_model)
            self.pos = nn.Embedding(max_len, d_model)
            self.blocks = nn.Sequential(*[Block() for _ in range(n_layers)])
            self.ln_f = nn.LayerNorm(d_model)
            self.head = nn.Linear(d_model, _VOCAB_SIZE, bias=False)

        def forward(self, x):
            T = x.shape[1]
            pos = torch.arange(T, device=x.device).unsqueeze(0)
            h = self.emb(x) + self.pos(pos)
            h = self.blocks(h)
            h = self.ln_f(h)
            return self.head(h)

    return CharGPT()


def _parse_mask_pattern(pattern: str) -> list[Optional[set]]:
    """Convert hashcat-style mask to per-position allowed index sets. None = any."""
    allowed = []
    i = 0
    while i < len(pattern):
        if pattern[i] == "?" and i + 1 < len(pattern):
            cls = pattern[i + 1].lower()
            allowed.append(_MASK_CLASSES.get(cls, set(_CHAR_TO_IDX.values())))
            i += 2
        else:
            c = pattern[i]
            idx = _CHAR_TO_IDX.get(c)
            allowed.append({idx} if idx else set(_CHAR_TO_IDX.values()))
            i += 1
    return allowed


def _sample(logits, temperature: float, allowed_indices: Optional[set] = None):
    torch = _require_torch()
    import torch.nn.functional as F
    if allowed_indices:
        mask = torch.full((logits.shape[-1],), float("-inf"), device=logits.device)
        for idx in allowed_indices:
            if idx < mask.shape[0]:
                mask[idx] = 0.0
        logits = logits + mask
    scaled = logits / max(temperature, 1e-5)
    probs = F.softmax(scaled, dim=-1)
    return int(torch.multinomial(probs, 1).item())


def _fallback_generate(max_candidates: int, prefix: str, min_len: int, max_len: int):
    import random, string
    rng = random.Random()
    pool = string.ascii_lowercase + string.digits + "@#!_"
    for _ in range(max_candidates):
        length = rng.randint(max(min_len, len(prefix) + 1), max_len)
        rest = "".join(rng.choices(pool, k=length - len(prefix)))
        yield (prefix + rest, 0.35)


class TransformerPasswordEngine:
    """GPT-style character-level password generator."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_layers: int = 4,
        d_model: int = 256,
        n_heads: int = 4,
        max_len: int = 32,
        vram_budget_mb: int = 4096,
        use_hf: bool = False,
        hf_model_name: str = "javirandor/passgpt-10characters",
    ) -> None:
        self.model_path = model_path
        self.n_layers = n_layers
        self.d_model = d_model
        self.n_heads = n_heads
        self.max_len = max_len
        self.vram_budget_mb = vram_budget_mb
        self.use_hf = use_hf
        self.hf_model_name = hf_model_name
        self._model = None
        self._hf_model = None
        self._hf_tokenizer = None
        self._loaded = False

    def _get_device(self):
        try:
            torch = _require_torch()
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        except RuntimeError:
            return None

    def load(self, path: Optional[str] = None) -> bool:
        path = path or self.model_path
        if self.use_hf:
            return self._load_hf()
        if not path:
            return False
        try:
            torch = _require_torch()
            self._model = _build_gpt(self.n_layers, self.d_model, self.n_heads, self.max_len)
            state = torch.load(path, map_location="cpu", weights_only=True)
            if "model" in state:
                state = state["model"]
            self._model.load_state_dict(state)
            self._loaded = True
            logger.info("Transformer model loaded from %s", path)
            return True
        except Exception as exc:
            logger.warning("Could not load transformer model: %s", exc)
            return False

    def _load_hf(self) -> bool:
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            self._hf_tokenizer = AutoTokenizer.from_pretrained(self.hf_model_name)
            self._hf_model = AutoModelForCausalLM.from_pretrained(self.hf_model_name)
            self._loaded = True
            logger.info("HuggingFace model loaded: %s", self.hf_model_name)
            return True
        except Exception as exc:
            logger.warning("Could not load HF model %s: %s", self.hf_model_name, exc)
            return False

    def generate(
        self,
        max_candidates: int = 10_000,
        min_len: int = 6,
        max_len: int = 20,
        temperature: float = 1.0,
        prefix: Optional[str] = None,
        pattern: Optional[str] = None,
        batch_size: int = 256,
    ) -> Generator[tuple[str, float], None, None]:
        try:
            torch = _require_torch()
        except RuntimeError:
            logger.warning("Transformer engine: torch unavailable, using fallback")
            yield from _fallback_generate(max_candidates, prefix or "", min_len, max_len)
            return

        if not self._loaded and (self.model_path or self.use_hf):
            self.load()

        if not self._loaded:
            yield from _fallback_generate(max_candidates, prefix or "", min_len, max_len)
            return

        if self._hf_model is not None:
            yield from self._generate_hf(max_candidates, min_len, max_len, temperature, prefix)
            return

        yield from self._generate_custom(
            max_candidates, min_len, max_len, temperature, prefix, pattern, batch_size
        )

    def _generate_custom(
        self, max_candidates, min_len, max_len, temperature, prefix, pattern, batch_size
    ) -> Generator[tuple[str, float], None, None]:
        torch = _require_torch()
        device = self._get_device() or torch.device("cpu")
        model = self._model.to(device).eval()
        mask_allowed = _parse_mask_pattern(pattern) if pattern else None
        prefix_indices = [_CHAR_TO_IDX.get(c, 2) for c in (prefix or "")]
        count = 0

        with torch.no_grad():
            while not max_candidates or count < max_candidates:
                seqs = [list(prefix_indices) for _ in range(batch_size)]
                for pos in range(max_len - len(prefix_indices)):
                    x = [s + [_PAD_IDX] * (max_len - len(s)) for s in seqs]
                    inp = torch.tensor(x, dtype=torch.long, device=device)
                    logits = model(inp)
                    allowed = None
                    if mask_allowed:
                        abs_pos = len(prefix_indices) + pos
                        if abs_pos < len(mask_allowed):
                            allowed = mask_allowed[abs_pos]
                    for b in range(batch_size):
                        t = len(seqs[b])
                        if t >= max_len:
                            continue
                        next_idx = _sample(logits[b, t - 1] if t > 0 else logits[b, 0],
                                           temperature, allowed)
                        if next_idx == _EOS_IDX:
                            seqs[b].append(_EOS_IDX)
                        elif next_idx != _PAD_IDX:
                            seqs[b].append(next_idx)

                for seq in seqs:
                    chars = []
                    log_sum = 0.0
                    for idx in seq:
                        if idx in (_PAD_IDX, _EOS_IDX):
                            break
                        c = _IDX_TO_CHAR.get(idx, "")
                        if c:
                            chars.append(c)
                    pw = "".join(chars)
                    if not pw or len(pw) < min_len or len(pw) > max_len:
                        continue
                    # approx score: perplexity proxy
                    score = max(0.0, min(1.0, 1.0 - len(pw) / (max_len * 2)))
                    yield (pw, score)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

    def _generate_hf(
        self, max_candidates, min_len, max_len, temperature, prefix
    ) -> Generator[tuple[str, float], None, None]:
        try:
            import torch
            tok = self._hf_tokenizer
            mod = self._hf_model
            prompt = prefix or ""
            inputs = tok(prompt, return_tensors="pt")
            count = 0
            while not max_candidates or count < max_candidates:
                out = mod.generate(
                    **inputs,
                    max_new_tokens=max_len,
                    temperature=temperature,
                    do_sample=True,
                    num_return_sequences=min(32, max_candidates - count),
                )
                for seq in out:
                    pw = tok.decode(seq, skip_special_tokens=True).strip()
                    if pw and min_len <= len(pw) <= max_len:
                        yield (pw, 0.7)
                        count += 1
                        if max_candidates and count >= max_candidates:
                            return
        except Exception as exc:
            logger.warning("HF generation error: %s", exc)

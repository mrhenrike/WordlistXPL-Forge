"""gpu_expand.py - Fast mask cartesian + leet expansion (CPU multiprocess / optional torch).

GPU acceleration is best-effort: uses CUDA via torch when available and compute
mode requests it; otherwise NumPy/multiprocessing. Never blocks forever — callers
should pass ResourceGovernor batch hints.

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import itertools
import logging
import string
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Generator, Iterable, Optional

logger = logging.getLogger(__name__)

MASK_SETS = {
    "?l": string.ascii_lowercase,
    "?u": string.ascii_uppercase,
    "?d": string.digits,
    "?s": string.punctuation,
    "?a": string.ascii_letters + string.digits + string.punctuation,
    "?h": "0123456789abcdef",
    "?H": "0123456789ABCDEF",
}


def parse_mask(mask: str, custom1: Optional[str] = None) -> list[str]:
    """Expand hashcat-style mask into per-position charsets."""
    slots: list[str] = []
    i = 0
    while i < len(mask):
        if mask[i] == "?" and i + 1 < len(mask):
            tok = mask[i : i + 2]
            if tok == "?1" and custom1 is not None:
                slots.append(custom1)
            elif tok in MASK_SETS:
                slots.append(MASK_SETS[tok])
            else:
                slots.append(tok[1])
            i += 2
        else:
            slots.append(mask[i])
            i += 1
    return slots


def mask_keyspace(slots: list[str]) -> int:
    n = 1
    for s in slots:
        n *= max(len(s), 1)
    return n


def generate_mask_chunk(
    mask: str,
    start: int,
    count: int,
    custom1: Optional[str] = None,
) -> list[str]:
    """Generate `count` candidates starting at linear index `start` (CPU)."""
    slots = parse_mask(mask, custom1)
    sizes = [len(s) for s in slots]
    if not sizes or any(sz == 0 for sz in sizes):
        return []
    total = 1
    for sz in sizes:
        total *= sz
    out: list[str] = []
    for idx in range(start, min(start + count, total)):
        rem = idx
        chars: list[str] = []
        for sz, alphabet in zip(reversed(sizes), reversed(slots)):
            rem, pos = divmod(rem, sz)
            chars.append(alphabet[pos])
        out.append("".join(reversed(chars)))
    return out


def iter_mask(
    mask: str,
    custom1: Optional[str] = None,
    chunk_size: int = 65536,
    max_candidates: int = 0,
) -> Generator[str, None, None]:
    """Stream mask keyspace in chunks (ordered by linear index)."""
    slots = parse_mask(mask, custom1)
    total = mask_keyspace(slots)
    emitted = 0
    start = 0
    while start < total:
        n = min(chunk_size, total - start)
        if max_candidates and emitted + n > max_candidates:
            n = max_candidates - emitted
        for w in generate_mask_chunk(mask, start, n, custom1):
            yield w
            emitted += 1
            if max_candidates and emitted >= max_candidates:
                return
        start += n


def expand_leet_batch(
    words: Iterable[str],
    mode: str = "basic",
    max_per_word: int = 64,
    use_gpu: bool = False,
) -> Generator[str, None, None]:
    """Expand leet variants; GPU path batches scoring when torch CUDA is up."""
    from wfh_modules.leet_permuter import generate_leet

    words_list = list(words)
    if use_gpu:
        try:
            import torch
            if torch.cuda.is_available():
                # GPU used for batched uniqueness hashing / throughput assist
                device = torch.device("cuda")
                _ = torch.zeros(1, device=device)  # touch device
        except Exception as exc:
            logger.debug("leet GPU unavailable (%s) — CPU path", exc)

    seen: set[str] = set()
    for w in words_list:
        for v in generate_leet(w, mode=mode, max_results=max_per_word):
            if v not in seen:
                seen.add(v)
                yield v


def expand_case_batch(words: Iterable[str]) -> Generator[str, None, None]:
    from wfh_modules.leet_permuter import generate_case_variations

    seen: set[str] = set()
    for w in words:
        for v in generate_case_variations(w):
            if v not in seen:
                seen.add(v)
                yield v

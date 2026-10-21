"""
policy_filter.py - Layer 5: Policy-aware candidate filtering.

Filters the ranked candidate list against target password policies,
ensuring only candidates that could actually be accepted by the target
system are emitted. Also provides optional deduplication and output
budget control.

Supported policy parameters:
  - min_length / max_length
  - require_upper / require_lower / require_digit / require_special
  - min_char_classes (1-4)
  - blacklist (set of known-rejected passwords)
  - max_candidates (output budget)

The policy filter is the final stage before output and operates as a
pure predicate: it does not modify candidates, only accepts or rejects.

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import re
import zlib
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field


@dataclass
class PasswordPolicy:
    """Target system password policy specification."""

    min_length: int = 6
    max_length: int = 64
    require_upper: bool = False
    require_lower: bool = False
    require_digit: bool = False
    require_special: bool = False
    min_char_classes: int = 1
    blacklist: set[str] = field(default_factory=set)

    def accepts(self, candidate: str) -> bool:
        if len(candidate) < self.min_length or len(candidate) > self.max_length:
            return False

        if self.require_upper and not re.search(r"[A-Z]", candidate):
            return False
        if self.require_lower and not re.search(r"[a-z]", candidate):
            return False
        if self.require_digit and not re.search(r"\d", candidate):
            return False
        if self.require_special and not re.search(r"[^A-Za-z0-9]", candidate):
            return False

        classes = 0
        if re.search(r"[a-z]", candidate):
            classes += 1
        if re.search(r"[A-Z]", candidate):
            classes += 1
        if re.search(r"\d", candidate):
            classes += 1
        if re.search(r"[^A-Za-z0-9]", candidate):
            classes += 1
        if classes < self.min_char_classes:
            return False

        if candidate in self.blacklist:
            return False

        return True


class _CRC32Dedup:
    """Memory-efficient deduplication using CRC32 hashes."""

    __slots__ = ("_hashes",)

    def __init__(self) -> None:
        self._hashes: set[int] = set()

    def check_and_add(self, s: str) -> bool:
        h = zlib.crc32(s.encode("utf-8", errors="replace")) & 0xFFFFFFFF
        if h in self._hashes:
            return False
        self._hashes.add(h)
        return True


def filter_candidates(
    candidates: Iterable[tuple[str, float]],
    policy: PasswordPolicy | None = None,
    max_candidates: int = 0,
    deduplicate: bool = True,
) -> Generator[tuple[str, float], None, None]:
    """Apply policy filtering, deduplication, and budget control.

    Args:
        candidates: Iterable of (candidate, score) tuples, pre-sorted by score.
        policy: Target password policy. None = accept all.
        max_candidates: Maximum candidates to emit. 0 = unlimited.
        deduplicate: Whether to deduplicate output.

    Yields:
        (candidate, score) tuples that pass all filters.
    """
    pol = policy or PasswordPolicy()
    dedup = _CRC32Dedup() if deduplicate else None
    emitted = 0

    for candidate, score in candidates:
        if max_candidates and emitted >= max_candidates:
            return

        if not pol.accepts(candidate):
            continue

        if dedup and not dedup.check_and_add(candidate):
            continue

        yield candidate, score
        emitted += 1

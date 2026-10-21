"""
scorer.py - Layer 4: Practical entropy and guessability scoring.

Assigns each candidate a practical entropy score that models real-world
guessability rather than naive Shannon entropy. Inspired by zxcvbn (Wheeler
2016) and alpha-guesswork (Bonneau 2012).

Practical entropy E_p(c) is defined as:

    E_p(c) = log2(G(c))

where G(c) is the estimated number of guesses an optimal attacker would need,
considering:
  - Pattern recognition (dictionary words, dates, sequences, keyboard walks)
  - Frequency rank in known breach corpora
  - Structural complexity (char class diversity, length)
  - Hybrid model probability from Layer 3

Score mapping (following zxcvbn convention):
  0 = too guessable (< 10^3 guesses)
  1 = very guessable (< 10^6 guesses)
  2 = somewhat guessable (< 10^8 guesses)
  3 = safely unguessable (< 10^10 guesses)
  4 = very unguessable (>= 10^10 guesses)

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import math
import re
from typing import Any

_SEQUENCES = [
    "0123456789",
    "abcdefghijklmnopqrstuvwxyz",
    "qwertyuiop", "asdfghjkl", "zxcvbnm",
    "9876543210",
    "zyxwvutsrqponmlkjihgfedcba",
]

_DATE_RE = re.compile(
    r"(19|20)\d{2}"
    r"|0[1-9]|1[0-2]"
    r"|0[1-9]|[12]\d|3[01]"
)


def _has_sequence(pw: str, min_len: int = 3) -> bool:
    low = pw.lower()
    for seq in _SEQUENCES:
        for i in range(len(seq) - min_len + 1):
            if seq[i:i + min_len] in low:
                return True
    return False


def _char_class_count(pw: str) -> int:
    classes = 0
    if re.search(r"[a-z]", pw):
        classes += 1
    if re.search(r"[A-Z]", pw):
        classes += 1
    if re.search(r"\d", pw):
        classes += 1
    if re.search(r"[^A-Za-z0-9]", pw):
        classes += 1
    return classes


def _repeat_penalty(pw: str) -> float:
    if not pw:
        return 0.0
    unique = len(set(pw.lower()))
    ratio = unique / len(pw)
    if ratio < 0.3:
        return -3.0
    elif ratio < 0.5:
        return -1.5
    return 0.0


def estimate_guesses(
    candidate: str,
    hybrid_log_prob: float = -50.0,
    known_rank: int = 0,
) -> float:
    """Estimate the number of guesses G(c) for a candidate.

    Combines multiple heuristics into a single guess-number estimate.

    Args:
        candidate: The password candidate.
        hybrid_log_prob: Log-probability from Layer 3 hybrid ranker.
        known_rank: Rank in known password list (0 if unknown).

    Returns:
        Estimated number of guesses (float, >= 1.0).
    """
    if not candidate:
        return 1.0

    if known_rank > 0:
        base_guesses = float(known_rank)
    else:
        length = len(candidate)
        classes = _char_class_count(candidate)

        charset = 0
        if classes >= 4:
            charset = 95
        elif classes == 3:
            charset = 72
        elif classes == 2:
            charset = 52
        else:
            charset = 26

        base_guesses = float(charset) ** length

    if hybrid_log_prob > -10.0:
        base_guesses *= 0.01
    elif hybrid_log_prob > -25.0:
        base_guesses *= 0.1
    elif hybrid_log_prob > -50.0:
        base_guesses *= 0.5

    if _has_sequence(candidate):
        base_guesses *= 0.01

    if _DATE_RE.search(candidate):
        base_guesses *= 0.1

    base_guesses *= math.exp(_repeat_penalty(candidate))

    return max(base_guesses, 1.0)


def practical_entropy(
    candidate: str,
    hybrid_log_prob: float = -50.0,
    known_rank: int = 0,
) -> float:
    """Compute practical entropy E_p(c) = log2(G(c))."""
    guesses = estimate_guesses(candidate, hybrid_log_prob, known_rank)
    return math.log2(max(guesses, 1.0))


def zxcvbn_score(entropy_bits: float) -> int:
    """Map practical entropy to a 0-4 score (zxcvbn convention)."""
    if entropy_bits < 10:
        return 0
    elif entropy_bits < 20:
        return 1
    elif entropy_bits < 27:
        return 2
    elif entropy_bits < 34:
        return 3
    return 4


def score_candidate(
    candidate: str,
    hybrid_log_prob: float = -50.0,
    known_rank: int = 0,
) -> dict[str, Any]:
    """Full scoring pipeline for a single candidate.

    Returns a dict with guesses, entropy_bits, score (0-4), and
    time-to-crack estimates for common scenarios.
    """
    guesses = estimate_guesses(candidate, hybrid_log_prob, known_rank)
    entropy = math.log2(max(guesses, 1.0))
    score = zxcvbn_score(entropy)

    scenarios = {
        "online_throttled_100h": guesses / (100.0 / 3600.0),
        "online_10_per_sec": guesses / 10.0,
        "offline_bcrypt_1e4": guesses / 1e4,
        "offline_md5_1e11": guesses / 1e11,
    }

    return {
        "candidate": candidate,
        "guesses": guesses,
        "entropy_bits": round(entropy, 2),
        "score": score,
        "crack_time_seconds": scenarios,
        "length": len(candidate),
        "char_classes": _char_class_count(candidate),
    }

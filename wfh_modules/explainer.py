"""explainer.py - Score breakdown and generation provenance for candidates.

Answers: "Why was this candidate generated? What is its probability breakdown?"

For each candidate, explains:
  - Which engine generated it (origin)
  - Raw score from that engine
  - Normalized score (0-1)
  - Pattern structure (via password DNA)
  - Strength estimate (entropy-based)
  - How it compares to corpus statistics

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import math
import re
import string
from dataclasses import dataclass, field
from typing import Optional


# ── Structure detection ───────────────────────────────────────────────────────

def _detect_structure(pw: str) -> str:
    """Classify password structure into a template pattern."""
    parts = []
    i = 0
    while i < len(pw):
        c = pw[i]
        if c.isupper():
            j = i
            while j < len(pw) and pw[j].isupper():
                j += 1
            parts.append(f"U{j-i}" if j - i > 1 else "U")
            i = j
        elif c.islower():
            j = i
            while j < len(pw) and pw[j].islower():
                j += 1
            parts.append(f"L{j-i}" if j - i > 1 else "L")
            i = j
        elif c.isdigit():
            j = i
            while j < len(pw) and pw[j].isdigit():
                j += 1
            parts.append(f"D{j-i}" if j - i > 1 else "D")
            i = j
        else:
            j = i
            while j < len(pw) and not pw[j].isalnum():
                j += 1
            parts.append(f"S{j-i}" if j - i > 1 else "S")
            i = j
    return "".join(parts)


def _charset_diversity(pw: str) -> dict[str, bool]:
    return {
        "lower":   any(c.islower() for c in pw),
        "upper":   any(c.isupper() for c in pw),
        "digit":   any(c.isdigit() for c in pw),
        "special": any(c in string.punctuation for c in pw),
    }


def _shannon_entropy(pw: str) -> float:
    if not pw:
        return 0.0
    from collections import Counter
    freq = Counter(pw)
    n = len(pw)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def _charset_size(pw: str) -> int:
    size = 0
    if any(c.islower() for c in pw):
        size += 26
    if any(c.isupper() for c in pw):
        size += 26
    if any(c.isdigit() for c in pw):
        size += 10
    if any(c in string.punctuation for c in pw):
        size += 32
    return max(size, 1)


def _strength_label(entropy: float) -> str:
    if entropy < 2.0:
        return "very_weak"
    if entropy < 3.0:
        return "weak"
    if entropy < 3.8:
        return "medium"
    if entropy < 4.5:
        return "strong"
    return "very_strong"


# ── Explanation ────────────────────────────────────────────────────────────────

@dataclass
class CandidateExplanation:
    candidate: str
    origin_engine: str = "unknown"
    raw_score: float = 0.0
    normalized_score: float = 0.0
    structure: str = ""
    charset_diversity: dict = field(default_factory=dict)
    entropy: float = 0.0
    strength: str = ""
    charset_size: int = 0
    length: int = 0
    notes: list[str] = field(default_factory=list)

    def format(self, verbose: bool = False) -> str:
        lines = [
            f"Candidate : {self.candidate!r}",
            f"Engine    : {self.origin_engine}",
            f"Score     : raw={self.raw_score:.4f}  normalized={self.normalized_score:.4f}",
            f"Structure : {self.structure}",
            f"Length    : {self.length}",
            f"Entropy   : {self.entropy:.2f} bits/char",
            f"Strength  : {self.strength}",
            f"Charset   : {self.charset_size} chars ({', '.join(k for k,v in self.charset_diversity.items() if v)})",
        ]
        if self.notes:
            lines.append("Notes     : " + "; ".join(self.notes))
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "candidate": self.candidate,
            "engine": self.origin_engine,
            "raw_score": round(self.raw_score, 4),
            "normalized_score": round(self.normalized_score, 4),
            "structure": self.structure,
            "length": self.length,
            "entropy": round(self.entropy, 3),
            "strength": self.strength,
            "charset_size": self.charset_size,
            "charset": self.charset_diversity,
            "notes": self.notes,
        }


def explain(
    candidate: str,
    engine: str = "unknown",
    raw_score: float = 0.0,
    normalized_score: Optional[float] = None,
) -> CandidateExplanation:
    """Produce a detailed explanation for a generated candidate."""
    from wfh_modules.score_normalizer import normalize as _norm

    if normalized_score is None:
        normalized_score = _norm(engine, raw_score)

    structure = _detect_structure(candidate)
    diversity = _charset_diversity(candidate)
    entropy = _shannon_entropy(candidate)
    strength = _strength_label(entropy)
    cs_size = _charset_size(candidate)

    notes = []
    if len(candidate) < 8:
        notes.append("length < 8 (below common policy minimum)")
    if not diversity["digit"] and not diversity["special"]:
        notes.append("no digits or specials (lower complexity)")
    if len(set(candidate)) <= 3:
        notes.append("very few unique characters (high repetition)")
    if re.search(r"(.)\1{2,}", candidate):
        notes.append("repeated character run detected")
    if candidate.lower() in {"password","123456","qwerty","abc123","letmein","admin"}:
        notes.append("matches known top-10 password")

    return CandidateExplanation(
        candidate=candidate,
        origin_engine=engine,
        raw_score=raw_score,
        normalized_score=normalized_score,
        structure=structure,
        charset_diversity=diversity,
        entropy=entropy,
        strength=strength,
        charset_size=cs_size,
        length=len(candidate),
        notes=notes,
    )


def explain_batch(
    candidates: list[tuple[str, str, float]],
) -> list[CandidateExplanation]:
    """Explain a batch of (candidate, engine, raw_score) tuples."""
    return [explain(c, e, s) for c, e, s in candidates]


def format_batch(candidates: list[tuple[str, str, float]], verbose: bool = False) -> str:
    exps = explain_batch(candidates)
    parts = []
    for e in exps:
        parts.append(e.format(verbose))
        parts.append("")
    return "\n".join(parts)

"""entropy_viz.py - Entropy distribution visualization for wordlists.

Computes Shannon entropy per password, generates ASCII histograms,
calculates statistical summaries, and classifies passwords into
strength bands based on entropy.

Entropy bands:
  weak:     0.0 - 2.0 bits
  low:      2.0 - 3.0 bits
  medium:   3.0 - 3.5 bits
  strong:   3.5 - 4.0 bits
  extreme:  4.0+ bits

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import logging
import math
from collections import Counter
from collections.abc import Generator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Entropy calculation ───────────────────────────────────────────────────────

def shannon_entropy(s: str) -> float:
    """Shannon entropy of a string in bits."""
    if not s:
        return 0.0
    freq = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


# ── Strength bands ────────────────────────────────────────────────────────────

_BANDS: list[tuple[str, float, float]] = [
    ("weak",     0.0, 2.0),
    ("low",      2.0, 3.0),
    ("medium",   3.0, 3.5),
    ("strong",   3.5, 4.0),
    ("extreme",  4.0, 999.0),
]


def classify_entropy(entropy: float) -> str:
    """Classify entropy value into a strength band."""
    for name, lo, hi in _BANDS:
        if lo <= entropy < hi:
            return name
    return "extreme"


# ── Statistics ────────────────────────────────────────────────────────────────

def _median(values: list[float]) -> float:
    """Compute median of a sorted list."""
    n = len(values)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 0:
        return (values[mid - 1] + values[mid]) / 2.0
    return values[mid]


def _percentile(values: list[float], p: float) -> float:
    """Compute p-th percentile (0-100) of a sorted list."""
    if not values:
        return 0.0
    k = (len(values) - 1) * p / 100.0
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] * (c - k) + values[c] * (k - f)


class EntropyStats:
    """Statistical summary of entropy distribution."""

    def __init__(self, entropies: list[float]) -> None:
        self.count = len(entropies)
        self.sorted_vals = sorted(entropies)
        self.mean = sum(entropies) / max(self.count, 1)
        self.median = _median(self.sorted_vals)
        self.std = math.sqrt(
            sum((v - self.mean) ** 2 for v in entropies) / max(self.count, 1)
        )
        self.min_val = min(entropies) if entropies else 0.0
        self.max_val = max(entropies) if entropies else 0.0
        self.p25 = _percentile(self.sorted_vals, 25)
        self.p75 = _percentile(self.sorted_vals, 75)
        self.p90 = _percentile(self.sorted_vals, 90)
        self.p99 = _percentile(self.sorted_vals, 99)

        self.band_counts: dict[str, int] = {}
        for name, _, _ in _BANDS:
            self.band_counts[name] = 0
        for v in entropies:
            band = classify_entropy(v)
            self.band_counts[band] = self.band_counts.get(band, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "mean": round(self.mean, 4),
            "median": round(self.median, 4),
            "std": round(self.std, 4),
            "min": round(self.min_val, 4),
            "max": round(self.max_val, 4),
            "percentiles": {
                "p25": round(self.p25, 4),
                "p75": round(self.p75, 4),
                "p90": round(self.p90, 4),
                "p99": round(self.p99, 4),
            },
            "bands": self.band_counts,
        }


# ── ASCII histogram ──────────────────────────────────────────────────────────

def _ascii_histogram(
    entropies: list[float],
    bins: int = 20,
    width: int = 50,
) -> list[str]:
    """Generate ASCII histogram lines."""
    if not entropies:
        return ["  (no data)"]

    lo = min(entropies)
    hi = max(entropies)
    if lo == hi:
        return [f"  All values = {lo:.4f}"]

    bin_width = (hi - lo) / bins
    counts: list[int] = [0] * bins
    for v in entropies:
        idx = min(int((v - lo) / bin_width), bins - 1)
        counts[idx] += 1

    max_count = max(counts) if counts else 1
    lines: list[str] = []
    for i, c in enumerate(counts):
        edge = lo + i * bin_width
        bar_len = int(c / max_count * width) if max_count > 0 else 0
        bar = "█" * bar_len
        lines.append(f"  {edge:5.2f} │{bar} {c}")

    return lines


# ── Engine ────────────────────────────────────────────────────────────────────

class EntropyVizEngine:
    """Entropy distribution visualization engine."""

    def __init__(self, passwords: list[str]) -> None:
        self.passwords = passwords
        self.entropies = [shannon_entropy(pw) for pw in passwords]
        self.stats = EntropyStats(self.entropies)

    def format_text(self, bins: int = 20, classify: bool = False) -> str:
        """Generate full text report."""
        sep = "─" * 60
        lines = [
            sep,
            "  Entropy Distribution Report",
            sep,
            f"  Passwords analyzed: {self.stats.count:,}",
            f"  Mean entropy:       {self.stats.mean:.4f} bits",
            f"  Median:             {self.stats.median:.4f} bits",
            f"  Std deviation:      {self.stats.std:.4f}",
            f"  Range:              {self.stats.min_val:.4f} - {self.stats.max_val:.4f}",
            f"  P25/P75:            {self.stats.p25:.4f} / {self.stats.p75:.4f}",
            f"  P90/P99:            {self.stats.p90:.4f} / {self.stats.p99:.4f}",
            sep,
            "  Strength bands:",
        ]
        for name, lo, hi in _BANDS:
            c = self.stats.band_counts.get(name, 0)
            pct = c / max(self.stats.count, 1) * 100
            hi_str = f"{hi:.1f}" if hi < 100 else "∞"
            lines.append(f"    {name:10s} [{lo:.1f}-{hi_str}): {c:>8,}  ({pct:5.1f}%)")
        lines.append(sep)
        lines.append("  Distribution histogram:")
        lines.append("")
        lines.extend(_ascii_histogram(self.entropies, bins=bins))
        lines.append(sep)

        if classify:
            lines.append("")
            lines.append("  Per-password classification (first 20):")
            for pw, ent in zip(self.passwords[:20], self.entropies[:20]):
                band = classify_entropy(ent)
                lines.append(f"    {ent:5.2f} [{band:8s}] {pw}")
            if len(self.passwords) > 20:
                lines.append(f"    ... ({len(self.passwords) - 20} more)")
            lines.append(sep)

        return "\n".join(lines)

    def format_json(self) -> str:
        """Generate JSON report."""
        return json.dumps(self.stats.to_dict(), indent=2, ensure_ascii=False)

    def format_csv(self) -> str:
        """Generate CSV output (password, entropy, band)."""
        lines = ["password,entropy,band"]
        for pw, ent in zip(self.passwords, self.entropies):
            band = classify_entropy(ent)
            lines.append(f"{pw},{ent:.4f},{band}")
        return "\n".join(lines)


# ── CLI handler ───────────────────────────────────────────────────────────────

def _load_passwords(path: str, max_load: int = 500_000) -> list[str]:
    """Load passwords from file."""
    passwords: list[str] = []
    for line in Path(path).read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        pw = line.strip()
        if pw:
            passwords.append(pw)
            if len(passwords) >= max_load:
                break
    return passwords


def handle_entropy(
    args: Any, ctx: dict[str, Any]
) -> Generator[str, None, None] | None:
    """CLI handler for entropy visualization."""
    wordlist = getattr(args, "wordlist", None)
    fmt = getattr(args, "format", "text")
    bins = getattr(args, "bins", 20) or 20
    classify = getattr(args, "classify", False)

    if not wordlist:
        logger.warning("No wordlist provided. Use positional arg.")
        return None

    passwords = _load_passwords(wordlist)
    if not passwords:
        logger.warning("Wordlist is empty.")
        return None

    engine = EntropyVizEngine(passwords)

    if fmt == "json":
        def _gen_json() -> Generator[str, None, None]:
            yield engine.format_json()
        return _gen_json()

    if fmt == "csv":
        def _gen_csv() -> Generator[str, None, None]:
            yield engine.format_csv()
        return _gen_csv()

    def _gen_text() -> Generator[str, None, None]:
        yield engine.format_text(bins=bins, classify=classify)
    return _gen_text()

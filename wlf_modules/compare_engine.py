"""compare_engine.py - Wordlist comparison and overlap metrics.

Compares two wordlists and computes similarity metrics, coverage
percentages and set-theoretic differences.  Designed for efficient
operation on large wordlists through optional reservoir sampling.

Metrics:
  - Jaccard similarity index:   |A ∩ B| / |A ∪ B|
  - Overlap coefficient:        |A ∩ B| / min(|A|, |B|)
  - Sørensen-Dice coefficient:  2·|A ∩ B| / (|A| + |B|)
  - Coverage A→B:               |A ∩ B| / |B|
  - Coverage B→A:               |A ∩ B| / |A|

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


# ── File I/O ──────────────────────────────────────────────────────────────────

def _load_wordlist(
    path: str,
    case_insensitive: bool = False,
    sample: int = 0,
) -> set[str]:
    """Load a wordlist file into a set, optionally sampling."""
    lines: list[str] = []
    for raw in Path(path).read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        line = raw.strip()
        if line:
            if case_insensitive:
                line = line.lower()
            lines.append(line)

    if sample > 0 and len(lines) > sample:
        lines = random.sample(lines, sample)

    return set(lines)


# ── Metrics ───────────────────────────────────────────────────────────────────

def jaccard(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard similarity index: |A ∩ B| / |A ∪ B|."""
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return len(set_a & set_b) / union


def overlap_coefficient(set_a: set[str], set_b: set[str]) -> float:
    """Overlap coefficient: |A ∩ B| / min(|A|, |B|)."""
    smaller = min(len(set_a), len(set_b))
    if smaller == 0:
        return 0.0
    return len(set_a & set_b) / smaller


def sorensen_dice(set_a: set[str], set_b: set[str]) -> float:
    """Sørensen-Dice coefficient: 2·|A ∩ B| / (|A| + |B|)."""
    total = len(set_a) + len(set_b)
    if total == 0:
        return 0.0
    return 2.0 * len(set_a & set_b) / total


def coverage(set_a: set[str], set_b: set[str]) -> tuple[float, float]:
    """Coverage percentages: (A covers B, B covers A).

    A covers B = |A ∩ B| / |B|  (how much of B is in A)
    B covers A = |A ∩ B| / |A|  (how much of A is in B)
    """
    intersection = len(set_a & set_b)
    cov_a_over_b = intersection / len(set_b) if set_b else 0.0
    cov_b_over_a = intersection / len(set_a) if set_a else 0.0
    return cov_a_over_b, cov_b_over_a


# ── Comparison result ─────────────────────────────────────────────────────────

class CompareResult:
    """Container for wordlist comparison results."""

    def __init__(
        self,
        path_a: str,
        path_b: str,
        set_a: set[str],
        set_b: set[str],
    ) -> None:
        self.path_a = path_a
        self.path_b = path_b
        self.size_a = len(set_a)
        self.size_b = len(set_b)
        self.intersection = set_a & set_b
        self.only_a = set_a - set_b
        self.only_b = set_b - set_a
        self.union_size = len(set_a | set_b)

        self.jaccard = jaccard(set_a, set_b)
        self.overlap = overlap_coefficient(set_a, set_b)
        self.dice = sorensen_dice(set_a, set_b)
        cov_ab, cov_ba = coverage(set_a, set_b)
        self.coverage_a_over_b = cov_ab
        self.coverage_b_over_a = cov_ba

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics to dict."""
        return {
            "file_a": self.path_a,
            "file_b": self.path_b,
            "size_a": self.size_a,
            "size_b": self.size_b,
            "intersection": len(self.intersection),
            "only_in_a": len(self.only_a),
            "only_in_b": len(self.only_b),
            "union": self.union_size,
            "jaccard": round(self.jaccard, 6),
            "overlap_coefficient": round(self.overlap, 6),
            "sorensen_dice": round(self.dice, 6),
            "coverage_a_over_b": round(self.coverage_a_over_b, 6),
            "coverage_b_over_a": round(self.coverage_b_over_a, 6),
        }

    def format_text(self) -> str:
        """Format result as human-readable text report."""
        name_a = Path(self.path_a).name
        name_b = Path(self.path_b).name
        w = max(len(name_a), len(name_b), 20)
        sep = "─" * (w + 30)

        lines = [
            sep,
            f"  Wordlist Comparison Report",
            sep,
            f"  File A: {name_a} ({self.size_a:,} entries)",
            f"  File B: {name_b} ({self.size_b:,} entries)",
            sep,
            f"  Common (A ∩ B):  {len(self.intersection):>12,}",
            f"  Only in A:       {len(self.only_a):>12,}",
            f"  Only in B:       {len(self.only_b):>12,}",
            f"  Union (A ∪ B):   {self.union_size:>12,}",
            sep,
            f"  Jaccard index:       {self.jaccard:>8.4f}  "
            f"({self.jaccard * 100:.2f}%)",
            f"  Overlap coeff:       {self.overlap:>8.4f}  "
            f"({self.overlap * 100:.2f}%)",
            f"  Sørensen-Dice:       {self.dice:>8.4f}  "
            f"({self.dice * 100:.2f}%)",
            f"  Coverage A→B:        {self.coverage_a_over_b:>8.4f}  "
            f"({self.coverage_a_over_b * 100:.2f}%)",
            f"  Coverage B→A:        {self.coverage_b_over_a:>8.4f}  "
            f"({self.coverage_b_over_a * 100:.2f}%)",
            sep,
        ]
        return "\n".join(lines)

    def format_csv(self) -> str:
        """Format result as CSV row (header + data)."""
        d = self.to_dict()
        header = ",".join(d.keys())
        values = ",".join(str(v) for v in d.values())
        return f"{header}\n{values}"


# ── Engine ────────────────────────────────────────────────────────────────────

class CompareEngine:
    """Wordlist comparison engine."""

    def __init__(
        self,
        path_a: str,
        path_b: str,
        case_insensitive: bool = False,
        sample: int = 0,
    ) -> None:
        self.path_a = path_a
        self.path_b = path_b
        self.case_insensitive = case_insensitive
        self.sample = sample
        self._set_a: Optional[set[str]] = None
        self._set_b: Optional[set[str]] = None
        self._result: Optional[CompareResult] = None

    def _load(self) -> None:
        """Load both wordlists."""
        self._set_a = _load_wordlist(
            self.path_a,
            case_insensitive=self.case_insensitive,
            sample=self.sample,
        )
        self._set_b = _load_wordlist(
            self.path_b,
            case_insensitive=self.case_insensitive,
            sample=self.sample,
        )
        logger.info(
            "Loaded %d entries from A, %d from B",
            len(self._set_a), len(self._set_b),
        )

    def compare(self) -> CompareResult:
        """Run comparison and return result."""
        if self._result is not None:
            return self._result
        if self._set_a is None or self._set_b is None:
            self._load()
        assert self._set_a is not None and self._set_b is not None
        self._result = CompareResult(
            self.path_a, self.path_b, self._set_a, self._set_b,
        )
        return self._result

    def iter_common(self) -> Generator[str, None, None]:
        """Yield entries present in both wordlists."""
        result = self.compare()
        yield from sorted(result.intersection)

    def iter_only_a(self) -> Generator[str, None, None]:
        """Yield entries present only in A."""
        result = self.compare()
        yield from sorted(result.only_a)

    def iter_only_b(self) -> Generator[str, None, None]:
        """Yield entries present only in B."""
        result = self.compare()
        yield from sorted(result.only_b)


# ── CLI handler ───────────────────────────────────────────────────────────────

def handle_compare(
    args: Any, ctx: dict[str, Any]
) -> Optional[Generator[str, None, None]]:
    """CLI handler for wordlist comparison."""
    file_a = getattr(args, "file_a", None)
    file_b = getattr(args, "file_b", None)
    fmt = getattr(args, "format", "text")
    case_insensitive = getattr(args, "case_insensitive", False)
    sample = getattr(args, "sample", 0) or 0
    output_common = getattr(args, "output_common", None)
    output_only_a = getattr(args, "output_only_a", None)
    output_only_b = getattr(args, "output_only_b", None)

    if not file_a or not file_b:
        logger.warning("Two wordlist files required. Use positional args.")
        return None

    for p in (file_a, file_b):
        if not Path(p).is_file():
            logger.error("File not found: %s", p)
            return None

    engine = CompareEngine(
        path_a=file_a,
        path_b=file_b,
        case_insensitive=case_insensitive,
        sample=sample,
    )
    result = engine.compare()

    if output_common:
        count = 0
        with open(output_common, "w", encoding="utf-8") as fh:
            for entry in engine.iter_common():
                fh.write(entry + "\n")
                count += 1
        logger.info("Wrote %d common entries to %s", count, output_common)

    if output_only_a:
        count = 0
        with open(output_only_a, "w", encoding="utf-8") as fh:
            for entry in engine.iter_only_a():
                fh.write(entry + "\n")
                count += 1
        logger.info("Wrote %d A-only entries to %s", count, output_only_a)

    if output_only_b:
        count = 0
        with open(output_only_b, "w", encoding="utf-8") as fh:
            for entry in engine.iter_only_b():
                fh.write(entry + "\n")
                count += 1
        logger.info("Wrote %d B-only entries to %s", count, output_only_b)

    if fmt == "json":
        def _gen_json() -> Generator[str, None, None]:
            yield json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        return _gen_json()

    if fmt == "csv":
        def _gen_csv() -> Generator[str, None, None]:
            yield result.format_csv()
        return _gen_csv()

    def _gen_text() -> Generator[str, None, None]:
        yield result.format_text()
    return _gen_text()

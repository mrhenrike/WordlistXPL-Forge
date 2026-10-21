"""
mask_analyzer.py: Hashcat mask frequency analysis for password corpora.

Converts each password to its hashcat mask representation (?u/?l/?d/?s/?b),
computes frequency-ranked mask tables, complexity scoring, charset position
heatmaps and exports top-N masks for targeted mask attacks.

Inspired by cracken mask analysis and PACK maskgen.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import csv
import io
import json
import logging
import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

CHARSET_UPPER = "?u"
CHARSET_LOWER = "?l"
CHARSET_DIGIT = "?d"
CHARSET_SPECIAL = "?s"
CHARSET_BYTE = "?b"

_CHARSETS = {
    CHARSET_UPPER: 26,
    CHARSET_LOWER: 26,
    CHARSET_DIGIT: 10,
    CHARSET_SPECIAL: 33,
    CHARSET_BYTE: 256,
}


def char_to_mask(ch: str) -> str:
    """Map a single character to its hashcat mask token."""
    if "A" <= ch <= "Z":
        return CHARSET_UPPER
    if "a" <= ch <= "z":
        return CHARSET_LOWER
    if "0" <= ch <= "9":
        return CHARSET_DIGIT
    o = ord(ch)
    if 0x20 <= o <= 0x7E:
        return CHARSET_SPECIAL
    return CHARSET_BYTE


def password_to_mask(password: str) -> str:
    """Convert a password string to its full hashcat mask."""
    return "".join(char_to_mask(ch) for ch in password)


def mask_keyspace(mask: str) -> int:
    """Calculate the total keyspace size for a given mask.

    Args:
        mask: Hashcat mask string (e.g. '?u?l?l?l?d?d').

    Returns:
        Number of possible candidates this mask can generate.
    """
    tokens = _parse_mask_tokens(mask)
    space = 1
    for tok in tokens:
        space *= _CHARSETS.get(tok, 256)
    return space


def mask_entropy(mask: str) -> float:
    """Calculate entropy in bits for a given mask."""
    ks = mask_keyspace(mask)
    if ks <= 1:
        return 0.0
    return math.log2(ks)


def mask_complexity_score(mask: str) -> float:
    """Score mask complexity on a 0-100 scale.

    Considers entropy, charset diversity, and length.
    """
    tokens = _parse_mask_tokens(mask)
    if not tokens:
        return 0.0

    entropy = mask_entropy(mask)
    unique_charsets = len(set(tokens))
    length = len(tokens)

    entropy_score = min(entropy / 128.0, 1.0) * 40
    diversity_score = (unique_charsets / len(_CHARSETS)) * 30
    length_score = min(length / 20.0, 1.0) * 30

    return round(entropy_score + diversity_score + length_score, 2)


def _parse_mask_tokens(mask: str) -> list[str]:
    """Parse a mask string into individual charset tokens."""
    tokens: list[str] = []
    i = 0
    while i < len(mask):
        if mask[i] == "?" and i + 1 < len(mask):
            tokens.append(mask[i : i + 2])
            i += 2
        else:
            tokens.append(CHARSET_BYTE)
            i += 1
    return tokens


@dataclass
class MaskStats:
    """Statistics for a single mask pattern."""

    mask: str
    count: int
    percentage: float
    keyspace: int
    entropy: float
    complexity: float
    length: int


@dataclass
class PositionHeatmap:
    """Charset frequency at each character position."""

    position: int
    upper: int = 0
    lower: int = 0
    digit: int = 0
    special: int = 0
    byte: int = 0

    @property
    def total(self) -> int:
        return self.upper + self.lower + self.digit + self.special + self.byte

    def dominant_charset(self) -> str:
        counts = {
            CHARSET_UPPER: self.upper,
            CHARSET_LOWER: self.lower,
            CHARSET_DIGIT: self.digit,
            CHARSET_SPECIAL: self.special,
            CHARSET_BYTE: self.byte,
        }
        return max(counts, key=counts.get)  # type: ignore[arg-type]


@dataclass
class MaskAnalysisResult:
    """Complete mask analysis result."""

    total_passwords: int
    unique_masks: int
    masks: list[MaskStats]
    heatmap: list[PositionHeatmap]
    length_distribution: dict[int, int]
    charset_summary: dict[str, int]


class MaskAnalyzer:
    """Analyze password corpora for mask frequency and patterns."""

    def __init__(self, max_length: int = 64) -> None:
        self._max_length = max_length
        self._mask_counter: Counter[str] = Counter()
        self._position_charsets: dict[int, Counter[str]] = {}
        self._length_counter: Counter[int] = Counter()
        self._charset_counter: Counter[str] = Counter()
        self._total = 0

    def feed(self, passwords: Iterable[str]) -> None:
        """Process a stream of passwords."""
        for pwd in passwords:
            pwd = pwd.rstrip("\n\r")
            if not pwd or len(pwd) > self._max_length:
                continue
            self._total += 1
            mask = password_to_mask(pwd)
            self._mask_counter[mask] += 1
            self._length_counter[len(pwd)] += 1

            for i, ch in enumerate(pwd):
                tok = char_to_mask(ch)
                self._charset_counter[tok] += 1
                if i not in self._position_charsets:
                    self._position_charsets[i] = Counter()
                self._position_charsets[i][tok] += 1

    def feed_file(self, path: Path, encoding: str = "utf-8") -> None:
        """Process passwords from a file, one per line."""
        with path.open("r", encoding=encoding, errors="replace") as fh:
            self.feed(fh)

    def analyze(self, top_n: int = 100) -> MaskAnalysisResult:
        """Generate analysis results."""
        masks: list[MaskStats] = []
        for mask, count in self._mask_counter.most_common(top_n):
            tokens = _parse_mask_tokens(mask)
            masks.append(
                MaskStats(
                    mask=mask,
                    count=count,
                    percentage=round(count / self._total * 100, 4) if self._total else 0.0,
                    keyspace=mask_keyspace(mask),
                    entropy=round(mask_entropy(mask), 2),
                    complexity=mask_complexity_score(mask),
                    length=len(tokens),
                )
            )

        max_pos = max(self._position_charsets.keys(), default=-1) + 1
        heatmap: list[PositionHeatmap] = []
        for pos in range(max_pos):
            pc = self._position_charsets.get(pos, Counter())
            heatmap.append(
                PositionHeatmap(
                    position=pos,
                    upper=pc.get(CHARSET_UPPER, 0),
                    lower=pc.get(CHARSET_LOWER, 0),
                    digit=pc.get(CHARSET_DIGIT, 0),
                    special=pc.get(CHARSET_SPECIAL, 0),
                    byte=pc.get(CHARSET_BYTE, 0),
                )
            )

        return MaskAnalysisResult(
            total_passwords=self._total,
            unique_masks=len(self._mask_counter),
            masks=masks,
            heatmap=heatmap,
            length_distribution=dict(sorted(self._length_counter.items())),
            charset_summary=dict(self._charset_counter.most_common()),
        )

    def reset(self) -> None:
        """Clear all accumulated state."""
        self._mask_counter.clear()
        self._position_charsets.clear()
        self._length_counter.clear()
        self._charset_counter.clear()
        self._total = 0


def export_top_masks(
    result: MaskAnalysisResult,
    top_n: int = 25,
    max_keyspace: int | None = None,
) -> list[str]:
    """Extract top-N masks suitable for hashcat mask attacks.

    Args:
        result: Analysis result from MaskAnalyzer.analyze().
        top_n: Maximum number of masks to return.
        max_keyspace: If set, exclude masks with keyspace above this threshold.

    Returns:
        List of mask strings ordered by frequency.
    """
    masks: list[str] = []
    for ms in result.masks[:top_n]:
        if max_keyspace is not None and ms.keyspace > max_keyspace:
            continue
        masks.append(ms.mask)
    return masks


def export_json(result: MaskAnalysisResult, path: Path | None = None) -> str:
    """Export analysis result as JSON."""
    data = {
        "total_passwords": result.total_passwords,
        "unique_masks": result.unique_masks,
        "charset_summary": result.charset_summary,
        "length_distribution": result.length_distribution,
        "masks": [
            {
                "mask": m.mask,
                "count": m.count,
                "percentage": m.percentage,
                "keyspace": m.keyspace,
                "entropy": m.entropy,
                "complexity": m.complexity,
                "length": m.length,
            }
            for m in result.masks
        ],
        "heatmap": [
            {
                "position": h.position,
                "upper": h.upper,
                "lower": h.lower,
                "digit": h.digit,
                "special": h.special,
                "byte": h.byte,
            }
            for h in result.heatmap
        ],
    }
    output = json.dumps(data, indent=2)
    if path:
        path.write_text(output, encoding="utf-8")
    return output


def export_csv(result: MaskAnalysisResult, path: Path | None = None) -> str:
    """Export mask frequency table as CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["rank", "mask", "count", "pct", "keyspace", "entropy", "complexity", "length"])
    for i, m in enumerate(result.masks, 1):
        writer.writerow([i, m.mask, m.count, m.percentage, m.keyspace, m.entropy, m.complexity, m.length])
    output = buf.getvalue()
    if path:
        path.write_text(output, encoding="utf-8")
    return output


def export_hcmask(result: MaskAnalysisResult, path: Path, top_n: int = 50) -> None:
    """Export masks in .hcmask format for hashcat."""
    masks = export_top_masks(result, top_n=top_n)
    path.write_text("\n".join(masks) + "\n", encoding="utf-8")
    logger.info("Exported %d masks to %s", len(masks), path)

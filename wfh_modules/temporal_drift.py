"""temporal_drift.py - Temporal password drift modeling.

Models how passwords evolve over time.  Users tend to increment years,
change season/event suffixes, apply periodic leet transformations, and
follow pop-culture references tied to specific years.

The model captures:
  1. Year token drift:  "2020" → "2021" → ... → "2026"
  2. Leet shift:        increasing leet substitution over time
  3. Complexity creep:  gradual addition of special chars to simple patterns
  4. Seasonal tokens:   summer/winter/carnival/copa/etc by year

Usage:
  engine = TemporalDriftEngine(base_year=2019, target_year=2026)
  for pw, score in engine.generate(seed_words=["muralha", "empresa123"]):
      print(pw)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import itertools
import re
import string
from dataclasses import dataclass, field
from typing import Generator, Iterator, Optional


# ── Year / date patterns ──────────────────────────────────────────────────────

def _year_variants(year: int) -> list[str]:
    y = str(year)
    return [y, y[-2:], y[2:], f"@{y}", f"{y}!"]


def _year_range(start: int, end: int) -> list[int]:
    return list(range(start, end + 1))


# ── Leet shift (escalates with time delta) ───────────────────────────────────

_LEET_TABLE: dict[str, list[str]] = {
    "a": ["@", "4"],
    "e": ["3"],
    "i": ["1", "!"],
    "o": ["0"],
    "s": ["$", "5"],
    "t": ["7"],
    "l": ["1"],
    "b": ["8"],
    "g": ["9"],
}


def _apply_leet(word: str, level: int) -> Iterator[str]:
    """Yield leet variants at a given substitution level (0=none, 3=all)."""
    chars = list(word.lower())
    positions = [i for i, c in enumerate(chars) if c in _LEET_TABLE]
    if not positions or level == 0:
        yield word
        return
    k = min(level, len(positions))
    for combo in itertools.combinations(positions, k):
        new_chars = chars[:]
        for pos in combo:
            c = new_chars[pos]
            subs = _LEET_TABLE.get(c, [c])
            new_chars[pos] = subs[0]
        yield "".join(new_chars)


# ── Seasonal / cultural tokens by year ───────────────────────────────────────

_SEASONAL_TOKENS: dict[int, list[str]] = {
    2019: ["2019", "copa", "eleicao", "bolsonaro"],
    2020: ["2020", "covid", "pandemia", "quarentena", "mask"],
    2021: ["2021", "vacina", "lockdown"],
    2022: ["2022", "copa2022", "lula", "eleicao22"],
    2023: ["2023", "lula2023", "ia", "chatgpt"],
    2024: ["2024", "ai", "deepfake", "copa24"],
    2025: ["2025", "claude", "llm", "gen-ai", "copa25"],
    2026: ["2026", "copa26", "ia2026"],
}

_COMPLEXITY_SUFFIX: list[str] = ["!", "@", "#", "123", "!", "1", "_", "@2024"]


# ── Drift mutations ───────────────────────────────────────────────────────────

def _year_increment_variants(pw: str, target_year: int) -> list[str]:
    """Replace any 4-digit year in password with years up to target_year."""
    matches = list(re.finditer(r"(20\d{2})", pw))
    if not matches:
        return []
    results = []
    for m in matches:
        old_year = int(m.group(1))
        for new_year in range(old_year + 1, target_year + 1):
            results.append(pw[:m.start()] + str(new_year) + pw[m.end():])
    return results


def _complexity_creep(pw: str) -> list[str]:
    """Add specials/digits to password that lacks them."""
    results = []
    if not any(c.isdigit() for c in pw):
        for suf in ["1", "123", "2026", "01"]:
            results.append(pw + suf)
    if not any(c in string.punctuation for c in pw):
        for suf in ["!", "@", "#", "_"]:
            results.append(pw + suf)
    return results


def _seasonal_blend(pw: str, year: int) -> list[str]:
    tokens = _SEASONAL_TOKENS.get(year, [])
    return [pw + tok for tok in tokens[:3]] + [tok + pw for tok in tokens[:2]]


# ── Engine ────────────────────────────────────────────────────────────────────

@dataclass
class DriftConfig:
    base_year: int = 2019
    target_year: int = 2026
    leet_max_level: int = 2
    include_seasonal: bool = True
    include_year_increment: bool = True
    include_complexity_creep: bool = True


class TemporalDriftEngine:
    """Models temporal password evolution to generate drift-aware candidates.

    Takes seed words/passwords and applies year increments, leet escalation,
    seasonal tokens, and complexity creep across a time span.
    """

    def __init__(
        self,
        base_year: int = 2019,
        target_year: int = 2026,
        leet_max_level: int = 2,
        include_seasonal: bool = True,
    ) -> None:
        self.cfg = DriftConfig(
            base_year=base_year,
            target_year=target_year,
            leet_max_level=leet_max_level,
            include_seasonal=include_seasonal,
        )
        self._drift_years = _year_range(base_year, target_year)

    def _apply_drift(self, seed: str) -> Generator[tuple[str, float], None, None]:
        """Yield all drift variants of a seed word."""
        # Original with year variants
        for year in self._drift_years:
            for yv in _year_variants(year):
                yield (seed + yv, 0.75)
                yield (yv + seed, 0.65)

        # Year increment (replace embedded years)
        if self.cfg.include_year_increment:
            for variant in _year_increment_variants(seed, self.cfg.target_year):
                yield (variant, 0.80)

        # Leet progressively
        for level in range(1, self.cfg.leet_max_level + 1):
            for leet_variant in _apply_leet(seed, level):
                if leet_variant != seed:
                    yield (leet_variant, 0.60)
                    # leet + years
                    for year in self._drift_years[-3:]:
                        for yv in _year_variants(year)[:2]:
                            yield (leet_variant + yv, 0.65)

        # Complexity creep
        if self.cfg.include_complexity_creep:
            for variant in _complexity_creep(seed):
                yield (variant, 0.55)

        # Seasonal
        if self.cfg.include_seasonal:
            for year in self._drift_years:
                for variant in _seasonal_blend(seed, year):
                    yield (variant, 0.50)

    def generate(
        self,
        seed_words: Optional[list[str]] = None,
        profile: Optional[dict] = None,
        max_candidates: int = 200_000,
    ) -> Generator[tuple[str, float], None, None]:
        """Generate temporally-drifted candidates from seed words."""
        seeds: list[str] = list(seed_words or [])

        # Extract seeds from profile
        if profile:
            name = profile.get("full_name", "") or profile.get("short_name", "")
            if name:
                for part in re.split(r"\s+", name):
                    if part:
                        seeds.append(part)
            seeds.extend(str(k) for k in profile.get("keywords", []))
            pets = profile.get("pets", [])
            if isinstance(pets, list):
                seeds.extend(str(p) for p in pets)

        if not seeds:
            # generic seed set
            seeds = ["senha", "admin", "user", "pass", "root", "empresa"]

        yielded: set[str] = set()
        count = 0
        for seed in seeds:
            for pw, score in self._apply_drift(seed):
                if pw not in yielded and len(pw) >= 4:
                    yielded.add(pw)
                    yield (pw, score)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return

    def describe(self) -> str:
        return (
            f"TemporalDriftEngine  {self.cfg.base_year}→{self.cfg.target_year}\n"
            f"  leet_max={self.cfg.leet_max_level}  "
            f"seasonal={self.cfg.include_seasonal}  "
            f"year_incr={self.cfg.include_year_increment}"
        )

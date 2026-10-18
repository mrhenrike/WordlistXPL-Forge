"""phonetic_engine.py - Phonetic similarity password generator.

Generates password candidates by finding words that sound similar to seed
words from the target profile.  Uses Soundex, Metaphone and Double Metaphone
algorithms (pure-Python, no external dependencies) to build a phonetic
neighbourhood, then applies common character substitutions to expand the
candidate space.

Useful against passphrases: users often choose passwords that sound like
familiar words but with visual/phonetic substitutions.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import itertools
import logging
import re
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


# ── Soundex ──────────────────────────────────────────────────────────────────

_SOUNDEX_MAP: dict[str, str] = {
    "b": "1", "f": "1", "p": "1", "v": "1",
    "c": "2", "g": "2", "j": "2", "k": "2", "q": "2", "s": "2",
    "x": "2", "z": "2",
    "d": "3", "t": "3",
    "l": "4",
    "m": "5", "n": "5",
    "r": "6",
}


def soundex(word: str) -> str:
    """Compute Soundex code for a word (4-character string)."""
    cleaned = re.sub(r"[^a-zA-Z]", "", word).upper()
    if not cleaned:
        return "Z000"
    first = cleaned[0]
    digits: list[str] = []
    prev = _SOUNDEX_MAP.get(first.lower(), "0")
    for ch in cleaned[1:]:
        code = _SOUNDEX_MAP.get(ch.lower(), "0")
        if code != "0" and code != prev:
            digits.append(code)
        prev = code
        if len(digits) >= 3:
            break
    return (first + "".join(digits)).ljust(4, "0")[:4]


# ── Metaphone ────────────────────────────────────────────────────────────────

def metaphone(word: str) -> str:
    """Compute a simplified Metaphone code for a word."""
    w = re.sub(r"[^a-zA-Z]", "", word).upper()
    if not w:
        return ""

    if w[:2] in ("AE", "GN", "KN", "PN", "WR"):
        w = w[1:]

    result: list[str] = []
    i = 0
    while i < len(w) and len(result) < 8:
        c = w[i]

        if c in "AEIOU":
            if i == 0:
                result.append(c)
            i += 1
            continue

        pair = w[i:i + 2]
        triple = w[i:i + 3]

        if c == "B":
            if not (i == len(w) - 1 and i >= 1 and w[i - 1] == "M"):
                result.append("B")
            i += 1
        elif c == "C":
            if pair in ("CI", "CE", "CY"):
                result.append("S")
            elif pair == "CH":
                result.append("X")
                i += 1
            else:
                result.append("K")
            i += 1
        elif c == "D":
            if pair in ("DG",):
                nxt = w[i + 2:i + 3]
                if nxt in ("I", "E", "Y"):
                    result.append("J")
                    i += 1
                else:
                    result.append("T")
            else:
                result.append("T")
            i += 1
        elif c == "F":
            result.append("F")
            i += 2 if pair == "FF" else 1
        elif c == "G":
            if i > 0 and w[i - 1] in "AEIOU" and pair in ("GH",):
                i += 2
                continue
            if pair in ("GN",) and i == len(w) - 2:
                i += 2
                continue
            if i > 0 and w[i - 1] == "G":
                i += 1
                continue
            result.append("K" if pair not in ("GI", "GE", "GY") else "J")
            i += 1
        elif c == "H":
            if i == 0 or w[i - 1] not in "AEIOU":
                nxt = w[i + 1:i + 2]
                if nxt in ("A", "E", "I", "O", "U"):
                    result.append("H")
            i += 1
        elif c == "J":
            result.append("J")
            i += 1
        elif c == "K":
            if i == 0 or w[i - 1] != "C":
                result.append("K")
            i += 1
        elif c == "L":
            result.append("L")
            i += 1
        elif c == "M":
            result.append("M")
            i += 1
        elif c == "N":
            result.append("N")
            i += 1
        elif c == "P":
            if pair == "PH":
                result.append("F")
                i += 2
            else:
                result.append("P")
                i += 1
        elif c == "Q":
            result.append("K")
            i += 1
        elif c == "R":
            result.append("R")
            i += 1
        elif c == "S":
            if triple == "SCH":
                result.append("SK")
                i += 3
            elif pair in ("SH", "SI", "SO"):
                result.append("X" if pair == "SH" else "S")
                i += 2 if pair == "SH" else 1
            else:
                result.append("S")
                i += 1
        elif c == "T":
            if pair == "TH":
                result.append("0")
                i += 2
            else:
                result.append("T")
                i += 1
        elif c == "V":
            result.append("F")
            i += 1
        elif c == "W":
            nxt = w[i + 1:i + 2]
            if nxt in ("A", "E", "I", "O", "U"):
                result.append("W")
            i += 1
        elif c == "X":
            result.append("KS")
            i += 1
        elif c == "Y":
            nxt = w[i + 1:i + 2]
            if nxt in ("A", "E", "I", "O", "U"):
                result.append("Y")
            i += 1
        elif c == "Z":
            result.append("S")
            i += 1
        else:
            i += 1

    return "".join(result)


# ── Substitution maps ────────────────────────────────────────────────────────

_PHONETIC_SUBS: dict[str, list[str]] = {
    "a": ["@", "4", "a", "A"],
    "e": ["3", "e", "E"],
    "i": ["1", "!", "i", "I"],
    "o": ["0", "o", "O"],
    "u": ["u", "U"],
    "s": ["$", "5", "z", "s", "S"],
    "t": ["+", "7", "t", "T"],
    "l": ["1", "|", "l", "L"],
    "b": ["8", "b", "B"],
    "g": ["9", "g", "G"],
}

_VISUAL_SUBS: dict[str, list[str]] = {
    "c": ["(", "c", "C", "k"],
    "k": ["k", "K", "c"],
    "f": ["ph", "f", "F"],
    "ph": ["f", "ph", "PH"],
    "x": ["ks", "x", "X"],
    "ck": ["k", "c", "ck"],
    "w": ["vv", "w", "W"],
    "z": ["s", "z", "Z"],
}


def _apply_substitutions(
    word: str,
    max_variants: int = 50,
) -> Generator[str, None, None]:
    """Generate visual/phonetic substitution variants of a word."""
    lower = word.lower()
    positions: list[list[str]] = []
    i = 0
    while i < len(lower):
        ch = lower[i]
        digraph = lower[i:i + 2]
        if digraph in _VISUAL_SUBS:
            positions.append(_VISUAL_SUBS[digraph])
            i += 2
        elif ch in _PHONETIC_SUBS:
            positions.append(_PHONETIC_SUBS[ch])
            i += 1
        elif ch in _VISUAL_SUBS:
            positions.append(_VISUAL_SUBS[ch])
            i += 1
        else:
            positions.append([ch, ch.upper()] if ch.isalpha() else [ch])
            i += 1

    count = 0
    for combo in itertools.product(*positions):
        variant = "".join(combo)
        if variant != word:
            yield variant
            count += 1
            if count >= max_variants:
                return


def _case_variants(word: str) -> list[str]:
    """Generate common casing variants."""
    return list({
        word.lower(),
        word.upper(),
        word.capitalize(),
        word[0].upper() + word[1:] if len(word) > 1 else word.upper(),
        word.swapcase(),
    })


# ── Phonetic Engine ──────────────────────────────────────────────────────────

_COMMON_SUFFIXES: list[str] = [
    "", "1", "12", "123", "!", "!!", "!1", "#", "@", "2026", "2025",
    "01", "007", "69", "666", "00", "99", "11", "22", "321",
]


class PhoneticEngine:
    """Password generator based on phonetic similarity."""

    def __init__(
        self,
        seeds: Optional[list[str]] = None,
        profile: Optional[dict[str, Any]] = None,
        max_subs_per_word: int = 30,
    ) -> None:
        self._seeds: list[str] = seeds or []
        if profile:
            self._seeds.extend(_extract_seeds(profile))
        self._max_subs = max_subs_per_word

    def generate(
        self,
        max_candidates: int = 10_000,
        min_len: int = 4,
        max_len: int = 32,
    ) -> Generator[str, None, None]:
        """Yield password candidates based on phonetic similarity."""
        seen: set[str] = set()
        count = 0

        for seed in self._seeds:
            if not seed or len(seed) < 2:
                continue

            case_vars = _case_variants(seed)
            for variant in case_vars:
                for suffix in _COMMON_SUFFIXES:
                    candidate = variant + suffix
                    if min_len <= len(candidate) <= max_len and candidate not in seen:
                        seen.add(candidate)
                        yield candidate
                        count += 1
                        if count >= max_candidates:
                            return

            for sub_variant in _apply_substitutions(seed, self._max_subs):
                for suffix in _COMMON_SUFFIXES:
                    candidate = sub_variant + suffix
                    if min_len <= len(candidate) <= max_len and candidate not in seen:
                        seen.add(candidate)
                        yield candidate
                        count += 1
                        if count >= max_candidates:
                            return

    def soundex_group(self) -> dict[str, list[str]]:
        """Group seeds by their Soundex code."""
        groups: dict[str, list[str]] = {}
        for seed in self._seeds:
            code = soundex(seed)
            groups.setdefault(code, []).append(seed)
        return groups

    def metaphone_group(self) -> dict[str, list[str]]:
        """Group seeds by their Metaphone code."""
        groups: dict[str, list[str]] = {}
        for seed in self._seeds:
            code = metaphone(seed)
            if code:
                groups.setdefault(code, []).append(seed)
        return groups


def _extract_seeds(profile: dict[str, Any]) -> list[str]:
    """Extract seed words from a target profile dict."""
    seeds: list[str] = []
    for key in ("full_name", "short_name", "username", "nickname", "company"):
        val = profile.get(key, "")
        if val:
            seeds.extend(str(val).split())
    keywords = profile.get("keywords", [])
    if isinstance(keywords, list):
        seeds.extend(str(k) for k in keywords)
    pets = profile.get("pets", [])
    if isinstance(pets, list):
        seeds.extend(str(p) for p in pets)
    return [s for s in seeds if len(s) >= 2]


# ── CLI handler ──────────────────────────────────────────────────────────────

def handle_phonetic(args: Any, ctx: dict[str, Any]) -> Optional[Generator[str, None, None]]:
    """CLI handler for phonetic password generation."""
    seeds: list[str] = []

    seed_arg = getattr(args, "seed", None)
    if seed_arg:
        seeds.extend(seed_arg.split(","))

    wordlist = getattr(args, "wordlist", None)
    if wordlist:
        from pathlib import Path
        text = Path(wordlist).read_text(encoding="utf-8", errors="ignore")
        seeds.extend(line.strip() for line in text.splitlines() if line.strip())

    profile_path = getattr(args, "profile", None)
    profile: Optional[dict[str, Any]] = None
    if profile_path:
        import json
        from pathlib import Path
        profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))

    if getattr(args, "analyze", False) and seeds:
        engine = PhoneticEngine(seeds=seeds, profile=profile)
        lines = ["Phonetic Analysis:"]
        lines.append(f"\nSoundex groups ({len(engine.soundex_group())}):")
        for code, words in sorted(engine.soundex_group().items()):
            lines.append(f"  {code}: {', '.join(words)}")
        lines.append(f"\nMetaphone groups ({len(engine.metaphone_group())}):")
        for code, words in sorted(engine.metaphone_group().items()):
            lines.append(f"  {code}: {', '.join(words)}")
        return iter(["\n".join(lines)])  # type: ignore[return-value]

    if not seeds and not profile:
        logger.warning("No seeds provided. Use --seed or --profile.")
        return None

    engine = PhoneticEngine(
        seeds=seeds,
        profile=profile,
        max_subs_per_word=getattr(args, "max_subs", 30),
    )
    return engine.generate(
        max_candidates=getattr(args, "limit", 10_000) or 10_000,
        min_len=getattr(args, "min_len", 4),
        max_len=getattr(args, "max_len", 32),
    )

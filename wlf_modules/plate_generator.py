"""
plate_generator.py - Generate password candidates from license plate patterns worldwide.

PII analysis found 9,296 plate-pattern matches in leaked password databases.
Users often use their license plate (with or without separators) as passwords,
combined with common suffixes, reversed, or mutated.

Supports:
  - Input sanitization: strips separators, keeps alphanumeric
  - Per-plate candidate generation: case variants, suffixes, reversals, substrings
  - Country-based random plate generation using regex-defined formats
  - Batch generation for multiple plates
  - 93 countries across 6 continents with legacy and current formats

Examples:
  from wlf_modules.plate_generator import generate_from_plate, list_countries
  for candidate in generate_from_plate("ABC-1D23"):
      print(candidate)

  for country in list_countries():
      print(country["code"], country["name"])

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
import random
import re
from collections.abc import Generator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

_SEPARATOR_RE = re.compile(r"[-/\\_.\s]")

_COMMON_SUFFIXES: list[str] = [
    "!", "@", "#", "123", "1234", "2024", "2025", "2026",
    "!!", "##", "@@", "01", "00", "1", "12",
]

_YEAR_SUFFIXES: list[str] = [str(y) for y in range(1970, 2027)]

_SPECIAL_CHARS: list[str] = ["!", "@", "#", "$", "%", "&", "*"]

# Module-level cache for loaded patterns
_patterns_cache: dict[str, Any] | None = None


# ── Pattern loading ──────────────────────────────────────────────────────────

def _default_json_path() -> Path:
    """Return default path for plate_patterns_worldwide.json relative to repo root."""
    return Path(__file__).resolve().parents[1] / "data" / "plate_patterns_worldwide.json"


def load_plate_patterns(json_path: Path | None = None) -> dict[str, Any]:
    """Load plate patterns from the JSON data file.

    Args:
        json_path: Path to the JSON file. Defaults to data/plate_patterns_worldwide.json.

    Returns:
        Parsed JSON dictionary with country plate formats.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    global _patterns_cache

    path = json_path or _default_json_path()

    if _patterns_cache is not None and json_path is None:
        return _patterns_cache

    with open(path, encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)

    if json_path is None:
        _patterns_cache = data

    logger.debug("Loaded plate patterns: %d countries", len(data.get("countries", [])))
    return data


def _get_country_data(country_code: str) -> dict[str, Any] | None:
    """Find country entry by ISO 2-letter code (case-insensitive)."""
    data = load_plate_patterns()
    code_upper = country_code.upper()
    for country in data.get("countries", []):
        if country.get("code", "").upper() == code_upper:
            result: dict[str, Any] = country
            return result
    return None


# ── Sanitization ─────────────────────────────────────────────────────────────

def sanitize_plate(raw: str) -> str:
    """Remove separators (-/\\_. space) and keep only [A-Za-z0-9].

    Args:
        raw: Raw plate string with possible separators.

    Returns:
        Cleaned alphanumeric-only string.
    """
    stripped = _SEPARATOR_RE.sub("", raw)
    return re.sub(r"[^A-Za-z0-9]", "", stripped)


# ── Per-plate candidate generation ───────────────────────────────────────────

def _extract_parts(plate: str) -> tuple[str, str]:
    """Split plate into letters-only and digits-only parts."""
    letters = re.sub(r"[^A-Za-z]", "", plate)
    digits = re.sub(r"[^0-9]", "", plate)
    return letters, digits


def generate_from_plate(
    plate: str,
    with_case_variants: bool = True,
    with_numbers: bool = True,
    with_specials: bool = True,
) -> Generator[str, None, None]:
    """Generate password candidates from a single license plate string.

    Given an input plate like "ABC1D23", yields:
      - Sanitized plate (uppercase, lowercase, original)
      - With common suffixes: !, @, #, 123, 1234, 2024, 2025, 2026
      - Reversed
      - Substrings (letters-only part, digits-only part)
      - Common mutations: plate+year, plate+special combos

    Args:
        plate: License plate string (may include separators).
        with_case_variants: Emit upper/lower/title case variants.
        with_numbers: Emit numeric suffix variants.
        with_specials: Emit special character suffix variants.

    Yields:
        Password candidate strings.
    """
    clean = sanitize_plate(plate)
    if not clean:
        return

    seen: set[str] = set()

    def _emit(candidate: str) -> Generator[str, None, None]:
        if candidate and candidate not in seen:
            seen.add(candidate)
            yield candidate

    # Base forms
    yield from _emit(clean)
    if with_case_variants:
        yield from _emit(clean.upper())
        yield from _emit(clean.lower())
        yield from _emit(clean.capitalize())
        yield from _emit(clean.swapcase())

    # Reversed
    reversed_plate = clean[::-1]
    yield from _emit(reversed_plate)
    if with_case_variants:
        yield from _emit(reversed_plate.upper())
        yield from _emit(reversed_plate.lower())

    # Substrings: letters-only and digits-only
    letters, digits = _extract_parts(clean)
    if letters:
        yield from _emit(letters)
        if with_case_variants:
            yield from _emit(letters.upper())
            yield from _emit(letters.lower())
    if digits and len(digits) >= 2:
        yield from _emit(digits)

    # Common suffixes
    bases = [clean]
    if with_case_variants:
        bases.extend([clean.upper(), clean.lower()])

    for base in bases:
        for suffix in _COMMON_SUFFIXES:
            yield from _emit(base + suffix)

    # Year suffixes (common passwords: plate + birth/registration year)
    if with_numbers:
        for base in bases:
            for year in _YEAR_SUFFIXES:
                yield from _emit(base + year)

    # Special char prefixes and suffixes
    if with_specials:
        for base in bases:
            for ch in _SPECIAL_CHARS:
                yield from _emit(ch + base)
                yield from _emit(base + ch)

    # Mixed: digits part + letters part, letters + digits
    if letters and digits:
        yield from _emit(digits + letters)
        yield from _emit(digits + letters.lower())
        yield from _emit(letters + digits)
        yield from _emit(letters.lower() + digits)

    # No-vowel variant (leet-adjacent simplification)
    no_vowels = re.sub(r"[AEIOUaeiou]", "", clean)
    if no_vowels != clean:
        yield from _emit(no_vowels)


# ── Country-based plate generation ───────────────────────────────────────────

def _expand_charset(charset_spec: str) -> str:
    """Expand a charset spec like 'A-Z' or 'BCDFGHJKLPRSTVWXYZ' into character string."""
    # Handle explicit range like A-Z or 0-9
    range_match = re.match(r"^([A-Za-z0-9])-([A-Za-z0-9])$", charset_spec)
    if range_match:
        start, end = range_match.group(1), range_match.group(2)
        return "".join(chr(c) for c in range(ord(start), ord(end) + 1))
    # Already an explicit list of chars
    return charset_spec


def _parse_pattern_segments(pattern: str) -> list[tuple[str, int, int]]:
    """Parse a regex-style pattern into segments of (charset_type, min_count, max_count).

    Recognizes:
      - [A-Z], [0-9], [A-Za-z0-9], [BCDF...] with {n}, {n,m} or plain
      - Literal characters like 'T' or 'U'
      - Quantifiers: {n}, {n,m}, plain (=1)

    Returns:
        List of (charset_or_literal, min_repeat, max_repeat) tuples.
    """
    segments: list[tuple[str, int, int]] = []
    i = 0
    while i < len(pattern):
        if pattern[i] == "[":
            # Character class
            end = pattern.index("]", i)
            charset_raw = pattern[i + 1 : end]
            i = end + 1

            # Parse quantifier
            min_n, max_n = 1, 1
            if i < len(pattern) and pattern[i] == "{":
                q_end = pattern.index("}", i)
                q_str = pattern[i + 1 : q_end]
                if "," in q_str:
                    parts = q_str.split(",")
                    min_n = int(parts[0])
                    max_n = int(parts[1]) if parts[1] else min_n
                else:
                    min_n = max_n = int(q_str)
                i = q_end + 1

            charset = _expand_charset(charset_raw)
            segments.append((charset, min_n, max_n))
        else:
            # Literal character
            lit = pattern[i]
            i += 1
            segments.append((lit, 1, 1))

    return segments


def _generate_plate_from_segments(
    segments: list[tuple[str, int, int]],
    rng: random.Random,
) -> str:
    """Generate one random plate string from parsed pattern segments."""
    parts: list[str] = []
    for charset, min_n, max_n in segments:
        count = rng.randint(min_n, max_n)
        if len(charset) == 1 and min_n == max_n == 1:
            # Literal character
            parts.append(charset)
        else:
            parts.append("".join(rng.choice(charset) for _ in range(count)))
    return "".join(parts)


def generate_country_plates(
    country_code: str,
    era: str = "current",
    max_per_format: int = 1000,
    seed: int | None = None,
) -> Generator[str, None, None]:
    """Generate random valid license plates for a country using pattern definitions.

    Uses the JSON pattern data to understand the plate structure and generates
    charset-based candidates. Uses random.Random(seed) for reproducibility.

    Args:
        country_code: ISO 2-letter country code (e.g. "BR", "US", "DE").
        era: Filter formats by era: "current", "legacy", or "all".
        max_per_format: Maximum plates to generate per format definition.
        seed: Random seed for reproducible generation.

    Yields:
        Random plate strings matching the country's format(s).
    """
    country = _get_country_data(country_code)
    if country is None:
        logger.warning("Unknown country code: %s", country_code)
        return

    rng = random.Random(seed)
    formats = country.get("formats", [])

    for fmt in formats:
        fmt_era = fmt.get("era", "current")
        if era != "all" and fmt_era != era:
            continue

        pattern = fmt.get("pattern", "")
        if not pattern:
            continue

        try:
            segments = _parse_pattern_segments(pattern)
        except (ValueError, IndexError) as exc:
            logger.warning("Failed to parse pattern '%s' for %s: %s", pattern, country_code, exc)
            continue

        seen: set[str] = set()
        for _ in range(max_per_format):
            plate = _generate_plate_from_segments(segments, rng)
            if plate not in seen:
                seen.add(plate)
                yield plate


# ── Listing ──────────────────────────────────────────────────────────────────

def list_countries() -> list[dict[str, str]]:
    """Return list of {code, name, continent} for all supported countries.

    Returns:
        List of dictionaries with country metadata.
    """
    data = load_plate_patterns()
    result: list[dict[str, str]] = []
    for country in data.get("countries", []):
        result.append({
            "code": country.get("code", ""),
            "name": country.get("name", ""),
            "continent": country.get("continent", ""),
        })
    return result


def list_formats(country_code: str) -> list[dict[str, str]]:
    """Return available plate formats for a country.

    Args:
        country_code: ISO 2-letter country code.

    Returns:
        List of format dictionaries with pattern, description, era, example.
    """
    country = _get_country_data(country_code)
    if country is None:
        return []

    result: list[dict[str, str]] = []
    for fmt in country.get("formats", []):
        result.append({
            "pattern": fmt.get("pattern", ""),
            "description": fmt.get("description", ""),
            "era": fmt.get("era", ""),
            "example": fmt.get("example", ""),
        })
    return result


# ── Batch generation ─────────────────────────────────────────────────────────

def generate_from_plates(
    plates: list[str],
    **kwargs: Any,
) -> Generator[str, None, None]:
    """Generate password candidates from multiple license plates.

    Deduplicates across all plates to avoid repeated candidates.

    Args:
        plates: List of plate strings (may include separators).
        **kwargs: Extra arguments forwarded to generate_from_plate().

    Yields:
        Unique password candidate strings across all input plates.
    """
    global_seen: set[str] = set()
    for plate in plates:
        for candidate in generate_from_plate(plate, **kwargs):
            if candidate not in global_seen:
                global_seen.add(candidate)
                yield candidate

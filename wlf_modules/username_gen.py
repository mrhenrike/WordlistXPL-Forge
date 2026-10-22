"""
username_gen.py - Personal username generation from PII fields.

Generates candidate usernames from a person's first name, last name,
nickname, and optional birth year using 50+ naming formats commonly
found in social media, email providers, and internal systems.

Inspired by the format library of username-anarchy (urbanadventurer).

Usage (as library):
    from wlf_modules.username_gen import generate_usernames
    for u in generate_usernames("Juliana", "Oliveira", nickname="ju", year="1991"):
        print(u)

Usage (CLI):
    wlf.py username --first juliana --last oliveira --nick ju --year 1991

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import logging
import unicodedata
from collections.abc import Generator
from typing import Any

logger = logging.getLogger(__name__)

__info__ = {
    "name": "username_gen",
    "version": "1.0.0",
    "author": "Andre Henrique (@mrhenrike)",
    "description": "Personal username generation from PII (50+ formats)",
    "category": "enumeration",
    "tags": ["username", "enumeration", "pii", "osint"],
}


def _normalize(text: str) -> str:
    """Strip accents and lowercase."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def _initials(name: str) -> str:
    """Return the first character of a name."""
    return name[0] if name else ""


def _build_patterns(
    first: str,
    last: str,
    nick: str,
    year: str,
) -> list[str]:
    """Build all username format patterns from the given PII fields.

    Returns a list of raw username strings (may contain duplicates and empties).
    """
    f = first
    l = last
    fi = _initials(f)
    li = _initials(l)
    n = nick
    y4 = year
    y2 = year[2:] if len(year) == 4 else year

    patterns: list[str] = []

    if f:
        patterns.append(f)
    if l:
        patterns.append(l)
    if n:
        patterns.append(n)

    if f and l:
        patterns.extend([
            f"{f}{l}",
            f"{f}.{l}",
            f"{f}_{l}",
            f"{f}-{l}",
            f"{l}{f}",
            f"{l}.{f}",
            f"{l}_{f}",
            f"{l}-{f}",
            f"{fi}{l}",
            f"{fi}.{l}",
            f"{fi}_{l}",
            f"{fi}-{l}",
            f"{f}{li}",
            f"{f}.{li}",
            f"{f}_{li}",
            f"{fi}{li}",
            f"{l}{fi}",
            f"{l}.{fi}",
            f"{l}_{fi}",
            f"{li}{f}",
            f"{f}{l[0:3]}",
            f"{f[0:3]}{l}",
            f"{f[0:3]}{l[0:3]}",
        ])

    if f and y4:
        patterns.extend([
            f"{f}{y4}",
            f"{f}{y2}",
            f"{f}_{y4}",
            f"{f}_{y2}",
            f"{f}.{y4}",
            f"{f}.{y2}",
            f"{y4}{f}",
            f"{y2}{f}",
        ])

    if l and y4:
        patterns.extend([
            f"{l}{y4}",
            f"{l}{y2}",
            f"{l}_{y4}",
            f"{l}_{y2}",
        ])

    if f and l and y4:
        patterns.extend([
            f"{f}{l}{y4}",
            f"{f}{l}{y2}",
            f"{f}.{l}{y4}",
            f"{f}.{l}{y2}",
            f"{f}_{l}{y4}",
            f"{f}_{l}{y2}",
            f"{fi}{l}{y4}",
            f"{fi}{l}{y2}",
            f"{l}{f}{y4}",
            f"{l}{f}{y2}",
            f"{f}{l[0:3]}{y2}",
            f"{fi}{li}{y4}",
            f"{fi}{li}{y2}",
        ])

    if n and y4:
        patterns.extend([
            f"{n}{y4}",
            f"{n}{y2}",
            f"{n}_{y4}",
            f"{n}_{y2}",
        ])

    if n and l:
        patterns.extend([
            f"{n}{l}",
            f"{n}.{l}",
            f"{n}_{l}",
            f"{l}{n}",
        ])

    if n and f and n != f:
        patterns.extend([
            f"{n}{f}",
            f"{f}{n}",
        ])

    for base in [f, n]:
        if not base:
            continue
        patterns.extend([
            f"{base}123",
            f"{base}_",
            f"_{base}",
            f"x{base}",
            f"{base}x",
            f"the{base}",
            f"real{base}",
            f"mr{base}",
            f"ms{base}",
            f"its{base}",
        ])

    return patterns


def generate_usernames(
    first_name: str,
    last_name: str = "",
    *,
    nickname: str = "",
    year: str = "",
    max_results: int = 0,
) -> Generator[str, None, None]:
    """Generate username candidates from personal information.

    Args:
        first_name: Target's first name.
        last_name: Target's last/family name.
        nickname: Optional nickname or handle.
        year: Optional 4-digit birth year.
        max_results: Limit output (0 = unlimited).

    Yields:
        Unique username strings, shortest first.
    """
    f = _normalize(first_name)
    l = _normalize(last_name)
    n = _normalize(nickname) if nickname else ""
    y = year.strip()

    raw = _build_patterns(f, l, n, y)

    seen: set[str] = set()
    results: list[str] = []

    for u in raw:
        u = u.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        results.append(u)

    results.sort(key=len)

    emitted = 0
    for u in results:
        yield u
        emitted += 1
        if max_results and emitted >= max_results:
            return


def run(
    first_name: str = "",
    last_name: str = "",
    nickname: str = "",
    year: str = "",
    max_results: int = 0,
) -> list[str]:
    """Generate usernames and return as list.

    Convenience wrapper for use from CLI and pipeline contexts.
    """
    return list(generate_usernames(
        first_name,
        last_name,
        nickname=nickname,
        year=year,
        max_results=max_results,
    ))


def handle_username(args: Any, _ctx: dict[str, Any]) -> Generator[str, None, None] | None:
    """CLI handler for the username subcommand."""
    first = getattr(args, "first", "") or ""
    last = getattr(args, "last", "") or ""
    nick = getattr(args, "nick", "") or ""
    year = getattr(args, "year", "") or ""
    limit = getattr(args, "limit", 0) or 0

    if not first and not last:
        logger.error("At least --first or --last is required.")
        return None

    return generate_usernames(first, last, nickname=nick, year=year, max_results=limit)

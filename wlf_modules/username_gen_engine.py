"""
username_gen_engine.py - Username/login generation from profile data.

Generates username candidates from first name, last name, email, and
domain combinations using 40+ common naming formats found in enterprise
and web environments. Useful for user enumeration, password spraying
target lists, and OSINT correlation.

Inspired by username-anarchy (urbanadventurer, 1,489 stars) with
additional corporate, regional (BR/LATAM), and web-era patterns.

Usage (as library):
    from wlf_modules.username_gen_engine import generate_usernames
    for u in generate_usernames("Juliana", "Oliveira", domain="corp.com"):
        print(u)

Usage (CLI):
    wlf.py username-gen --first Juliana --last Oliveira --domain corp.com

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Generator
from typing import Any

logger = logging.getLogger(__name__)

__info__ = {
    "name": "username_gen_engine",
    "version": "1.0.0",
    "author": "Andre Henrique (@mrhenrike)",
    "description": "Username generation from profile data (40+ formats)",
    "category": "enumeration",
    "tags": ["username", "enumeration", "profiling", "osint"],
}


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _sanitize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", _normalize(name))


def _email_local(email: str) -> str:
    if "@" in email:
        return email.split("@", 1)[0].lower()
    return ""


def _name_formats(first: str, last: str) -> list[str]:
    """Generate username formats from first and last name.

    Returns 40+ patterns commonly found in corporate and web environments.
    """
    f = _sanitize(first)
    ln = _sanitize(last)
    if not f or not ln:
        if f:
            return [f, f[:3], f[:4], f + "1", f + "123"]
        if ln:
            return [ln, ln[:3], ln[:4], ln + "1", ln + "123"]
        return []

    fi = f[0]
    li = ln[0]
    f3 = f[:3]
    l3 = ln[:3]

    patterns: list[str] = [
        f,
        ln,
        f + ln,
        ln + f,
        fi + ln,
        f + li,
        fi + "." + ln,
        f + "." + ln,
        f + "." + li,
        ln + "." + f,
        ln + "." + fi,
        fi + ln,
        li + f,
        f + "_" + ln,
        ln + "_" + f,
        fi + "_" + ln,
        f + "-" + ln,
        ln + "-" + f,
        fi + "-" + ln,
        f3 + l3,
        l3 + f3,
        f3 + ln,
        l3 + f,
        fi + li,
        f + ln[0:2],
        ln + f[0:2],
        fi + ln + "1",
        f + ln + "1",
        f + "." + ln + "1",
        f[0:2] + ln,
        f + ln[:4],
        ln + f[:4],
        fi + l3,
        li + f3,
        f3 + "." + l3,
        f + ln + "01",
        fi + ln + "01",
        f + "1",
        ln + "1",
        f + "123",
        ln + "123",
    ]
    return patterns


def _domain_formats(base_patterns: list[str], domain: str) -> list[str]:
    """Generate email-style usernames with domain."""
    if not domain:
        return []
    results: list[str] = []
    for pat in base_patterns[:20]:
        results.append(pat + "@" + domain)
    return results


def _numbered_variants(base_patterns: list[str], max_num: int = 3) -> list[str]:
    """Add numeric suffixes to patterns."""
    results: list[str] = []
    for pat in base_patterns[:15]:
        for n in range(1, max_num + 1):
            results.append(pat + str(n))
        results.append(pat + "01")
        results.append(pat + "99")
    return results


def generate_usernames(
    first_name: str = "",
    last_name: str = "",
    *,
    email: str = "",
    domain: str = "",
    nicknames: list[str] | None = None,
    max_candidates: int = 0,
) -> Generator[str, None, None]:
    """Generate username candidates from profile data.

    Args:
        first_name: Target's first name.
        last_name: Target's last name.
        email: Known email address (local part extracted).
        domain: Corporate/email domain for email-format usernames.
        nicknames: Additional known usernames/handles.
        max_candidates: Limit output (0 = unlimited).

    Yields:
        Unique username candidate strings.
    """
    seen: set[str] = set()
    emitted = 0

    def _emit(candidate: str) -> bool:
        nonlocal emitted
        c = candidate.strip().lower()
        if not c or len(c) < 2 or c in seen:
            return False
        seen.add(c)
        emitted += 1
        return True

    base = _name_formats(first_name, last_name)

    for pat in base:
        if _emit(pat):
            yield pat
            if max_candidates and emitted >= max_candidates:
                return

    local = _email_local(email)
    if local:
        if _emit(local):
            yield local
            if max_candidates and emitted >= max_candidates:
                return

    if nicknames:
        for nick in nicknames:
            n = _sanitize(nick)
            if _emit(n):
                yield n
                if max_candidates and emitted >= max_candidates:
                    return

    for variant in _numbered_variants(base):
        if _emit(variant):
            yield variant
            if max_candidates and emitted >= max_candidates:
                return

    for email_fmt in _domain_formats(base, domain):
        if _emit(email_fmt):
            yield email_fmt
            if max_candidates and emitted >= max_candidates:
                return


def run(
    first_name: str = "",
    last_name: str = "",
    email: str = "",
    domain: str = "",
    nicknames: list[str] | None = None,
    max_candidates: int = 0,
) -> list[str]:
    """Generate usernames and return as list."""
    return list(generate_usernames(
        first_name,
        last_name,
        email=email,
        domain=domain,
        nicknames=nicknames,
        max_candidates=max_candidates,
    ))


def handle_username_gen(
    args: Any, _ctx: dict[str, Any],
) -> Generator[str, None, None] | None:
    """CLI handler for the username-gen subcommand."""
    first = getattr(args, "first", "") or ""
    last = getattr(args, "last", "") or ""
    email = getattr(args, "email", "") or ""
    domain = getattr(args, "domain", "") or ""
    nicknames_raw = getattr(args, "nicknames", None)
    limit = getattr(args, "limit", 0) or 0

    nicks = nicknames_raw.split(",") if nicknames_raw else None

    if not first and not last and not email:
        logger.error("Provide at least --first, --last, or --email.")
        return None

    return generate_usernames(
        first, last, email=email, domain=domain,
        nicknames=nicks, max_candidates=limit,
    )

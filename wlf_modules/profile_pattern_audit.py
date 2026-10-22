"""Read-only, offline profile-pattern risk auditing for password policy tests.

This module DOES NOT produce password guesses, wordlists or credentials. It accepts
an existing password under evaluation and returns rule identifiers only.
Sensitive input is not logged or included in the return payload.

Autor: Andre Henrique (@mrhenrike) | Uniao Geek
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

__info__: dict[str, Any] = {
    "name": "profile_pattern_audit",
    "version": "1.0.0",
    "category": "audit",
    "description": "Identifies structural weaknesses in passwords using profile context",
    "author": "Andre Henrique (@mrhenrike)",
}


def _fold(value: str) -> str:
    """Unicode-safe approximate textual matching; never strip digits."""
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(c)
    ).casefold()


def _word(value: Any) -> str:
    return _fold(str(value or "").strip())


def _digits(value: Any) -> str:
    return "".join(c for c in str(value or "") if "0" <= c <= "9")


def _tokens(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        vals = [value]
    elif isinstance(value, (list, tuple)):
        vals = [str(v) for v in value]
    else:
        vals = []
    return tuple(dict.fromkeys(s for v in vals for s in [_word(v)] if s))


@dataclass(frozen=True)
class ProfileContext:
    first_names: tuple[str, ...] = ()
    last_names: tuple[str, ...] = ()
    names: tuple[str, ...] = ()
    spouse_names: tuple[str, ...] = ()
    nicknames: tuple[str, ...] = ()
    company_names: tuple[str, ...] = ()
    phones: tuple[str, ...] = ()
    birth_year: int | None = None
    reference_year: int = field(default_factory=lambda: date.today().year)
    recent_year_count: int = 5

    @classmethod
    def from_mapping(
        cls, raw: Mapping[str, Any], *, reference_year: int | None = None
    ) -> ProfileContext:
        full = _word(raw.get("full_name", ""))
        parts = [x for x in re.split(r"\s+", full) if x]
        first = _tokens(raw.get("firstname") or raw.get("first_name"))
        last = _tokens(
            raw.get("lastname") or raw.get("last_name") or raw.get("surname")
        )
        if parts and not first:
            first = (parts[0],)
        if len(parts) > 1 and not last:
            last = (parts[-1],)
        names = tuple(
            dict.fromkeys(
                (
                    *_tokens(raw.get("name")),
                    *first,
                    *last,
                    *_tokens(raw.get("short_name")),
                )
            )
        )
        source_phone = raw.get("phones", ()) or (
            () if not raw.get("phone") else (raw.get("phone"),)
        )
        if isinstance(source_phone, str):
            source_phone = (source_phone,)
        phones = tuple(
            dict.fromkeys(p for v in source_phone for p in [_digits(v)] if p)
        )
        by = raw.get("birth_year")
        birth_year = int(by) if by not in (None, "", 0) else None
        yr = reference_year if reference_year is not None else date.today().year
        if yr < 1900 or yr > 9999:
            raise ValueError("reference_year outside supported range")
        if birth_year is not None and not (1900 <= birth_year <= yr):
            raise ValueError("birth_year outside supported range")
        count = int(raw.get("recent_year_count", 5))
        if not 1 <= count <= 100:
            raise ValueError("recent_year_count must be 1..100")
        return cls(
            first_names=first,
            last_names=last,
            names=names,
            spouse_names=_tokens(
                raw.get("spouse_name")
                or raw.get("partner_name")
                or raw.get("namedoconjuge")
            ),
            nicknames=_tokens(raw.get("nicknames")),
            company_names=_tokens(
                raw.get("company_name") or raw.get("company_names")
            ),
            phones=phones,
            birth_year=birth_year,
            reference_year=yr,
            recent_year_count=count,
        )

    @property
    def years(self) -> tuple[str, ...]:
        nums = list(
            range(
                self.reference_year - self.recent_year_count + 1,
                self.reference_year + 1,
            )
        )
        if self.birth_year is not None:
            nums.append(self.birth_year)
        return tuple(dict.fromkeys(s for n in nums for s in (str(n), str(n)[-2:])))


def audit_password(password: str, context: ProfileContext) -> dict[str, Any]:
    """Identify structural weaknesses in an already-known test password.

    No candidate enumeration, authentication attempt, password echo, or log.
    Pattern identifiers are suitable for a defensive report or policy check.
    """
    p = _fold(password)
    matched: set[str] = set()
    years = set(context.years)
    names = set(context.names)
    firsts = set(context.first_names)
    lasts = set(context.last_names)
    spouse = set(context.spouse_names)
    phones = set(context.phones)

    for n in names:
        if n and (
            re.fullmatch(re.escape(n) + r"[0-9]{2,6}", p)
            or re.fullmatch(r"[0-9]{2,6}" + re.escape(n), p)
        ):
            matched.add("NAME_NUMERIC_AFFIX_2_TO_6")
        for s in spouse:
            if s and p in (n + s, s + n):
                matched.add("NAME_SPOUSE_COMBINATION")
        for phone in phones:
            if p in (n + phone, phone + n):
                matched.add("NAME_EXPLICIT_PHONE_COMBINATION")
        for y in years:
            if p in (n + y, y + n):
                matched.add("NAME_YEAR_COMBINATION")
            if p in (n + "@" + y, n + "#" + y, n + "_" + y, n + "-" + y):
                matched.add("NAME_SEPARATOR_YEAR")

    for first in firsts:
        for last in lasts:
            if p in (first + last, last + first):
                matched.add("FIRST_LAST_COMBINATION")
            for year in years:
                if p in (first + year + last, last + year + first):
                    matched.add("FIRST_YEAR_LAST_COMBINATION")
            for phone in phones:
                if p in (first + phone + last, last + phone + first):
                    matched.add("FIRST_EXPLICIT_PHONE_LAST_COMBINATION")
            for width in (2, 4, 6):
                pattern1 = (
                    re.escape(first) + rf"[0-9]{{{width}}}" + re.escape(last)
                )
                pattern2 = (
                    re.escape(last) + rf"[0-9]{{{width}}}" + re.escape(first)
                )
                if re.fullmatch(pattern1, p) or re.fullmatch(pattern2, p):
                    matched.add("FIRST_DIGITS_2_4_6_LAST_COMBINATION")

    for company in context.company_names:
        for year in years:
            if p in (company + year, year + company):
                matched.add("COMPANY_YEAR_COMBINATION")

    for nick in context.nicknames:
        for year in years:
            if p in (nick + year, year + nick):
                matched.add("NICKNAME_YEAR_COMBINATION")

    return {
        "risk_indicators": sorted(matched),
        "indicator_count": len(matched),
        "contains_profile_pattern": bool(matched),
    }


def run(
    password: str = "",
    profile: dict[str, Any] | None = None,
    reference_year: int | None = None,
) -> list[str]:
    """WLF module contract: run audit on a password against a profile context."""
    if not password:
        return []
    ctx = ProfileContext.from_mapping(
        profile or {}, reference_year=reference_year
    )
    result = audit_password(password, ctx)
    indicators: list[str] = result["risk_indicators"]
    return indicators

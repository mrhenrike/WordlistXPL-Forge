"""corp_convention.py - Corporate password convention engine.

Generates passwords that follow common corporate naming conventions
observed in enterprise environments.  These patterns emerge from
password policies that require complexity but allow predictable
structures.

Patterns:
  - verb + separator + corpname + digits  (Change@Corp2024)
  - season + year + symbol                (Summer2024!)
  - dept + project + digits               (ITProject123)
  - corpname + separator + year + symbol  (Acme@2024!)
  - month + year + corpname               (Oct2024Acme)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import itertools
import logging
from collections.abc import Generator
from typing import Any

logger = logging.getLogger(__name__)

# ── Corporate vocabulary ────────────────────────────────────────────────────

VERBS = [
    "Change", "Welcome", "Reset", "Access", "Login", "Enter",
    "Start", "Open", "Update", "Connect", "Admin", "Setup",
    "Manage", "Secure", "Launch", "Deploy", "Build", "Create",
]

SEASONS = ["Spring", "Summer", "Fall", "Autumn", "Winter"]

MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    "January", "February", "March", "April",
    "June", "July", "August", "September",
    "October", "November", "December",
]

DEPARTMENTS = [
    "IT", "HR", "Dev", "Ops", "QA", "Sec", "Fin", "Eng",
    "Sales", "Mkt", "Legal", "Admin", "Infra", "Data",
    "DevOps", "NetOps", "SecOps", "SysAdmin", "HelpDesk",
]

PROJECTS = [
    "Project", "System", "Portal", "Platform", "Server",
    "Network", "Cloud", "Database", "Service", "App",
    "Intranet", "Gateway", "Firewall", "Backup", "Monitor",
]

SEPARATORS = ["@", "#", "!", "$", "_", "-", ".", "+", "&"]

SYMBOLS = ["!", "@", "#", "$", "%", "&", "*", ".", "?"]

DEFAULT_YEARS = ["2023", "2024", "2025", "2026"]

DIGIT_SUFFIXES = [
    "1", "12", "123", "1234", "01", "001",
    "00", "99", "007", "321", "101", "42",
]


# ── Pattern generators ──────────────────────────────────────────────────────

def _verb_sep_corp_digits(
    corp_names: list[str],
    years: list[str],
) -> Generator[str, None, None]:
    """Pattern: Verb + Separator + CorpName + Digits/Year."""
    for verb, sep, corp in itertools.product(VERBS[:10], SEPARATORS[:5], corp_names):
        for yr in years:
            yield f"{verb}{sep}{corp}{yr}"
            yield f"{verb}{sep}{corp}{yr}!"
        for d in DIGIT_SUFFIXES[:6]:
            yield f"{verb}{sep}{corp}{d}"


def _season_year_symbol(
    corp_names: list[str],
    years: list[str],
) -> Generator[str, None, None]:
    """Pattern: Season + Year + Symbol (optionally with corp)."""
    for season, yr in itertools.product(SEASONS, years):
        for sym in SYMBOLS[:5]:
            yield f"{season}{yr}{sym}"
            yield f"{season}{yr}"
            for corp in corp_names[:3]:
                yield f"{season}{yr}{sym}{corp}"
                yield f"{corp}{season}{yr}{sym}"


def _dept_project_digits(
    corp_names: list[str],
    years: list[str],
) -> Generator[str, None, None]:
    """Pattern: Department + Project + Digits."""
    for dept, proj in itertools.product(DEPARTMENTS[:12], PROJECTS[:8]):
        for d in DIGIT_SUFFIXES[:4]:
            yield f"{dept}{proj}{d}"
        for yr in years[:2]:
            yield f"{dept}{proj}{yr}"
    for dept, corp in itertools.product(DEPARTMENTS[:8], corp_names):
        for d in DIGIT_SUFFIXES[:4]:
            yield f"{dept}{corp}{d}"


def _corp_sep_year_symbol(
    corp_names: list[str],
    years: list[str],
) -> Generator[str, None, None]:
    """Pattern: CorpName + Separator + Year + Symbol."""
    for corp, sep, yr in itertools.product(corp_names, SEPARATORS[:5], years):
        for sym in SYMBOLS[:5]:
            yield f"{corp}{sep}{yr}{sym}"
            yield f"{corp}{yr}{sym}"
        yield f"{corp}{sep}{yr}"
        yield f"{corp}{yr}"


def _month_year_corp(
    corp_names: list[str],
    years: list[str],
) -> Generator[str, None, None]:
    """Pattern: Month + Year + CorpName."""
    for month, yr in itertools.product(MONTHS[:12], years):
        yield f"{month}{yr}"
        yield f"{month}{yr}!"
        for corp in corp_names[:3]:
            yield f"{month}{yr}{corp}"
            yield f"{corp}{month}{yr}"


_PATTERN_MAP: dict[str, Any] = {
    "verb_sep_corp": _verb_sep_corp_digits,
    "season_year": _season_year_symbol,
    "dept_project": _dept_project_digits,
    "corp_year": _corp_sep_year_symbol,
    "month_year": _month_year_corp,
}

PATTERNS = tuple(_PATTERN_MAP.keys())


# ── Engine ──────────────────────────────────────────────────────────────────

class CorpConventionEngine:
    """Corporate password convention generation engine."""

    def __init__(
        self,
        corp_names: list[str],
        years: list[str] | None = None,
        patterns: list[str] | None = None,
    ) -> None:
        self.corp_names = corp_names if corp_names else ["Corp"]
        self.years = years if years else list(DEFAULT_YEARS)
        requested = patterns if patterns else list(PATTERNS)
        self.patterns: list[str] = [p for p in requested if p in _PATTERN_MAP]
        if not self.patterns:
            self.patterns = list(PATTERNS)

    def generate(
        self,
        limit: int = 0,
        min_len: int = 6,
        max_len: int = 32,
    ) -> Generator[str, None, None]:
        """Yield corporate convention password candidates."""
        seen: set[str] = set()
        count = 0
        for pattern_name in self.patterns:
            fn = _PATTERN_MAP[pattern_name]
            for candidate in fn(self.corp_names, self.years):
                if len(candidate) < min_len or len(candidate) > max_len:
                    continue
                if candidate in seen:
                    continue
                seen.add(candidate)
                yield candidate
                count += 1
                if 0 < limit <= count:
                    return


# ── CLI handler ─────────────────────────────────────────────────────────────

def handle_corp_conv(
    args: Any, ctx: dict[str, Any]
) -> Generator[str, None, None] | None:
    """CLI handler for corporate convention generation."""
    corp_names_raw = getattr(args, "corp_names", None)
    years_raw = getattr(args, "years", None)
    patterns_raw = getattr(args, "patterns", None)
    limit = getattr(args, "limit", 0) or 0

    if not corp_names_raw:
        logger.warning("No company names provided. Use --corp-names.")
        return None

    corp_names = [n.strip() for n in corp_names_raw if n.strip()]
    years = [y.strip() for y in years_raw] if years_raw else None
    patterns = [p.strip() for p in patterns_raw] if patterns_raw else None

    engine = CorpConventionEngine(
        corp_names=corp_names,
        years=years,
        patterns=patterns,
    )

    return engine.generate(
        limit=limit,
        min_len=ctx.get("min_len", 6) or 6,
        max_len=ctx.get("max_len", 32) or 32,
    )

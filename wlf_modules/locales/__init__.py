"""locales - Regional and cultural password generation engines.

Each locale module provides names, slang, holidays, institutions and
cultural patterns specific to a country or language region.  All engines
share the same ABC so the CLI can dispatch by locale code.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import abc
import logging
from typing import Generator, Optional, Any

logger = logging.getLogger(__name__)

__all__ = [
    "BaseLocaleEngine",
    "get_engine",
    "list_locales",
    "LOCALE_REGISTRY",
]


class BaseLocaleEngine(abc.ABC):
    """Abstract base for locale-specific password generation."""

    locale_code: str = ""
    locale_name: str = ""

    def __init__(
        self,
        profile: Optional[dict[str, Any]] = None,
        max_candidates: int = 0,
    ) -> None:
        self.profile = profile or {}
        self.max_candidates = max_candidates

    @abc.abstractmethod
    def generate(self) -> Generator[tuple[str, float], None, None]:
        """Yield (candidate, score) tuples."""

    def _emit_block(
        self,
        bases: list[str],
        years: list[str],
        suffixes: list[str],
        separators: list[str],
        score: float,
        seen: set[str],
        count: list[int],
    ) -> Generator[tuple[str, float], None, None]:
        """Helper: expand bases x years/suffixes, dedup and yield."""
        for base in bases:
            if not base or base in seen:
                continue
            seen.add(base)
            count[0] += 1
            if self.max_candidates and count[0] > self.max_candidates:
                return
            yield (base, score)
            for yr in years:
                for sep in separators:
                    cand = f"{base}{sep}{yr}"
                    if cand not in seen:
                        seen.add(cand)
                        count[0] += 1
                        if self.max_candidates and count[0] > self.max_candidates:
                            return
                        yield (cand, score * 0.9)
            for sfx in suffixes:
                cand = f"{base}{sfx}"
                if cand not in seen:
                    seen.add(cand)
                    count[0] += 1
                    if self.max_candidates and count[0] > self.max_candidates:
                        return
                    yield (cand, score * 0.85)


LOCALE_REGISTRY: dict[str, type[BaseLocaleEngine]] = {}


def register_engine(cls: type[BaseLocaleEngine]) -> type[BaseLocaleEngine]:
    """Class decorator to register a locale engine."""
    code = cls.locale_code.lower()
    if code:
        LOCALE_REGISTRY[code] = cls
        aliases = getattr(cls, "locale_aliases", [])
        for alias in aliases:
            LOCALE_REGISTRY[alias.lower()] = cls
    return cls


def get_engine(
    locale_code: str,
    profile: Optional[dict[str, Any]] = None,
    max_candidates: int = 0,
) -> Optional[BaseLocaleEngine]:
    """Instantiate a locale engine by code."""
    cls = LOCALE_REGISTRY.get(locale_code.lower().strip())
    if cls is None:
        logger.warning("Locale '%s' not found. Available: %s", locale_code, list_locales())
        return None
    return cls(profile=profile, max_candidates=max_candidates)


def list_locales() -> list[str]:
    """Return registered primary locale codes."""
    seen: set[str] = set()
    result: list[str] = []
    for code, cls in LOCALE_REGISTRY.items():
        primary = cls.locale_code.lower()
        if primary not in seen:
            seen.add(primary)
            result.append(primary)
    return sorted(result)


def _autoload() -> None:
    """Import all locale modules so they self-register."""
    import importlib
    for mod_name in ("en_us", "en_gb", "es", "fr", "de", "pt_pt", "pt_br", "ja", "zh", "ar", "hi", "ko"):
        try:
            importlib.import_module(f"wlf_modules.locales.{mod_name}")
        except ImportError:
            pass


_autoload()

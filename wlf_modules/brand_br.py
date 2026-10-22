"""brand_br.py - Brazilian brand-based password candidate generator.

PII analysis of 1.6M passwords from 51 leaked databases found 43,599
matches for brand patterns.  This module generates candidates derived
from popular Brazilian brand names across banking, telecom, e-commerce,
tech, delivery, streaming, social media, transport, government and
football categories.

Each brand is expanded with casing variants, numeric suffixes, special
characters, leet substitutions and (for football clubs) fan-culture
patterns, producing a realistic candidate set aligned with real leak
distributions.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
"""
from __future__ import annotations

import logging
from collections.abc import Generator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category constants
# ---------------------------------------------------------------------------

_DIGITAL_BANKS: list[str] = [
    "nubank", "itau", "bradesco", "santander", "caixa", "bb", "inter",
    "c6bank", "picpay", "neon", "original", "safra", "modal", "btg",
    "xp", "rico", "clear", "pagbank", "mercadopago", "ame", "stone",
    "pagseguro", "will", "next", "pan", "bmg", "agibank", "daycoval",
    "pine", "banrisul", "sicredi", "sicoob", "unicred",
]

_TELECOM: list[str] = [
    "vivo", "claro", "tim", "oi", "nextel", "algar", "sercomtel",
    "brisanet", "desktop", "americanet",
]

_ECOMMERCE: list[str] = [
    "mercadolivre", "amazon", "shopee", "magalu", "americanas",
    "casasbahia", "pontofrio", "submarino", "netshoes", "centauro",
    "dafiti", "shein", "aliexpress", "kabum", "pichau", "terabyte",
]

_TECH_BRANDS: list[str] = [
    "samsung", "apple", "motorola", "xiaomi", "lg", "positivo",
    "multilaser", "intelbras", "elsys", "aoc", "philco", "consul",
    "brastemp", "electrolux",
]

_FOOD_DELIVERY: list[str] = [
    "ifood", "rappi", "ubereats", "zedodelivery", "aiqfome",
]

_STREAMING: list[str] = [
    "netflix", "spotify", "globoplay", "hbomax", "disneyplus",
    "amazonprime", "paramount", "deezer", "tidal", "crunchyroll", "star",
]

_SOCIAL_BR: list[str] = [
    "instagram", "facebook", "twitter", "tiktok", "whatsapp", "telegram",
    "discord", "kwai", "youtube", "twitch",
]

_TRANSPORT: list[str] = [
    "uber", "nineninety", "cabify", "blablacar", "clickbus", "buser",
]

_GOV_SERVICES: list[str] = [
    "govbr", "meugov", "cnh", "detran", "poupatempo", "sus", "inss",
    "fgts", "caixa", "receita", "cpf", "cnpj", "irpf",
]

_FOOTBALL_CLUBS: list[str] = [
    "flamengo", "palmeiras", "corinthians", "saopaulo", "santos",
    "gremio", "internacional", "cruzeiro", "atleticomg", "vasco",
    "fluminense", "botafogo", "bahia", "sport", "fortaleza", "ceara",
    "coritiba", "athleticopr", "goias", "cuiaba", "bragantino",
    "america", "chapecoense", "avai", "juventude", "nautico", "santa",
    "guarani", "ponte", "operario", "londrina", "criciuma",
]

# Mapping from user-facing category name to internal list
_CATEGORY_MAP: dict[str, list[str]] = {
    "digital_banks": _DIGITAL_BANKS,
    "telecom": _TELECOM,
    "ecommerce": _ECOMMERCE,
    "tech_brands": _TECH_BRANDS,
    "food_delivery": _FOOD_DELIVERY,
    "streaming": _STREAMING,
    "social_br": _SOCIAL_BR,
    "transport": _TRANSPORT,
    "gov_services": _GOV_SERVICES,
    "football_clubs": _FOOTBALL_CLUBS,
}

# Common numeric suffixes found in leaked passwords
_NUMERIC_SUFFIXES: list[str] = [
    "1", "12", "123", "1234", "01", "007", "2024", "2025", "2026",
]

# Common trailing special characters
_SPECIAL_CHARS: list[str] = ["!", "@", "#", "*", "."]

# Year suffixes
_YEAR_SUFFIXES: list[str] = [
    "2020", "2021", "2022", "2023", "2024", "2025", "2026",
]

# Leet substitution table
_LEET_MAP: dict[str, str] = {
    "a": "4",
    "e": "3",
    "i": "1",
    "o": "0",
    "s": "5",
}

# Fan-culture patterns for football clubs (placeholder {} = club name)
_FAN_PATTERNS: list[str] = [
    "meu{brand}",
    "{brand}ate_morrer",
    "eu_amo_{brand}",
    "vai{brand}",
    "{brand}campeao",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_brands(categories: list[str] | None = None) -> list[str]:
    """Return brand strings for the requested categories (or all).

    Parameters
    ----------
    categories:
        Category names matching keys in ``_CATEGORY_MAP``.  ``None`` or
        an empty list returns every brand across all categories.

    Returns
    -------
    list[str]
        Deduplicated list of brand strings, preserving insertion order.
    """
    if not categories:
        selected: list[str] = []
        for brands in _CATEGORY_MAP.values():
            selected.extend(brands)
        # Deduplicate while preserving order
        return list(dict.fromkeys(selected))

    selected = []
    for cat in categories:
        cat_lower = cat.lower().strip()
        if cat_lower in _CATEGORY_MAP:
            selected.extend(_CATEGORY_MAP[cat_lower])
        else:
            logger.warning("Unknown brand category: %s", cat)
    return list(dict.fromkeys(selected))


def _apply_leet(word: str) -> str:
    """Apply basic leet substitutions to a word."""
    result: list[str] = []
    for ch in word:
        result.append(_LEET_MAP.get(ch, ch))
    return "".join(result)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_brand_br(
    categories: list[str] | None = None,
    with_numbers: bool = True,
    with_leet: bool = True,
    with_year: bool = True,
    max_results: int = 0,
) -> Generator[str, None, None]:
    """Yield password candidates based on Brazilian brand names.

    Parameters
    ----------
    categories:
        Restrict to specific brand categories.  ``None`` uses all.
    with_numbers:
        Append common numeric suffixes to each brand.
    with_leet:
        Emit leet-speak variants (a->4, e->3, i->1, o->0, s->5).
    with_year:
        Append year suffixes (2020 through 2026).
    max_results:
        Cap the total number of candidates.  ``0`` means unlimited.

    Yields
    ------
    str
        Password candidate strings, one at a time.
    """
    brands = get_brands(categories)
    count = 0
    seen: set[str] = set()
    _football_set = set(_FOOTBALL_CLUBS)

    def _collect(candidate: str) -> str | None:
        """Deduplicate and enforce the result cap.

        Returns the candidate when it should be yielded, ``None`` when
        it is a duplicate.  Raises ``_LimitReached`` when the cap is hit.
        """
        nonlocal count
        if candidate in seen:
            return None
        seen.add(candidate)
        count += 1
        return candidate

    def _at_limit() -> bool:
        return max_results > 0 and count >= max_results

    for brand in brands:
        # ── Base casing variants ──────────────────────────────────────
        for variant in (brand, brand.capitalize(), brand.upper()):
            out = _collect(variant)
            if out is not None:
                yield out
                if _at_limit():
                    return

        # ── Numeric suffixes ──────────────────────────────────────────
        if with_numbers:
            for suffix in _NUMERIC_SUFFIXES:
                for base in (brand, brand.capitalize()):
                    out = _collect(f"{base}{suffix}")
                    if out is not None:
                        yield out
                        if _at_limit():
                            return

        # ── Special character suffixes ────────────────────────────────
        for char in _SPECIAL_CHARS:
            for base in (brand, brand.capitalize()):
                out = _collect(f"{base}{char}")
                if out is not None:
                    yield out
                    if _at_limit():
                        return

        # ── Leet variants ─────────────────────────────────────────────
        if with_leet:
            leet_form = _apply_leet(brand)
            if leet_form != brand:
                for variant in (leet_form, leet_form.capitalize(), leet_form.upper()):
                    out = _collect(variant)
                    if out is not None:
                        yield out
                        if _at_limit():
                            return

                # Leet + numeric
                if with_numbers:
                    for suffix in _NUMERIC_SUFFIXES:
                        out = _collect(f"{leet_form}{suffix}")
                        if out is not None:
                            yield out
                            if _at_limit():
                                return

        # ── Year suffixes ─────────────────────────────────────────────
        if with_year:
            for year in _YEAR_SUFFIXES:
                for base in (brand, brand.capitalize()):
                    out = _collect(f"{base}{year}")
                    if out is not None:
                        yield out
                        if _at_limit():
                            return

        # ── Football fan patterns ─────────────────────────────────────
        if brand in _football_set:
            for pattern in _FAN_PATTERNS:
                candidate = pattern.format(brand=brand)
                out = _collect(candidate)
                if out is not None:
                    yield out
                    if _at_limit():
                        return

                cap_candidate = candidate.capitalize()
                out = _collect(cap_candidate)
                if out is not None:
                    yield out
                    if _at_limit():
                        return


def available_categories() -> list[str]:
    """Return sorted list of available category names."""
    return sorted(_CATEGORY_MAP.keys())

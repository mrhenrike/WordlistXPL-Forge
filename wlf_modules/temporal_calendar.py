"""temporal_calendar.py - Multi-cultural calendar data for temporal password generation.

Provides holidays, seasons, months, weekdays and date-based password patterns
for multiple locales.  Consumed by temporal_drift.py and the pipeline to
generate culturally-aware temporal password candidates.

Supported locales: pt-BR, en-US, en-GB, es, fr, de, pt-PT

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

from collections.abc import Generator

# ── Holidays by locale ───────────────────────────────────────────────────────

HOLIDAYS: dict[str, list[str]] = {
    "pt-BR": [
        "natal", "anonovo", "carnaval", "pascoa", "tiradentes",
        "diadotrabalho", "independencia", "finados", "proclamacao",
        "saojoao", "festajunina", "corpus", "padroeira", "reveillon",
        "feriado", "copabrasil", "copa", "brasileirao",
    ],
    "en-US": [
        "christmas", "newyear", "thanksgiving", "halloween", "easter",
        "4thjuly", "july4th", "independence", "memorial", "labor",
        "veterans", "superbowl", "valentines", "stpatricks", "mlkday",
        "blackfriday", "cybermonday", "summer", "spring", "winter",
    ],
    "en-GB": [
        "christmas", "newyear", "easter", "bankholiday", "guyfawkes",
        "bonfire", "boxingday", "remembrance", "queens", "kings",
        "pancakeday", "mothersday", "fathersday", "hogmanay",
    ],
    "es": [
        "navidad", "anonuevo", "reyes", "semanasanta", "pascua",
        "diademuertos", "todossantos", "hispanidad", "constitucion",
        "feria", "sanfermin", "tomatina", "nochevieja", "nochebuena",
        "independencia", "madre", "padre",
    ],
    "fr": [
        "noel", "nouvelAN", "paques", "14juillet", "bastille",
        "toussaint", "ascension", "armistice", "pentecote",
        "fetedelamusique", "chandeleur", "poissondavril",
        "fetedutravail", "fetedesmeres", "fetedesperes",
    ],
    "de": [
        "weihnachten", "neujahr", "ostern", "silvester", "karneval",
        "fasching", "oktoberfest", "tagdereinheit", "pfingsten",
        "fronleichnam", "himmelfahrt", "muttertag", "vatertag",
        "nikolaus", "adventcal", "rosenmontag",
    ],
    "pt-PT": [
        "natal", "anonovo", "pascoa", "25abril", "liberdade",
        "10junho", "diadeportugal", "assuncao", "republica",
        "todossantos", "imaculada", "carnaval", "santospopulares",
        "saojoao", "santoantonio",
    ],
}


# ── Seasons by locale ────────────────────────────────────────────────────────

SEASONS: dict[str, list[str]] = {
    "pt-BR": ["verao", "outono", "inverno", "primavera"],
    "en-US": ["summer", "fall", "winter", "spring"],
    "en-GB": ["summer", "autumn", "winter", "spring"],
    "es": ["verano", "otono", "invierno", "primavera"],
    "fr": ["ete", "automne", "hiver", "printemps"],
    "de": ["sommer", "herbst", "winter", "fruehling"],
    "pt-PT": ["verao", "outono", "inverno", "primavera"],
}


# ── Months by locale ─────────────────────────────────────────────────────────

MONTHS: dict[str, list[str]] = {
    "pt-BR": [
        "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        "jan", "fev", "mar", "abr", "mai", "jun",
        "jul", "ago", "set", "out", "nov", "dez",
    ],
    "en-US": [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec",
    ],
    "es": [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        "ene", "feb", "mar", "abr", "may", "jun",
        "jul", "ago", "sep", "oct", "nov", "dic",
    ],
    "fr": [
        "janvier", "fevrier", "mars", "avril", "mai", "juin",
        "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
        "jan", "fev", "mar", "avr", "mai", "jun",
        "jul", "aou", "sep", "oct", "nov", "dec",
    ],
    "de": [
        "januar", "februar", "maerz", "april", "mai", "juni",
        "juli", "august", "september", "oktober", "november", "dezember",
        "jan", "feb", "marz", "apr", "mai", "jun",
        "jul", "aug", "sep", "okt", "nov", "dez",
    ],
}


# ── Weekdays ─────────────────────────────────────────────────────────────────

WEEKDAYS: dict[str, list[str]] = {
    "pt-BR": ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo",
              "seg", "ter", "qua", "qui", "sex", "sab", "dom"],
    "en-US": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
              "mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    "es": ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo",
           "lun", "mar", "mie", "jue", "vie", "sab", "dom"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche",
           "lun", "mar", "mer", "jeu", "ven", "sam", "dim"],
    "de": ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag",
           "mo", "di", "mi", "do", "fr", "sa", "so"],
}


# ── Separators and suffixes ──────────────────────────────────────────────────

SEPARATORS: list[str] = ["", "@", "#", "!", "_", ".", "-"]

YEAR_SUFFIXES: list[str] = [
    "2024", "2025", "2026", "24", "25", "26",
    "2023", "23", "2022", "22",
]

DIGIT_SUFFIXES: list[str] = [
    "1", "12", "123", "1234", "!", "!!", "#", "01", "007",
    "69", "666", "99", "00", "321",
]


# ── Generator ────────────────────────────────────────────────────────────────

def _case_variants(word: str) -> list[str]:
    """Common casing patterns for a word."""
    return list({
        word.lower(),
        word.upper(),
        word.capitalize(),
    })


def generate_temporal_candidates(
    locales: list[str] | None = None,
    max_candidates: int = 50_000,
    min_len: int = 4,
    max_len: int = 32,
    include_holidays: bool = True,
    include_seasons: bool = True,
    include_months: bool = True,
    include_weekdays: bool = False,
) -> Generator[str, None, None]:
    """Generate temporal password candidates from calendar data.

    Combines locale-specific temporal tokens with years, digits and
    separator patterns to produce culturally-aware password candidates.
    """
    if locales is None:
        locales = ["pt-BR", "en-US"]

    tokens: list[str] = []
    for loc in locales:
        if include_holidays:
            tokens.extend(HOLIDAYS.get(loc, []))
        if include_seasons:
            tokens.extend(SEASONS.get(loc, []))
        if include_months:
            tokens.extend(MONTHS.get(loc, []))
        if include_weekdays:
            tokens.extend(WEEKDAYS.get(loc, []))

    tokens = list(dict.fromkeys(tokens))

    seen: set[str] = set()
    count = 0

    def _emit(candidate: str) -> bool:
        nonlocal count
        if min_len <= len(candidate) <= max_len and candidate not in seen:
            seen.add(candidate)
            return True
        return False

    for token in tokens:
        for variant in _case_variants(token):
            for suffix in YEAR_SUFFIXES:
                for sep in SEPARATORS[:3]:
                    candidate = variant + sep + suffix
                    if _emit(candidate):
                        yield candidate
                        count += 1
                        if count >= max_candidates:
                            return

            for suffix in DIGIT_SUFFIXES:
                candidate = variant + suffix
                if _emit(candidate):
                    yield candidate
                    count += 1
                    if count >= max_candidates:
                        return

            if _emit(variant):
                yield variant
                count += 1
                if count >= max_candidates:
                    return

    for token in tokens:
        for variant in _case_variants(token):
            for year in YEAR_SUFFIXES[:4]:
                for sep in SEPARATORS[:4]:
                    for dsuf in DIGIT_SUFFIXES[:5]:
                        candidate = variant + sep + year + dsuf
                        if _emit(candidate):
                            yield candidate
                            count += 1
                            if count >= max_candidates:
                                return


def get_locale_tokens(locale: str) -> dict[str, list[str]]:
    """Return all temporal tokens for a locale."""
    return {
        "holidays": HOLIDAYS.get(locale, []),
        "seasons": SEASONS.get(locale, []),
        "months": MONTHS.get(locale, []),
        "weekdays": WEEKDAYS.get(locale, []),
    }


def available_locales() -> list[str]:
    """Return sorted list of available locales."""
    return sorted(set(HOLIDAYS.keys()) | set(SEASONS.keys()))

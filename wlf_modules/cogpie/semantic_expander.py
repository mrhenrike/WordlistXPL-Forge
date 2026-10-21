"""
semantic_expander.py - Layer 1: Semantic expansion of personal tokens.

Transforms raw profile tokens (names, dates, keywords) into an expanded set
of semantically related variants: abbreviations, diminutives, transliterations,
leetspeak, phonetic variants, and culturally common nicknames.

The expansion follows a lattice structure where each input token t_i produces
a set S_i of variants. The total semantic space is the union of all S_i sets.

Formally:
    S(t) = {t} U abbrev(t) U diminutive(t) U transliterate(t) U leet(t) U phonetic(t)
    SemanticSpace(P) = Union_{t in P} S(t)

where P is the set of profile tokens.

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Generator
from typing import Any


_ACCENT_MAP: dict[str, str] = {
    "a": "aáàâã", "e": "eéê", "i": "iíî", "o": "oóôõ",
    "u": "uúû", "c": "cç",
}
_ACCENT_STRIP = {}
for _base, _accented in _ACCENT_MAP.items():
    for _ch in _accented:
        if _ch != _base:
            _ACCENT_STRIP[_ch] = _base
            _ACCENT_STRIP[_ch.upper()] = _base.upper()

_LEET_MAP: dict[str, list[str]] = {
    "a": ["4", "@"], "e": ["3"], "i": ["1", "!"], "o": ["0"],
    "s": ["5", "$"], "t": ["7", "+"], "g": ["9"], "b": ["8"],
    "l": ["1", "|"], "z": ["2"],
}

_PT_BR_DIMINUTIVES: dict[str, list[str]] = {
    "inho": ["inho", "inha"],
    "zinho": ["zinho", "zinha"],
    "nho": ["nho", "nha"],
}

_COMMON_NICKNAMES: dict[str, list[str]] = {
    "andre": ["dede", "dede", "dre", "andrezinho"],
    "antonio": ["tonho", "tonio", "tonico"],
    "carlos": ["carlao", "carlinhos", "caca"],
    "daniel": ["dani", "dan"],
    "eduardo": ["du", "dudu", "edu"],
    "fernando": ["fer", "nando", "fefe"],
    "gabriel": ["gabi", "biel", "gabizinho"],
    "gustavo": ["guga", "gu", "guto"],
    "henrique": ["rique", "riquinho", "hen"],
    "joao": ["jj", "joaozinho"],
    "jose": ["ze", "zezinho", "zeca"],
    "lucas": ["luca", "lu", "lucao"],
    "marcelo": ["marcelo", "celinho", "celo"],
    "maria": ["mari", "marizinha"],
    "matheus": ["mat", "teus", "mateus"],
    "paulo": ["paulinho", "pa"],
    "pedro": ["pedrinho", "pe"],
    "rafael": ["rafa", "rafinha"],
    "rodrigo": ["rod", "rods", "digo"],
    "thiago": ["thi", "thiguinho"],
    "william": ["will", "willy", "liam"],
    "ana": ["aninha", "anita"],
    "beatriz": ["bia", "bea"],
    "camila": ["cami", "mila"],
    "juliana": ["ju", "juju", "juli"],
    "larissa": ["lari", "issa"],
    "leticia": ["le", "leti", "ticia"],
    "patricia": ["pati", "pat"],
}


def _strip_accents(text: str) -> str:
    result = []
    for ch in text:
        result.append(_ACCENT_STRIP.get(ch, ch))
    return "".join(result)


def _nfkd_strip(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def expand_token(token: str) -> set[str]:
    """Expand a single token into its semantic variant set S(t).

    Returns a set including: original, lowercase, uppercase, capitalized,
    accent-stripped, abbreviations, diminutives, leet variants, and known
    nicknames.
    """
    variants: set[str] = set()
    if not token or not token.strip():
        return variants

    t = token.strip()
    variants.add(t)
    variants.add(t.lower())
    variants.add(t.upper())
    variants.add(t.capitalize())

    stripped = _strip_accents(t)
    variants.add(stripped)
    variants.add(stripped.lower())

    nfkd = _nfkd_strip(t)
    if nfkd != stripped:
        variants.add(nfkd)
        variants.add(nfkd.lower())

    low = t.lower()
    if len(low) > 2:
        variants.add(low[:3])
        variants.add(low[:4] if len(low) > 3 else low[:3])
        variants.add(low[0] + low[-1])

    base_lower = _strip_accents(low)
    if base_lower in _COMMON_NICKNAMES:
        for nick in _COMMON_NICKNAMES[base_lower]:
            variants.add(nick)
            variants.add(nick.capitalize())

    for base, subs in _LEET_MAP.items():
        if base in low:
            for sub in subs:
                variants.add(low.replace(base, sub, 1))

    variants.discard("")
    return variants


def expand_date(date_str: str) -> set[str]:
    """Expand a date string into common password fragments.

    Accepts formats: YYYY, DD/MM/YYYY, DD-MM-YYYY, DDMMYYYY, YYYY-MM-DD.
    Returns: full year, 2-digit year, day+month combos, reversed, etc.
    """
    variants: set[str] = set()
    if not date_str:
        return variants

    clean = date_str.strip().replace(" ", "")
    variants.add(clean)

    digits = re.sub(r"[^0-9]", "", clean)
    if digits:
        variants.add(digits)
        variants.add(digits[::-1])

    if len(digits) == 8:
        d, m, y = digits[:2], digits[2:4], digits[4:8]
        if int(y) > 1900:
            variants.update([y, y[-2:], d + m, m + d, d + m + y, m + d + y])
            variants.update([y + m + d, d + m + y[-2:], m + y[-2:]])
        else:
            y2, m2, d2 = digits[:4], digits[4:6], digits[6:8]
            variants.update([y2, y2[-2:], d2 + m2, m2 + d2, d2 + m2 + y2])
            variants.update([y2 + m2 + d2, d2 + m2 + y2[-2:]])
    elif len(digits) == 4:
        variants.add(digits[-2:])
    elif len(digits) == 6:
        variants.update([digits[:2] + digits[2:4], digits[2:4] + digits[:2]])
        variants.update([digits[-2:], digits[:4]])

    variants.discard("")
    return variants


def expand_profile(profile: dict[str, Any]) -> dict[str, set[str]]:
    """Expand an entire profile into categorized semantic banks.

    Args:
        profile: Dict with keys like 'names', 'dates', 'keywords', 'pets',
                 'companies', 'phones', 'emails', 'old_passwords'.

    Returns:
        Dict mapping category names to sets of expanded variants.
    """
    banks: dict[str, set[str]] = {
        "names": set(),
        "dates": set(),
        "keywords": set(),
        "pets": set(),
        "companies": set(),
        "phones": set(),
        "emails": set(),
        "old_passwords": set(),
        "numbers": set(),
    }

    for name in profile.get("names", []):
        banks["names"].update(expand_token(name))
        parts = re.split(r"[\s.]+", name)
        if len(parts) > 1:
            initials = "".join(p[0] for p in parts if p)
            banks["names"].add(initials.lower())
            banks["names"].add(initials.upper())
            for part in parts:
                banks["names"].update(expand_token(part))

    for d in profile.get("dates", []):
        banks["dates"].update(expand_date(str(d)))

    for kw in profile.get("keywords", []):
        banks["keywords"].update(expand_token(kw))

    for pet in profile.get("pets", []):
        banks["pets"].update(expand_token(pet))

    for company in profile.get("companies", []):
        banks["companies"].update(expand_token(company))
        parts = company.split()
        if len(parts) > 1:
            banks["companies"].add("".join(p[0] for p in parts).upper())

    for phone in profile.get("phones", []):
        digits = re.sub(r"[^0-9]", "", str(phone))
        if digits:
            banks["phones"].add(digits)
            banks["phones"].add(digits[-4:])
            banks["phones"].add(digits[-8:])

    for email in profile.get("emails", []):
        local = str(email).split("@")[0]
        banks["emails"].update(expand_token(local))

    for old_pw in profile.get("old_passwords", []):
        banks["old_passwords"].add(old_pw)
        if len(old_pw) > 3:
            banks["old_passwords"].add(old_pw[::-1])
            banks["old_passwords"].add(old_pw + "1")
            banks["old_passwords"].add(old_pw + "!")
            banks["old_passwords"].add(old_pw[0].upper() + old_pw[1:])

    for num in profile.get("numbers", []):
        banks["numbers"].add(str(num))

    return banks

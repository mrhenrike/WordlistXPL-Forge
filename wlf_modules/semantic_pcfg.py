"""semantic_pcfg.py - Personal/semantic structure helpers for PCFG-style generation.

Tags tokens as NAME / PET / YEAR / COMPANY / KEYWORD and emits template fills
compatible with profile YAML fields.

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import itertools
from typing import Generator, Iterable


def extract_semantic_banks(profile: dict) -> dict[str, list[str]]:
    banks: dict[str, list[str]] = {
        "NAME": [],
        "PET": [],
        "YEAR": [],
        "YY": [],
        "COMPANY": [],
        "KEYWORD": [],
        "SEP": ["", "@", "#", ".", "_", "!"],
    }
    for key in ("full_name", "short_name", "surname", "partner_name"):
        v = profile.get(key)
        if v:
            banks["NAME"].append(str(v))
    for nick in profile.get("nicknames") or []:
        banks["NAME"].append(str(nick))
    for pet in profile.get("pets") or []:
        if isinstance(pet, dict):
            if pet.get("name"):
                banks["PET"].append(str(pet["name"]))
            if pet.get("year"):
                y = str(pet["year"])
                banks["YEAR"].append(y)
                banks["YY"].append(y[-2:])
        else:
            banks["PET"].append(str(pet))
    if profile.get("company_name"):
        banks["COMPANY"].append(str(profile["company_name"]))
    for kw in profile.get("keywords") or []:
        banks["KEYWORD"].append(str(kw))
    for d in profile.get("special_dates") or []:
        s = str(d)
        banks["YEAR"].append(s)
        if len(s) >= 2:
            banks["YY"].append(s[-2:])
    # dedupe preserve order
    for k, vals in list(banks.items()):
        seen = set()
        out = []
        for v in vals:
            if v and v not in seen:
                seen.add(v)
                out.append(v)
        banks[k] = out or ([""] if k == "SEP" else ["X"])
    return banks


_TEMPLATES = [
    ("COMPANY", "SEP", "PET", "YY"),
    ("COMPANY", "SEP", "YEAR"),
    ("NAME", "SEP", "YEAR"),
    ("NAME", "SEP", "PET", "SEP", "YEAR"),
    ("SEP", "COMPANY", "SEP", "YEAR", "SEP", "PET"),
    ("SEP", "NAME", "SEP", "KEYWORD"),
    ("KEYWORD", "SEP", "YY"),
    ("PET", "SEP", "YEAR"),
]


def generate_semantic(
    profile: dict,
    max_candidates: int = 50_000,
    templates: Iterable[tuple[str, ...]] | None = None,
) -> Generator[str, None, None]:
    banks = extract_semantic_banks(profile)
    tmpls = list(templates or _TEMPLATES)
    seen: set[str] = set()
    count = 0
    for tmpl in tmpls:
        lists = [banks.get(t, ["X"]) for t in tmpl]
        for combo in itertools.product(*lists):
            cand = "".join(combo)
            if len(cand) < 4 or cand in seen:
                continue
            # skip pure-separator empties
            if not any(ch.isalnum() for ch in cand):
                continue
            seen.add(cand)
            yield cand
            count += 1
            if max_candidates and count >= max_candidates:
                return

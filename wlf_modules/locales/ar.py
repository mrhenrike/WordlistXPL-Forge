"""ar.py - Arabic cultural password patterns (transliterated).

Transliterated Arabic names, religious terms, slang and cultural
tokens commonly found in Arabic-language passwords.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from typing import Generator, Optional, Any

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "mohammed","mohamed","ahmad","ahmed","ali","omar","hassan","hussein",
    "khalid","ibrahim","youssef","mustafa","abdallah","abdullah","saeed",
    "nasser","faisal","sultan","rashid","hamad","tariq","waleed","majed",
    "fatima","aisha","maryam","sara","nour","layla","hana","reem",
    "dana","lina","amira","yasmin","salma","rana","dina","noura",
    "asma","abeer","huda","ghada","manal","mona","samira","amal",
]

_SURNAMES = [
    "alsaud","alfahd","almohammad","alhassan","alhussein","alkhalid",
    "alharbi","alghamdi","alqahtani","alshehri","aldossari","alotaibi",
    "almutairi","alsubaie","alanazi","alzahrani","almalki","albishi",
    "ibrahim","hassan","ahmed","ali","khaled","omar","youssef","saeed",
]

_RELIGIOUS = [
    "allah","bismillah","alhamdulillah","mashallah","inshallah",
    "subhanallah","allahuakbar","lailahaillallah","assalamu",
    "quran","sunnah","hadith","salah","zakat","hajj","umrah",
    "ramadan","eid","mubarak","jannah","dua","dhikr","tawba",
    "masjid","mecca","medina","kaaba","alaqsa","muslim","islam",
]

_CULTURE = [
    "dubai","riyadh","jeddah","cairo","beirut","amman","doha",
    "abudhabi","sharjah","muscat","manama","kuwait","casablanca",
    "habibi","habibti","yalla","khalas","sahbi","wallah","akhi",
    "shukran","ahlan","marhaba","sabah","alkhair","masaa",
    "oud","darbuka","dabke","belly","dance","arabic","arab",
    "falafal","hummus","shawarma","kunafa","baklava","mansaf",
    "camel","desert","oasis","palm","dune","bedouin","falcon",
]

_FOOTBALL = [
    "alahli","alhilal","alnassr","alittihad","alshabab","alraed",
    "zamalek","ahly","pyramids","alain","alwahda","alsadd",
    "salah","mahrez","benzema","ronaldo","messi","hakimi",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class AREngine(BaseLocaleEngine):
    locale_code = "ar"
    locale_name = "Arabic"
    locale_aliases = ["ar_sa", "ar_eg", "ar_ae", "arabic"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        seen: set[str] = set()
        count = [0]
        for block, score in [
            (_NAMES, 0.7), (_SURNAMES, 0.6), (_RELIGIOUS, 0.65),
            (_CULTURE, 0.6), (_FOOTBALL, 0.55),
        ]:
            yield from self._emit_block(
                block, _YEARS[:8], _SUFFIXES[:5], _SEPS[:3], score, seen, count,
            )
            if self.max_candidates and count[0] >= self.max_candidates:
                return
        for name in _NAMES[:15]:
            for sur in _SURNAMES[:10]:
                cand = f"{name}{sur}"
                if cand not in seen:
                    seen.add(cand)
                    count[0] += 1
                    if self.max_candidates and count[0] >= self.max_candidates:
                        return
                    yield (cand, 0.6)

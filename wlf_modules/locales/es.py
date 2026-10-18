"""es.py - Spanish-language cultural password patterns.

Names, slang, football, holidays and cultural tokens common across
the Spanish-speaking world (Spain + LatAm).

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from typing import Generator, Optional, Any

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "carlos","jose","juan","miguel","antonio","francisco","pedro","luis",
    "alejandro","fernando","roberto","diego","javier","rafael","pablo",
    "sergio","andres","adrian","jorge","daniel","ricardo","mario","oscar",
    "maria","carmen","rosa","ana","isabel","elena","pilar","laura",
    "cristina","marta","lucia","paula","andrea","sofia","valentina",
    "camila","daniela","gabriela","alejandra","catalina","natalia",
]

_SURNAMES = [
    "garcia","martinez","lopez","gonzalez","rodriguez","fernandez",
    "sanchez","perez","gomez","martin","jimenez","ruiz","hernandez",
    "diaz","moreno","alvarez","romero","alonso","gutierrez","navarro",
    "torres","dominguez","vazquez","ramos","gil","serrano","blanco",
]

_SLANG = [
    "tio","colega","chaval","majo","guay","mola","flipar","currar",
    "pasta","pavo","bro","wey","chido","neta","chale","vato",
    "parce","marica","bacano","chevere","pana","chamo","boludo",
    "pendejo","carnal","cuate","compa","loco","piola","groso",
]

_FOOTBALL = [
    "realmadrid","madrid","barca","barcelona","atletico","sevilla",
    "valencia","betis","bilbao","sociedad","villarreal","celta",
    "bocajuniors","boca","river","riverplate","pumas","america",
    "chivas","santos","colo","penarol","nacional","millonarios",
    "messi","ronaldo","maradona","xavi","iniesta","ramos",
    "modric","benzema","suarez","neymar","laliga","copa",
]

_CULTURE = [
    "espana","spain","mexico","argentina","colombia","chile","peru",
    "fiesta","siesta","amigo","amor","vida","muerte","corazon",
    "sol","luna","playa","cerveza","tequila","sangria","paella",
    "flamenco","tango","salsa","reggaeton","cumbia","bachata",
    "dios","santa","virgen","cristo","iglesia","santos",
    "torero","matador","corrida","olé","vamos","arriba",
]

_HOLIDAYS = [
    "navidad","reyes","semanasanta","diademuertos","independencia",
    "nochebuena","nochevieja","sanfermin","tomatina","fallas",
    "feria","carnaval","guadalupe","sanvalentin","halloween",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class ESEngine(BaseLocaleEngine):
    locale_code = "es"
    locale_name = "Spanish"
    locale_aliases = ["es_es", "es_mx", "es_ar", "es_co", "spanish", "espanol"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        seen: set[str] = set()
        count = [0]
        for block, score in [
            (_NAMES, 0.7), (_SURNAMES, 0.6), (_SLANG, 0.55),
            (_FOOTBALL, 0.65), (_CULTURE, 0.6), (_HOLIDAYS, 0.5),
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

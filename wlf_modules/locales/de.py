"""de.py - German cultural password patterns.

Names, slang, Bundesliga, holidays and cultural tokens for
Germany, Austria and the DACH region.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from collections.abc import Generator

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "hans","peter","thomas","michael","andreas","stefan","markus","christian",
    "martin","matthias","frank","sebastian","alexander","daniel","lukas",
    "jan","tobias","felix","jonas","leon","paul","niklas","max","tim",
    "anna","maria","claudia","sabine","julia","petra","monika","andrea",
    "nicole","katharina","stefanie","christina","laura","lena","sophie",
    "sarah","lisa","sandra","eva","karin","ursula","marie","emma","mia",
]

_SURNAMES = [
    "mueller","schmidt","schneider","fischer","weber","meyer","wagner",
    "becker","schulz","hoffmann","schaefer","koch","bauer","richter",
    "klein","wolf","schroeder","neumann","schwarz","zimmermann",
    "braun","krueger","hofmann","hartmann","lange","schmitt","werner",
]

_SLANG = [
    "geil","krass","alter","digga","bruder","mies","heftig","bock",
    "brudi","ehre","alman","isso","hamma","hammer","mega","voll",
    "chillen","zocken","abgehen","fetzen","saufen","goennen","labern",
    "lauch","ehrenmann","ehrenfrau","sheesh","korrekt","safe",
]

_BUNDESLIGA = [
    "bayern","muenchen","dortmund","bvb","schalke","leverkusen",
    "leipzig","gladbach","wolfsburg","frankfurt","bremen","hertha",
    "koeln","union","berlin","freiburg","augsburg","hoffenheim",
    "beckenbauer","gerd","mueller","klose","lahm","neuer","reus",
    "lewandowski","goetze","schweinsteiger","kimmich","sane",
    "bundesliga","pokal","meister","dfb","mannschaft",
]

_CULTURE = [
    "deutschland","germany","berlin","hamburg","muenchen","koeln",
    "frankfurt","stuttgart","duesseldorf","dresden","leipzig","wien",
    "bier","wurst","pretzel","bratwurst","schnitzel","apfelstrudel",
    "oktoberfest","weihnachten","karneval","fasching","ostern",
    "autobahn","volkswagen","mercedes","bmw","porsche","audi",
    "siemens","adidas","puma","lidl","aldi","lufthansa",
    "wanderlust","kindergarten","zeitgeist","angst","blitz",
    "berg","wald","schloss","rhein","donau","alpen",
]

_HOLIDAYS = [
    "weihnachten","heiligabend","silvester","neujahr","ostern",
    "pfingsten","tagdereinheit","erntedank","nikolaus","advent",
    "oktoberfest","karneval","fasching","rosenmontag","maibaum",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class DEEngine(BaseLocaleEngine):
    locale_code = "de"
    locale_name = "German"
    locale_aliases = ["de_de", "de_at", "de_ch", "german", "deutsch"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        seen: set[str] = set()
        count = [0]
        for block, score in [
            (_NAMES, 0.7), (_SURNAMES, 0.6), (_SLANG, 0.55),
            (_BUNDESLIGA, 0.65), (_CULTURE, 0.6), (_HOLIDAYS, 0.5),
        ]:
            yield from self._emit_block(
                block, _YEARS[:8], _SUFFIXES[:5], _SEPS[:3], score, seen, count,
            )
            if self.max_candidates and count[0] >= self.max_candidates:
                return

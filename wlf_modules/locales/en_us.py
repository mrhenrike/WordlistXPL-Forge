"""en_us.py - US English cultural password patterns.

Names, sports, holidays, slang and institutional patterns common
in American English passwords.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from collections.abc import Generator

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "james","john","robert","michael","david","william","richard","joseph",
    "thomas","charles","christopher","daniel","matthew","anthony","mark",
    "donald","steven","paul","andrew","joshua","kenneth","kevin","brian",
    "george","timothy","ronald","edward","jason","jeffrey","ryan",
    "mary","patricia","jennifer","linda","barbara","elizabeth","susan",
    "jessica","sarah","karen","lisa","nancy","betty","margaret","sandra",
    "ashley","emily","donna","michelle","dorothy","carol","amanda","melissa",
]

_SURNAMES = [
    "smith","johnson","williams","brown","jones","garcia","miller","davis",
    "rodriguez","martinez","hernandez","lopez","gonzalez","wilson","anderson",
    "thomas","taylor","moore","jackson","martin","lee","perez","thompson",
    "white","harris","sanchez","clark","ramirez","lewis","robinson","walker",
]

_SLANG = [
    "yolo","goat","lit","bruh","fam","bro","dude","chill","vibe",
    "flex","savage","fire","bet","cap","slay","bussin","rizz","skibidi",
    "sus","npc","sigma","chad","based","cringe","cope","ratio",
]

_HOLIDAYS = [
    "christmas","xmas","thanksgiving","halloween","july4th","4thofjuly",
    "easter","valentines","memorial","labor","newyear","mlk",
    "superbowl","blackfriday","cybermonday","stpatricks",
]

_SPORTS = [
    "cowboys","eagles","steelers","packers","patriots","chiefs","49ers",
    "lakers","celtics","bulls","warriors","heat","nets","knicks",
    "yankees","dodgers","redsox","cubs","braves","astros",
    "bruins","penguins","rangers","blackhawks","lightning",
    "nfl","nba","mlb","nhl","ncaa","espn",
    "brady","lebron","jordan","kobe","curry","mahomes",
]

_INSTITUTIONS = [
    "usarmy","usnavy","usmc","airforce","coastguard","pentagon",
    "fbi","cia","nsa","dhs","secret","service","whitehouse",
    "walmart","amazon","google","apple","microsoft","tesla","meta",
    "harvard","mit","stanford","yale","princeton","ucla","nyu",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#", "!"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "@123", "!!", "2024", "2025", "2026"]


@register_engine
class ENUSEngine(BaseLocaleEngine):
    locale_code = "en-us"
    locale_name = "US English"
    locale_aliases = ["en_us", "enus", "american"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        seen: set[str] = set()
        count = [0]
        for block, score in [
            (_NAMES, 0.7), (_SURNAMES, 0.6), (_SLANG, 0.55),
            (_HOLIDAYS, 0.6), (_SPORTS, 0.65), (_INSTITUTIONS, 0.5),
        ]:
            yield from self._emit_block(
                block, _YEARS[:8], _SUFFIXES[:6], _SEPS[:3], score, seen, count,
            )
            if self.max_candidates and count[0] >= self.max_candidates:
                return
        for name in _NAMES[:15]:
            for sur in _SURNAMES[:10]:
                for sep in ("", "_", "."):
                    cand = f"{name}{sep}{sur}"
                    if cand not in seen:
                        seen.add(cand)
                        count[0] += 1
                        if self.max_candidates and count[0] >= self.max_candidates:
                            return
                        yield (cand, 0.6)

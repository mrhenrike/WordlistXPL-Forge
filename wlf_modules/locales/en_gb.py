"""en_gb.py - British English cultural password patterns.

UK-specific names, football, monarchy, slang and institutional
patterns commonly found in British passwords.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from typing import Generator, Optional, Any

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "oliver","harry","george","jack","charlie","leo","freddie","oscar",
    "arthur","noah","archie","alfie","henry","thomas","joshua","james",
    "william","edward","alexander","samuel","benjamin","lucas","max",
    "olivia","amelia","isla","emily","ava","jessica","mia","ella",
    "sophie","grace","lily","isabella","charlotte","rosie","daisy",
    "florence","ruby","poppy","alice","freya","matilda","phoebe",
]

_SURNAMES = [
    "smith","jones","taylor","brown","williams","wilson","johnson",
    "davies","robinson","wright","thompson","evans","walker","white",
    "roberts","green","hall","wood","jackson","clarke","patel","khan",
]

_SLANG = [
    "mate","bruv","innit","cheers","bloke","cheeky","bollocks","rubbish",
    "bloody","knackered","dodgy","brilliant","gutted","lad","lass",
    "nutter","muppet","skint","snog","banter","chav","geezer",
]

_FOOTBALL = [
    "arsenal","chelsea","liverpool","mancity","manutd","tottenham","spurs",
    "westham","everton","newcastle","aston","villa","leicester","wolves",
    "leeds","celtic","rangers","realmadirid","barca",
    "premier","league","fa","cup","wembley","anfield","oldtrafford",
    "beckham","rooney","gerrard","lampard","shearer","kane","rashford",
]

_CULTURE = [
    "queen","king","royal","crown","palace","windsor","buckingham",
    "london","manchester","birmingham","leeds","bristol","liverpool",
    "edinburgh","glasgow","cardiff","belfast","oxford","cambridge",
    "bbc","nhs","tesco","asda","sainsburys","primark","greggs",
    "tea","crumpet","fish","chips","pub","pint","lager","cider",
    "brexit","pound","sterling","quid","tenner","fiver",
]

_HOLIDAYS = [
    "christmas","boxing","easter","bankholiday","bonfire","night",
    "guyfawkes","remembrance","jubilee","coronation","hogmanay",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class ENGBEngine(BaseLocaleEngine):
    locale_code = "en-gb"
    locale_name = "British English"
    locale_aliases = ["en_gb", "engb", "british", "uk"]

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

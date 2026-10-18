"""hi.py - Hindi/Indian cultural password patterns (transliterated).

Romanized Hindi names, Bollywood references, cricket, festivals
and cultural tokens found in Indian passwords.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from typing import Generator, Optional, Any

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "raj","rahul","amit","vijay","sunil","anil","rohit","vikas",
    "sachin","deepak","rajesh","suresh","mahesh","dinesh","ganesh",
    "mukesh","ramesh","lokesh","naresh","pankaj","sanjay","ajay",
    "priya","neha","pooja","anita","sunita","kavita","meena","rekha",
    "asha","nisha","ritu","swati","divya","preeti","anjali","sonal",
    "komal","sapna","geeta","seema","mamta","shikha","ruchi","mansi",
]

_SURNAMES = [
    "sharma","verma","gupta","singh","kumar","patel","joshi","mishra",
    "yadav","pandey","tiwari","dubey","trivedi","srivastava","agarwal",
    "mehta","shah","desai","nair","menon","reddy","rao","pillai",
    "iyer","mukherjee","banerjee","chatterjee","bose","das","ghosh",
]

_BOLLYWOOD = [
    "shahrukh","srk","amitabh","salman","aamir","ranbir","ranveer",
    "deepika","priyanka","katrina","alia","kareena","aishwarya",
    "bollywood","filmi","desi","item","masala","dhoom","dangal",
    "sholay","ddlj","lagaan","barfi","pk","queen","padmavat",
]

_CRICKET = [
    "sachin","tendulkar","dhoni","virat","kohli","rohit","bumrah",
    "kapil","gavaskar","dravid","ganguly","sehwag","yuvraj",
    "cricket","ipl","worldcup","sixers","boundary","wicket",
    "csk","mi","rcb","kkr","srh","dc","rr","pbks","gt","lsg",
]

_CULTURE = [
    "india","bharat","hindustan","delhi","mumbai","bangalore",
    "chennai","kolkata","hyderabad","pune","ahmedabad","jaipur",
    "namaste","dhanyavad","pyaar","dost","yaar","bhai","didi",
    "guru","karma","dharma","moksha","mantra","yoga","chakra",
    "diwali","holi","ganesh","shiva","vishnu","krishna","ram",
    "hanuman","durga","lakshmi","saraswati","puja","aarti",
    "chai","biryani","masala","paneer","naan","dosa","samosa",
    "tata","reliance","infosys","wipro","hcl","mahindra","bajaj",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class HIEngine(BaseLocaleEngine):
    locale_code = "hi"
    locale_name = "Hindi/Indian"
    locale_aliases = ["hi_in", "hindi", "indian", "india"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        seen: set[str] = set()
        count = [0]
        for block, score in [
            (_NAMES, 0.7), (_SURNAMES, 0.6), (_BOLLYWOOD, 0.6),
            (_CRICKET, 0.65), (_CULTURE, 0.6),
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

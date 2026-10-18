"""ko.py - Korean cultural password patterns (romanized).

Romanized Korean names, K-pop/K-drama references, gaming culture
and cultural tokens found in Korean passwords.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from typing import Generator, Optional, Any

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "minho","jungkook","taehyung","jimin","seokjin","yoongi","hoseok",
    "namjoon","jihoon","seungmin","changbin","hyunjin","felix","bangchan",
    "doyoung","jaehyun","mark","taeyong","jeno","haechan","renjun",
    "jisoo","jennie","rose","lisa","irene","seulgi","joy","wendy",
    "yeri","nayeon","momo","sana","dahyun","chaeyoung","tzuyu",
    "winter","karina","giselle","ningning","minji","hanni","danielle",
]

_SURNAMES = [
    "kim","lee","park","choi","jung","kang","cho","yoon","jang",
    "lim","han","oh","seo","shin","kwon","hwang","ahn","song",
    "yoo","hong","moon","yang","bae","baek","heo","nam","sim",
]

_KPOP = [
    "bts","blackpink","exo","twice","stray","kids","nct","aespa",
    "seventeen","ateez","enhypen","newjeans","lesserafim","ive",
    "bigbang","snsd","shinee","redvelvet","mamamoo","itzy","gidle",
    "army","blink","once","stay","carat","atiny","engene","bunny",
    "idol","aegyo","bias","maknae","hyung","unnie","noona","oppa",
    "daebak","fighting","hwaiting","saranghae","aigoo","omo",
]

_CULTURE = [
    "seoul","busan","incheon","daegu","gwangju","daejeon","ulsan",
    "korea","hanguk","joseon","hallyu","hanbok","hangeul","kimchi",
    "bibimbap","bulgogi","tteokbokki","soju","makgeolli","ramyeon",
    "samsung","hyundai","lg","kia","lotte","kakao","naver","coupang",
    "taekwondo","hapkido","ssireum","starcraft","lol","overwatch",
    "faker","skt","t1","geng","damwon","drx","kt","rolster",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class KOEngine(BaseLocaleEngine):
    locale_code = "ko"
    locale_name = "Korean"
    locale_aliases = ["ko_kr", "korean", "hanguk"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        seen: set[str] = set()
        count = [0]
        for block, score in [
            (_NAMES, 0.7), (_SURNAMES, 0.6),
            (_KPOP, 0.65), (_CULTURE, 0.6),
        ]:
            yield from self._emit_block(
                block, _YEARS[:8], _SUFFIXES[:5], _SEPS[:3], score, seen, count,
            )
            if self.max_candidates and count[0] >= self.max_candidates:
                return
        for sur in _SURNAMES[:15]:
            for name in _NAMES[:10]:
                cand = f"{sur}{name}"
                if cand not in seen:
                    seen.add(cand)
                    count[0] += 1
                    if self.max_candidates and count[0] >= self.max_candidates:
                        return
                    yield (cand, 0.6)

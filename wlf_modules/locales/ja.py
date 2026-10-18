"""ja.py - Japanese cultural password patterns.

Romaji names, anime/gaming culture, holidays and institutional
patterns common in Japanese passwords. Uses romanized forms since
password fields typically accept ASCII.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from typing import Generator, Optional, Any

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "takeshi","hiroshi","yuki","kenji","daisuke","ryota","kazuki","shota",
    "naoki","masashi","takumi","haruto","sota","ren","yuto","kaito",
    "hayato","riku","minato","asahi","hinata","yamato","itsuki","sora",
    "sakura","yui","hana","aoi","mio","rin","mei","kokona",
    "himari","ichika","akari","koharu","yuna","riko","sara","misaki",
    "haruka","nanami","ayaka","momoka","shiori","kana","natsuki",
]

_SURNAMES = [
    "sato","suzuki","takahashi","tanaka","watanabe","ito","yamamoto",
    "nakamura","kobayashi","kato","yoshida","yamada","sasaki","matsumoto",
    "inoue","kimura","hayashi","shimizu","yamaguchi","mori","abe","ikeda",
    "hashimoto","yamashita","ishikawa","nakajima","maeda","fujita",
]

_CULTURE = [
    "tokyo","osaka","kyoto","yokohama","nagoya","sapporo","fukuoka",
    "hiroshima","sendai","kobe","okinawa","hokkaido","fuji","sakura",
    "samurai","ninja","bushido","katana","shogun","ronin","geisha",
    "sushi","ramen","sake","wasabi","matcha","onigiri","tempura",
    "karate","judo","sumo","kendo","aikido","budo","dojo","sensei",
    "manga","anime","otaku","kawaii","sugoi","baka","senpai","kohai",
    "shinkansen","kaizen","ikigai","wabi","sabi","mottainai",
    "toyota","sony","nintendo","honda","panasonic","mitsubishi",
]

_GAMING_ANIME = [
    "naruto","sasuke","goku","vegeta","luffy","ichigo","pikachu",
    "pokemon","zelda","mario","sephiroth","cloud","kirby","metroid",
    "finalfantasy","dragonball","onepiece","bleach","deathnote",
    "evangelion","gundam","akira","ghibli","totoro","spirited",
    "jojo","berserk","hunter","fullmetal","alchemist","demon",
    "slayer","tanjiro","nezuko","jujutsu","kaisen","itadori",
]

_HOLIDAYS = [
    "oshogatsu","hanami","obon","tanabata","shogatsu","seijin",
    "kodomonohi","bunka","shichi","gosan","golden","week",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class JAEngine(BaseLocaleEngine):
    locale_code = "ja"
    locale_name = "Japanese"
    locale_aliases = ["ja_jp", "japanese", "japan", "nihongo"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        seen: set[str] = set()
        count = [0]
        for block, score in [
            (_NAMES, 0.7), (_SURNAMES, 0.6), (_CULTURE, 0.6),
            (_GAMING_ANIME, 0.65), (_HOLIDAYS, 0.5),
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

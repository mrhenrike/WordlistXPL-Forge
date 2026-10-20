"""pt_pt.py - European Portuguese cultural password patterns.

Names, slang, football, holidays and cultural tokens specific to
Portugal (distinct from PT-BR patterns in br_deep_engine).

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from collections.abc import Generator

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "joao","pedro","miguel","tiago","andre","francisco","diogo","rafael",
    "bruno","hugo","rui","nuno","luis","ricardo","daniel","filipe",
    "antonio","jose","manuel","carlos","goncalo","duarte","bernardo",
    "maria","ana","ines","catarina","sofia","mariana","beatriz","rita",
    "sara","diana","raquel","claudia","carla","teresa","isabel","helena",
    "marta","patricia","monica","leonor","matilde","carolina","margarida",
]

_SURNAMES = [
    "silva","santos","ferreira","pereira","oliveira","costa","rodrigues",
    "martins","jesus","sousa","fernandes","goncalves","gomes","lopes",
    "marques","alves","almeida","ribeiro","pinto","carvalho","teixeira",
    "moreira","correia","mendes","nunes","soares","vieira","monteiro",
]

_SLANG = [
    "gajo","gaja","fixe","bue","cena","tuga","puto","bacano",
    "bestial","brutal","catano","caralho","foda","ganda","irmao",
    "mano","tipo","bazar","curte","moca","onda","reles","tasca",
    "bifana","fino","imperial","bagaco","pasteldenata","francesinha",
]

_FOOTBALL = [
    "benfica","sporting","porto","braga","vitoria","guimaraes",
    "belenenses","boavista","maritimo","academica","leiria",
    "ronaldo","cr7","eusebio","figo","rui","costa","pauleta",
    "mourinho","bernardo","fernandes","pepe","nani","quaresma",
    "primeiraliga","liganos","taca","supertaca","derby",
]

_CULTURE = [
    "portugal","lisboa","porto","algarve","madeira","acores","coimbra",
    "braga","faro","sintra","evora","aveiro","guimaraes","cascais",
    "fado","amalia","saudade","bacalhau","vinho","ginjinha","pasteis",
    "azulejo","manueline","alfama","bairroalto","belem","chiado",
    "camoes","pessoa","saramago","descobrimentos","navegadores",
    "caravela","quinas","escudo","euro","lusitano","luso","tuga",
]

_HOLIDAYS = [
    "natal","pascoa","carnaval","anonovo","reis","25abril","10junho",
    "diasdetodos","imaculada","restauracao","liberdade","camoes",
    "saojoao","santoantonio","saopedro","festas","romaria",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class PTPTEngine(BaseLocaleEngine):
    locale_code = "pt-pt"
    locale_name = "European Portuguese"
    locale_aliases = ["pt_pt", "ptpt", "portuguese", "portugal"]

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

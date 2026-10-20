"""fr.py - French cultural password patterns.

Names, verlan/argot, football, holidays and cultural tokens for
France and Francophone regions.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from collections.abc import Generator

from wlf_modules.locales import BaseLocaleEngine, register_engine

_NAMES = [
    "jean","pierre","louis","nicolas","antoine","julien","thomas","paul",
    "alexandre","maxime","lucas","hugo","mathieu","vincent","raphael",
    "clement","gabriel","arthur","etienne","olivier","francois","benoit",
    "marie","camille","julie","sophie","charlotte","manon","lea","chloe",
    "emma","clara","alice","lucie","louise","pauline","marine","aurelie",
    "margaux","mathilde","anais","sarah","laura","elise","juliette",
]

_SURNAMES = [
    "martin","bernard","thomas","petit","robert","richard","durand",
    "dubois","moreau","laurent","simon","michel","lefevre","leroy",
    "roux","david","bertrand","morel","fournier","girard","bonnet",
    "dupont","lambert","fontaine","rousseau","vincent","muller","blanc",
]

_SLANG = [
    "mec","meuf","ouf","kiffer","chelou","relou","chanme","daron",
    "daronne","belek","seum","bail","wesh","wallah","frere","soeur",
    "bolos","cimer","tise","bicrave","hagra","hess","gow",
    "verlan","keuf","reum","reup","teuf","zarbi","vener","kenavo",
]

_FOOTBALL = [
    "psg","paris","marseille","lyon","monaco","lille","rennes",
    "nice","nantes","lens","toulouse","bordeaux","saintetienne",
    "mbappe","zidane","platini","henry","griezmann","benzema",
    "kante","pogba","ribery","vieira","deschamps","papin",
    "ligue1","coupe","allez","champions","equipedefrance",
]

_CULTURE = [
    "france","paris","lyon","marseille","toulouse","bordeaux","lille",
    "baguette","croissant","fromage","vin","champagne","cognac",
    "bonjour","merci","amour","liberte","egalite","fraternite",
    "eiffel","louvre","versailles","montmartre","champs","elysees",
    "revolution","napoleon","republique","tricolore","marseillaise",
    "boulangerie","cafe","bistrot","terrasse","pastis","crepe",
]

_HOLIDAYS = [
    "noel","paques","toussaint","bastille","14juillet","jourdean",
    "pentecote","ascension","armistice","fetenat","chandeleur",
    "poissondavril","fetedelamusique","beaujolais",
]

_YEARS = ["2020","2021","2022","2023","2024","2025","2026","20","21","22","23","24","25","26"]
_SEPS = ["", "_", ".", "@", "#"]
_SUFFIXES = ["!", "@", "#", "123", "1234", "2024", "2025", "2026"]


@register_engine
class FREngine(BaseLocaleEngine):
    locale_code = "fr"
    locale_name = "French"
    locale_aliases = ["fr_fr", "french", "francais"]

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

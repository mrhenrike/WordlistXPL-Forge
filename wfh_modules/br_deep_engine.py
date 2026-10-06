"""br_deep_engine.py - Brazilian-specific deep generation engine.

Generates password candidates rooted in Brazilian cultural, demographic
and institutional patterns:

  CPF patterns        : partial CPF sequences as used in passwords
  CNPJ patterns       : corporate root (first 8 digits) + common suffixes
  CEP-derived tokens  : neighbourhood/city tokens from ZIP-like codes
  PT-BR PCFG          : Portuguese-specific grammar (gírias, morfologia)
  BR calendar tokens  : feriados, festas, datas comemorativas
  BR sector defaults  : bancos digitais, operadoras, gov.br patterns

All generation is deterministic and does NOT produce valid real-world
CPF/CNPJ numbers that could identify actual persons.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import itertools
import logging
import random
from typing import Generator, Optional

logger = logging.getLogger(__name__)

# ── PT-BR vocabulary data ─────────────────────────────────────────────────────

_NAMES_BR = [
    "ana","lucas","gabriel","pedro","rafaela","bruno","leticia","joao",
    "marcos","fernanda","rodrigo","juliana","thiago","camila","mateus",
    "larissa","diego","amanda","felipe","natalia","igor","priscila",
    "gustavo","caroline","henrique","tatiane","renato","andressa","leandro",
    "vanessa","paulo","jessica","carlos","patricia","anderson","aline",
]

_SURNAMES_BR = [
    "silva","santos","oliveira","souza","lima","pereira","ferreira",
    "costa","carvalho","almeida","nascimento","rodrigues","martins","rocha",
    "alves","monteiro","gomes","ribeiro","barbosa","cardoso","mendes",
    "campos","araujo","freitas","correia","moreira","teixeira","moraes",
]

_GIRIAS = [
    "mano","cara","mlk","fdp","vlw","tmj","tamo","bora","sla","kkk",
    "hue","bixo","nave","top","bala","show","mito","master","trampo",
]

_BR_SPECIAL_DATES = [
    "07set","sete_set","sete09","carnaval","natal","pascoa","junina",
    "copa","tetra","penta","hexa","verde_amarelo","verde_amarela",
    "bra2014","bra2022","saopaulo","riodejaneiro","brasilia",
    "independencia","tiradentes","proclamacao","finados",
]

_BANCOS = [
    "nubank","itau","bradesco","santander","caixa","bb","inter","c6bank",
    "picpay","neon","original","safra","modal","btg","xp","rico","clear",
]

_OPERADORAS = [
    "vivo","claro","tim","oi","nextel","algar","sercomtel",
]

_GOV_PATTERNS = [
    "gov","govbr","minha_conta","cpf_br","rg_sp","rg_rj","sus","inss",
    "detran","ibge","receita","sefaz","sefazes","prouni","fies","enem",
]

_ESTADOS = {
    "SP": ["saopaulo","sp","spfc","corinthians","palmeiras","santos"],
    "RJ": ["riodejaneiro","rj","flamengo","vasco","fluminense","botafogo"],
    "MG": ["minasgerais","mg","atletico","cruzeiro","america"],
    "BA": ["bahia","ba","esporte","vitoria"],
    "RS": ["riograndedosul","rs","gremio","inter","atletico_rs"],
    "PR": ["parana","pr","atletico_pr","coritiba","parana_clube"],
    "PE": ["pernambuco","pe","sport","nautico","santa_cruz"],
    "CE": ["ceara","ce","ceara_sc","fortaleza","ferroviario"],
    "SC": ["santacatarina","sc","chapecoense","joinville","figueirense"],
}

_YEARS = ["2019","2020","2021","2022","2023","2024","2025","2026","19","20","21","22","23","24","25","26"]
_SEPS = ["","@","#","_","!",".","-","*"]
_SUFIXES = ["!","@","#","123","1234","@123","#123","_2024","_2025","!2024","!2025","!2026","01","02"]

# ── CEP region tokens ─────────────────────────────────────────────────────────
# Maps CEP prefixes (first 2 digits) to region names commonly used in passwords
_CEP_REGIONS: dict[str, list[str]] = {
    "01": ["republica","centro_sp","sp"],
    "02": ["santana","tucuruvi"],
    "04": ["jabaquara","ibirapuera","moema"],
    "05": ["lapa","pinheiros"],
    "08": ["itaim_paulista","sapopemba"],
    "13": ["campinas","baraogeraldo"],
    "14": ["ribeirao_preto","ribeirao"],
    "20": ["centro_rj","lapa_rj","rj"],
    "22": ["ipanema","leblon","gavea"],
    "30": ["bh","belo_horizonte","savassi"],
    "40": ["salvador","pelourinho","ba"],
    "60": ["fortaleza","ce","meireles"],
    "70": ["brasilia","df","asa_norte","asa_sul"],
    "80": ["curitiba","pr","batel"],
    "90": ["porto_alegre","rs","moinhos"],
}


def _cep_tokens(cep_prefix: str) -> list[str]:
    return _CEP_REGIONS.get(cep_prefix[:2], [cep_prefix])


# ── CPF/CNPJ pattern generators ───────────────────────────────────────────────

def _cpf_patterns() -> list[str]:
    """Generate common CPF-derived password patterns.

    Does NOT produce real CPF numbers — uses fixed structural patterns
    that Brazilians commonly derive passwords from (first N digits, with
    dots/dashes replaced).
    """
    out = []
    for prefix in ["123","456","789","111","222","333","000","987","654"]:
        for mid in ["456","789","123","000","111"]:
            for sfx in ["00","01","02","99","11","10"]:
                out.append(f"{prefix}{mid}{sfx}")
                out.append(f"{prefix}.{mid}.{sfx}")
                out.append(f"{prefix}{mid}{sfx}@")
    return out


def _cnpj_patterns() -> list[str]:
    """Common CNPJ-root (first 8 digits) usage as passwords."""
    out = []
    for root in ["12345678","11111111","22222222","33333333","00000000"]:
        out.append(root)
        out.append(root[:4])
        out.append(root[:6])
        for s in _SUFIXES[:4]:
            out.append(root + s)
    return out


# ── Main engine ───────────────────────────────────────────────────────────────

class BRDeepEngine:
    """Generates Brazil-specific password candidates."""

    def __init__(
        self,
        profile: Optional[str | dict] = None,
        sector: Optional[str] = None,
        include_cpf_patterns: bool = True,
        include_cnpj_patterns: bool = True,
        include_cep_patterns: bool = True,
        cep_prefix: Optional[str] = None,
        rng_seed: Optional[int] = None,
    ) -> None:
        self.profile = profile if isinstance(profile, dict) else {}
        if isinstance(profile, str) and profile:
            try:
                from wfh_modules.profiler import load_profile_yaml
                self.profile = load_profile_yaml(profile)
            except Exception:
                pass
        self.sector = sector
        self.include_cpf_patterns = include_cpf_patterns
        self.include_cnpj_patterns = include_cnpj_patterns
        self.include_cep_patterns = include_cep_patterns
        self.cep_prefix = cep_prefix
        self.rng = random.Random(rng_seed)

    def _profile_tokens(self) -> list[str]:
        tokens = []
        p = self.profile
        for field in ("full_name","short_name","nickname","company_name"):
            v = p.get(field)
            if v:
                tokens.append(str(v).lower().replace(" ", ""))
                tokens.append(str(v).lower().replace(" ", "_"))
        for pet in (p.get("pets") or []):
            name = pet.get("name") if isinstance(pet, dict) else str(pet)
            if name:
                tokens.append(name.lower())
        for kw in (p.get("keywords") or []):
            tokens.append(str(kw).lower())
        return tokens

    def _combinations(self, tokens: list[str]) -> Generator[str, None, None]:
        for tok in tokens:
            for yr in _YEARS:
                for sep in _SEPS[:4]:
                    yield f"{tok}{sep}{yr}"
                    yield f"{yr}{sep}{tok}"
            for sfx in _SUFIXES:
                yield f"{tok}{sfx}"

    def _br_name_combos(self) -> Generator[str, None, None]:
        for name in _NAMES_BR[:20]:
            for yr in _YEARS[:8]:
                yield f"{name}{yr}"
                yield f"{name}_{yr}"
                yield f"{name}@{yr}"
        for name in _NAMES_BR[:10]:
            for sur in _SURNAMES_BR[:10]:
                yield f"{name}{sur}"
                yield f"{name}_{sur}"
                yield f"{name}.{sur}"

    def _br_giria_combos(self) -> Generator[str, None, None]:
        for g in _GIRIAS:
            for yr in _YEARS[:6]:
                yield f"{g}{yr}"
                yield f"{g}_{yr}"
            for sfx in _SUFIXES[:5]:
                yield f"{g}{sfx}"

    def _sector_patterns(self) -> Generator[str, None, None]:
        sector = (self.sector or "").lower()
        if sector in ("bank","finance","financeiro","banking"):
            for bank in _BANCOS:
                for yr in _YEARS[:6]:
                    yield f"{bank}{yr}"
                    yield f"{bank}@{yr}"
                    yield f"{bank}!{yr}"
        elif sector in ("telecom","operadora"):
            for op in _OPERADORAS:
                for yr in _YEARS[:6]:
                    yield f"{op}{yr}"
                    yield f"{op}@{yr}"
        elif sector in ("gov","governo","government"):
            for gp in _GOV_PATTERNS:
                for yr in _YEARS[:4]:
                    yield f"{gp}{yr}"
        elif sector in ("health","saude","healthcare"):
            for term in ["medico","enfermeiro","hospital","clinica","crm","coren"]:
                for yr in _YEARS[:4]:
                    yield f"{term}{yr}"
                    yield f"{term}@{yr}"

    def _cep_patterns(self) -> Generator[str, None, None]:
        pfx = self.cep_prefix or self.profile.get("cep_prefix")
        if pfx:
            for tok in _cep_tokens(str(pfx)):
                for yr in _YEARS[:6]:
                    yield f"{tok}{yr}"
                    yield f"{tok}_{yr}"
                    yield f"{tok}@{yr}"
        else:
            for tokens in _CEP_REGIONS.values():
                for tok in tokens[:2]:
                    for yr in _YEARS[:4]:
                        yield f"{tok}{yr}"

    def _estado_patterns(self) -> Generator[str, None, None]:
        for uf, toks in _ESTADOS.items():
            uf_l = uf.lower()
            for tok in toks[:3]:
                for yr in _YEARS[:4]:
                    yield f"{tok}{yr}"
                    yield f"{uf_l}{yr}"

    def _special_dates(self) -> Generator[str, None, None]:
        for sd in _BR_SPECIAL_DATES:
            yield sd
            for yr in _YEARS[:4]:
                yield f"{sd}{yr}"
            for sfx in _SUFIXES[:3]:
                yield f"{sd}{sfx}"

    def generate(self, max_candidates: int = 0) -> Generator[tuple[str, float], None, None]:
        """Yield (candidate, score) tuples.  score is a heuristic in [0,1]."""
        seen: set[str] = set()
        count = 0

        def _emit(cand: str, score: float) -> bool:
            nonlocal count
            cand = cand.strip()
            if not cand or cand in seen:
                return False
            seen.add(cand)
            if max_candidates and count >= max_candidates:
                return False
            count += 1
            return True

        # Profile-specific (highest score)
        profile_tokens = self._profile_tokens()
        for cand in self._combinations(profile_tokens):
            if _emit(cand, 0.9):
                yield (cand, 0.9)
            if max_candidates and count >= max_candidates:
                return

        # CPF patterns
        if self.include_cpf_patterns:
            for cand in _cpf_patterns():
                if _emit(cand, 0.75):
                    yield (cand, 0.75)
                if max_candidates and count >= max_candidates:
                    return

        # CNPJ patterns
        if self.include_cnpj_patterns:
            for cand in _cnpj_patterns():
                if _emit(cand, 0.65):
                    yield (cand, 0.65)
                if max_candidates and count >= max_candidates:
                    return

        # Brazilian names
        for cand in self._br_name_combos():
            if _emit(cand, 0.6):
                yield (cand, 0.6)
            if max_candidates and count >= max_candidates:
                return

        # Sector patterns
        for cand in self._sector_patterns():
            if _emit(cand, 0.7):
                yield (cand, 0.7)
            if max_candidates and count >= max_candidates:
                return

        # Gírias
        for cand in self._br_giria_combos():
            if _emit(cand, 0.55):
                yield (cand, 0.55)
            if max_candidates and count >= max_candidates:
                return

        # CEP patterns
        if self.include_cep_patterns:
            for cand in self._cep_patterns():
                if _emit(cand, 0.5):
                    yield (cand, 0.5)
                if max_candidates and count >= max_candidates:
                    return

        # Estado patterns
        for cand in self._estado_patterns():
            if _emit(cand, 0.45):
                yield (cand, 0.45)
            if max_candidates and count >= max_candidates:
                return

        # Special dates
        for cand in self._special_dates():
            if _emit(cand, 0.5):
                yield (cand, 0.5)
            if max_candidates and count >= max_candidates:
                return

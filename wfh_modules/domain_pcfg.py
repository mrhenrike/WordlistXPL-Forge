"""domain_pcfg.py - Domain-specific PCFG auto-training.

Automatically trains a PCFG grammar from:
  - A target domain/sector (corporate, healthcare, education, finance, gov, etc.)
  - Public corpus wordlists from that sector
  - Profile-extracted vocabulary

Supports incremental training (add new passwords at runtime) and serialization
to/from JSON for model persistence.

Grammar definition:
  S  → {structure}+
  Aₙ → alpha segment of length n (with domain-specific vocab)
  Dₙ → digit segment of length n
  Sₙ → special segment of length n

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Generator, Optional


# ── Domain vocabulary seeds ───────────────────────────────────────────────────

_DOMAIN_VOCAB: dict[str, list[str]] = {
    "corporate": [
        "empresa", "corp", "admin", "root", "server", "backup", "office",
        "windows", "linux", "network", "firewall", "vpn", "sap", "erp",
        "manager", "director", "ceo", "cfo", "ti", "helpdesk",
    ],
    "healthcare": [
        "hospital", "medico", "paciente", "saude", "clinica", "enfermeira",
        "prontuario", "exame", "cirurgia", "farmacia", "sus", "plano",
        "radiology", "lab", "health", "nurse", "doctor",
    ],
    "education": [
        "escola", "aluno", "professor", "faculdade", "campus", "biblioteca",
        "vestibular", "enem", "trabalho", "tcc", "curso", "aula",
        "university", "student", "teacher", "class",
    ],
    "finance": [
        "banco", "financeiro", "credito", "debito", "investimento", "bolsa",
        "forex", "trading", "acoes", "fundo", "conta", "cartao",
        "bank", "finance", "invest", "stock",
    ],
    "gov": [
        "governo", "ministerio", "prefeitura", "secretaria", "servidore",
        "funcional", "sisp", "siafi", "siape", "sei", "cpf", "cnpj",
        "inss", "receita", "federal", "estadual", "municipal",
    ],
    "ecommerce": [
        "loja", "pedido", "compra", "produto", "estoque", "frete",
        "cliente", "fornecedor", "nfe", "marketplace", "shopee", "mercado",
        "amazon", "shop", "store", "order", "cart",
    ],
    "gaming": [
        "gamer", "player", "game", "rank", "level", "boss", "quest",
        "guild", "raid", "pvp", "steam", "xbox", "ps5", "lol", "cs",
    ],
}

_GENERIC_VOCAB = [
    "senha", "password", "pass", "admin", "user", "root", "test",
    "hello", "welcome", "login", "secure", "safe", "key",
]


def _sector_vocab(sector: str) -> list[str]:
    return _DOMAIN_VOCAB.get(sector.lower(), []) + _GENERIC_VOCAB


# ── PCFG training ─────────────────────────────────────────────────────────────

def _seg_type(s: str) -> str:
    if s.isalpha():
        return "A"
    if s.isdigit():
        return "D"
    return "S"


def _tokenize(pw: str) -> list[tuple[str, str]]:
    segs = []
    for m in re.finditer(r"[A-Za-z]+|[0-9]+|[^A-Za-z0-9]+", pw):
        val = m.group()
        segs.append((_seg_type(val), val))
    return segs


@dataclass
class DomainPCFGModel:
    sector: str = "generic"
    structure_counts: dict[str, float] = field(default_factory=dict)
    segment_counts: dict[str, dict[str, float]] = field(default_factory=lambda: defaultdict(dict))
    total_trained: int = 0
    alpha: float = 0.1    # Dirichlet smoothing

    def to_dict(self) -> dict:
        return {
            "sector": self.sector,
            "structure_counts": self.structure_counts,
            "segment_counts": dict(self.segment_counts),
            "total_trained": self.total_trained,
            "alpha": self.alpha,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DomainPCFGModel":
        m = cls(sector=d.get("sector", "generic"), alpha=d.get("alpha", 0.1))
        m.structure_counts = d.get("structure_counts", {})
        m.segment_counts = defaultdict(dict, d.get("segment_counts", {}))
        m.total_trained = d.get("total_trained", 0)
        return m


class DomainPCFG:
    """Domain-specific PCFG that auto-trains from sector vocabulary and corpora."""

    def __init__(self, sector: str = "generic", alpha: float = 0.1) -> None:
        self.model = DomainPCFGModel(sector=sector, alpha=alpha)
        self._rng = random.Random()

    def train(self, passwords: list[str], weight: float = 1.0) -> None:
        for pw in passwords:
            self._train_one(pw, weight)

    def train_sector_vocab(self) -> None:
        """Auto-seed from built-in domain vocabulary."""
        vocab = _sector_vocab(self.model.sector)
        seed_pws = []
        for word in vocab:
            seed_pws.append(word)
            seed_pws.append(word.capitalize())
            seed_pws.append(word + "123")
            seed_pws.append(word + "!")
            seed_pws.append(word + "2024")
            seed_pws.append(word + "2025")
        self.train(seed_pws, weight=0.5)

    def train_from_profile(self, profile: dict) -> None:
        """Extract seeds from a user/target profile."""
        seeds = []
        name = profile.get("full_name", "") or profile.get("short_name", "")
        if name:
            for part in re.split(r"\s+", name):
                if part:
                    seeds.append(part.lower())
                    seeds.append(part.capitalize())
        for kw in profile.get("keywords", []):
            seeds.append(str(kw))
        for pet in profile.get("pets", []) if isinstance(profile.get("pets"), list) else []:
            seeds.append(str(pet))
        for date in profile.get("special_dates", []):
            seeds.append(str(date).replace("-", ""))
        self.train(seeds, weight=2.0)

    def _train_one(self, pw: str, weight: float = 1.0) -> None:
        segs = _tokenize(pw)
        struct = "".join(f"{t}{len(v)}" for t, v in segs)
        self.model.structure_counts[struct] = self.model.structure_counts.get(struct, 0.0) + weight
        for seg_type, value in segs:
            key = f"{seg_type}{len(value)}"
            d = self.model.segment_counts[key]
            d[value] = d.get(value, 0.0) + weight
        self.model.total_trained += 1

    def _sample_structure(self) -> Optional[str]:
        d = self.model.structure_counts
        if not d:
            return None
        keys = list(d.keys())
        weights = [v + self.model.alpha for v in d.values()]
        return self._rng.choices(keys, weights=weights)[0]

    def _sample_segment(self, seg_type: str, length: int) -> str:
        key = f"{seg_type}{length}"
        d = self.model.segment_counts.get(key, {})
        if d:
            keys = list(d.keys())
            weights = [v + self.model.alpha for v in d.values()]
            return self._rng.choices(keys, weights=weights)[0]
        # fallback: random chars of appropriate class
        if seg_type == "A":
            chars = "abcdefghijklmnopqrstuvwxyz"
        elif seg_type == "D":
            chars = "0123456789"
        else:
            chars = "!@#$%^&*()_+-="
        return "".join(self._rng.choices(chars, k=length))

    def sample(self) -> Optional[str]:
        struct = self._sample_structure()
        if not struct:
            return None
        parts = re.findall(r"([ADS])(\d+)", struct)
        segments = []
        for seg_type, length_str in parts:
            segments.append(self._sample_segment(seg_type, int(length_str)))
        return "".join(segments)

    def prob(self, pw: str) -> float:
        segs = _tokenize(pw)
        struct = "".join(f"{t}{len(v)}" for t, v in segs)
        total_struct = sum(self.model.structure_counts.values()) or 1.0
        p_struct = (self.model.structure_counts.get(struct, 0.0) + self.model.alpha) / (
            total_struct + self.model.alpha * max(len(self.model.structure_counts), 1)
        )
        log_p = math.log(p_struct + 1e-30)
        for seg_type, value in segs:
            key = f"{seg_type}{len(value)}"
            d = self.model.segment_counts.get(key, {})
            total_seg = sum(d.values()) or 1.0
            p_seg = (d.get(value, 0.0) + self.model.alpha) / (
                total_seg + self.model.alpha * max(len(d), 1)
            )
            log_p += math.log(p_seg + 1e-30)
        return max(0.0, min(1.0, (log_p + 50) / 40.0))

    def generate(
        self,
        profile: Optional[dict] = None,
        corpus: Optional[list[str]] = None,
        max_candidates: int = 100_000,
        min_len: int = 4,
        max_len: int = 32,
    ) -> Generator[tuple[str, float], None, None]:
        self.train_sector_vocab()
        if profile:
            self.train_from_profile(profile)
        if corpus:
            self.train(corpus)

        yielded: set[str] = set()
        count = 0
        attempts = 0

        while count < max_candidates:
            attempts += 1
            if attempts > max_candidates * 5:
                break
            pw = self.sample()
            if pw is None or len(pw) < min_len or len(pw) > max_len:
                continue
            if pw in yielded:
                continue
            yielded.add(pw)
            yield (pw, self.prob(pw))
            count += 1

    def save(self, path: str) -> None:
        Path(path).write_text(json.dumps(self.model.to_dict()), encoding="utf-8")

    def load(self, path: str) -> bool:
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            self.model = DomainPCFGModel.from_dict(d)
            return True
        except Exception:
            return False

    def describe(self) -> str:
        n_struct = len(self.model.structure_counts)
        n_segs = sum(len(v) for v in self.model.segment_counts.values())
        top = sorted(self.model.structure_counts.items(), key=lambda x: -x[1])[:5]
        lines = [
            f"DomainPCFG [{self.model.sector}]  "
            f"{self.model.total_trained} trained  "
            f"{n_struct} structures  {n_segs} segments",
            "  Top structures: " + ", ".join(f"{s}({c:.0f})" for s, c in top),
        ]
        return "\n".join(lines)

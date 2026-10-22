"""
cpf_cnpj_gen.py: Gerador de CPFs e CNPJs validos para wordlists de auditoria.

Gera documentos com digitos verificadores corretos (algoritmo modulo 11),
com suporte a selecao de regiao fiscal (9o digito do CPF), multiplos
algoritmos de geracao (incluindo CogPIE como default), modos interativo
e CLI, e estimativa de tamanho de arquivo.

Uso defensivo: gerados para testes de politicas de senha, auditoria de
credenciais e avaliacao de conformidade. Nao utilizar para fraude ou
falsificacao documental.

Autor: Andre Henrique (@mrhenrike) | Uniao Geek
Versao: 1.0.0
"""
from __future__ import annotations

import argparse
import logging
import random
from collections.abc import Generator, Sequence
from typing import Any

logger = logging.getLogger(__name__)

__info__: dict[str, Any] = {
    "name": "cpf_cnpj_gen",
    "version": "1.0.0",
    "description": "Gerador de CPFs e CNPJs validos para wordlists de auditoria de senhas",
    "author": "Andre Henrique (@mrhenrike) | Uniao Geek",
    "category": "generation",
    "tags": ["cpf", "cnpj", "brazil", "document", "password", "audit"],
}

# ── Region map ───────────────────────────────────────────────────────────────

REGION_DIGIT_STATES: dict[int, list[str]] = {
    0: ["RS"],
    1: ["DF", "GO", "MS", "MT", "TO"],
    2: ["AC", "AM", "AP", "PA", "RO", "RR"],
    3: ["CE", "MA", "PI"],
    4: ["AL", "PB", "PE", "RN"],
    5: ["BA", "SE"],
    6: ["MG"],
    7: ["ES", "RJ"],
    8: ["SP"],
    9: ["PR", "SC"],
}

REGION_MAP: dict[str, int] = {}
for _digit, _states in REGION_DIGIT_STATES.items():
    for _state in _states:
        REGION_MAP[_state] = _digit

ALGORITHMS: list[str] = [
    "cogpie",
    "sequential",
    "random",
    "weighted_random",
    "markov_prefix",
    "pcfg_pattern",
]

_INVALID_SAME_DIGIT_CPFS: set[str] = {str(d) * 11 for d in range(10)}

# ── Check digit computation ──────────────────────────────────────────────────


def _cpf_check_digits(base9: list[int]) -> tuple[int, int]:
    """Compute CPF check digits from first 9 digits using mod-11."""
    weights1 = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    s1 = sum(d * w for d, w in zip(base9, weights1))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1

    weights2 = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    extended = base9 + [d1]
    s2 = sum(d * w for d, w in zip(extended, weights2))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2

    return d1, d2


def _cnpj_check_digits(base12: list[int]) -> tuple[int, int]:
    """Compute CNPJ check digits from first 12 digits using mod-11."""
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s1 = sum(d * w for d, w in zip(base12, weights1))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1

    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    extended = base12 + [d1]
    s2 = sum(d * w for d, w in zip(extended, weights2))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2

    return d1, d2


def validate_cpf(cpf: str) -> bool:
    """Validate a CPF string (11 digits, no formatting)."""
    digits_only = "".join(c for c in cpf if c.isdigit())
    if len(digits_only) != 11:
        return False
    if digits_only in _INVALID_SAME_DIGIT_CPFS:
        return False
    base = [int(c) for c in digits_only[:9]]
    d1, d2 = _cpf_check_digits(base)
    return int(digits_only[9]) == d1 and int(digits_only[10]) == d2


def validate_cnpj(cnpj: str) -> bool:
    """Validate a CNPJ string (14 digits, no formatting)."""
    digits_only = "".join(c for c in cnpj if c.isdigit())
    if len(digits_only) != 14:
        return False
    if len(set(digits_only)) == 1:
        return False
    base = [int(c) for c in digits_only[:12]]
    d1, d2 = _cnpj_check_digits(base)
    return int(digits_only[12]) == d1 and int(digits_only[13]) == d2


# ── Formatting ───────────────────────────────────────────────────────────────


def format_cpf(digits: str) -> str:
    """Format 11-digit CPF as XXX.XXX.XXX-XX."""
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def format_cnpj(digits: str) -> str:
    """Format 14-digit CNPJ as XX.XXX.XXX/XXXX-XX."""
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


# ── Size estimation ──────────────────────────────────────────────────────────


def estimate_file_size(count: int, doc_type: str, fmt: str) -> str:
    """Estimate output file size in human-readable form."""
    if doc_type == "cpf":
        chars_plain = 11
        chars_formatted = 14  # XXX.XXX.XXX-XX
    else:
        chars_plain = 14
        chars_formatted = 18  # XX.XXX.XXX/XXXX-XX

    if fmt == "both":
        line_len = chars_plain + 1 + chars_formatted + 1  # tab separator + newline
    elif fmt == "formatted":
        line_len = chars_formatted + 1
    else:
        line_len = chars_plain + 1

    total_bytes = count * line_len
    if total_bytes < 1024:
        return f"~{total_bytes} B"
    if total_bytes < 1024 * 1024:
        return f"~{total_bytes / 1024:.1f} KB"
    return f"~{total_bytes / (1024 * 1024):.1f} MB"


# ── Generation algorithms ────────────────────────────────────────────────────


def _make_cpf(base9: list[int]) -> str:
    """Build a valid 11-digit CPF string from 9 base digits."""
    d1, d2 = _cpf_check_digits(base9)
    return "".join(str(d) for d in base9) + str(d1) + str(d2)


def _make_cnpj(base8: list[int], branch: int = 1) -> str:
    """Build a valid 14-digit CNPJ string from 8 base digits + branch."""
    branch_digits = [int(c) for c in f"{branch:04d}"]
    base12 = base8 + branch_digits
    d1, d2 = _cnpj_check_digits(base12)
    return "".join(str(d) for d in base12) + str(d1) + str(d2)


def _gen_cpf_random(
    rng: random.Random,
    region: int | None,
) -> str:
    """Generate a single random valid CPF."""
    while True:
        base = [rng.randint(0, 9) for _ in range(9)]
        if region is not None:
            base[8] = region
        cpf = _make_cpf(base)
        if cpf not in _INVALID_SAME_DIGIT_CPFS:
            return cpf


def _gen_cpf_sequential(
    start: int,
    region: int | None,
) -> Generator[str, None, None]:
    """Generate CPFs sequentially from a starting 8-digit prefix."""
    prefix = start
    while prefix < 100_000_000:
        for r in ([region] if region is not None else range(10)):
            base = [int(c) for c in f"{prefix:08d}"] + [r]
            cpf = _make_cpf(base)
            if cpf not in _INVALID_SAME_DIGIT_CPFS:
                yield cpf
        prefix += 1


def _gen_cpf_cogpie(
    rng: random.Random,
    region: int | None,
) -> str:
    """Generate CPF using CogPIE cognitive bias patterns.

    Models common human tendencies: repeated digits, ascending/descending
    sequences, date-like patterns, personally meaningful number clusters.
    """
    pattern = rng.choices(
        ["repeated", "ascending", "date_embed", "cluster", "mixed"],
        weights=[25, 15, 30, 15, 15],
        k=1,
    )[0]

    if pattern == "repeated":
        d = rng.randint(0, 9)
        base = [d] * 8
        count = rng.randint(3, 6)
        positions = rng.sample(range(8), min(count, 8))
        for p in positions:
            base[p] = d
        for i in range(8):
            if i not in positions:
                base[i] = rng.randint(0, 9)
    elif pattern == "ascending":
        start_d = rng.randint(0, 5)
        base = [(start_d + i) % 10 for i in range(8)]
    elif pattern == "date_embed":
        year = rng.randint(1960, 2010)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        date_str = f"{day:02d}{month:02d}{year % 100:02d}"
        base = [int(c) for c in date_str[:8]]
    elif pattern == "cluster":
        segments = []
        for _ in range(3):
            d = rng.randint(0, 9)
            seg_len = rng.choice([2, 3])
            segments.extend([d] * seg_len)
        base = segments[:8]
    else:
        base = [rng.randint(0, 9) for _ in range(8)]

    while len(base) < 8:
        base.append(rng.randint(0, 9))
    base = base[:8]

    r = region if region is not None else rng.randint(0, 9)
    full_base = base + [r]
    cpf = _make_cpf(full_base)
    if cpf in _INVALID_SAME_DIGIT_CPFS:
        full_base[0] = (full_base[0] + 1) % 10
        cpf = _make_cpf(full_base)
    return cpf


def _gen_cpf_weighted_random(
    rng: random.Random,
    region: int | None,
) -> str:
    """Generate CPF with weighted random: favor repeated and sequential digits."""
    weights_per_digit = [1.0] * 10
    prev = rng.randint(0, 9)
    base: list[int] = [prev]

    for _ in range(7):
        w = list(weights_per_digit)
        w[prev] *= 3.0  # favor repetition
        if prev < 9:
            w[prev + 1] *= 2.0  # favor ascending
        if prev > 0:
            w[prev - 1] *= 1.5  # slight favor descending
        total = sum(w)
        probs = [x / total for x in w]
        chosen = rng.choices(range(10), weights=probs, k=1)[0]
        base.append(chosen)
        prev = chosen

    r = region if region is not None else rng.randint(0, 9)
    full_base = base + [r]
    cpf = _make_cpf(full_base)
    if cpf in _INVALID_SAME_DIGIT_CPFS:
        full_base[rng.randint(0, 7)] = (full_base[rng.randint(0, 7)] + 1) % 10
        cpf = _make_cpf(full_base)
    return cpf


_MARKOV_TRANSITIONS: dict[int, list[tuple[int, float]]] = {
    0: [(0, 0.20), (1, 0.15), (2, 0.10), (3, 0.10), (4, 0.08), (5, 0.08), (6, 0.07), (7, 0.07), (8, 0.08), (9, 0.07)],
    1: [(0, 0.10), (1, 0.18), (2, 0.15), (3, 0.12), (4, 0.10), (5, 0.08), (6, 0.07), (7, 0.07), (8, 0.07), (9, 0.06)],
    2: [(0, 0.10), (1, 0.12), (2, 0.16), (3, 0.14), (4, 0.10), (5, 0.09), (6, 0.08), (7, 0.07), (8, 0.07), (9, 0.07)],
    3: [(0, 0.09), (1, 0.10), (2, 0.12), (3, 0.16), (4, 0.12), (5, 0.10), (6, 0.08), (7, 0.08), (8, 0.08), (9, 0.07)],
    4: [(0, 0.08), (1, 0.09), (2, 0.10), (3, 0.11), (4, 0.15), (5, 0.12), (6, 0.10), (7, 0.09), (8, 0.08), (9, 0.08)],
    5: [(0, 0.08), (1, 0.08), (2, 0.09), (3, 0.10), (4, 0.11), (5, 0.15), (6, 0.12), (7, 0.10), (8, 0.09), (9, 0.08)],
    6: [(0, 0.07), (1, 0.07), (2, 0.08), (3, 0.09), (4, 0.10), (5, 0.11), (6, 0.16), (7, 0.12), (8, 0.10), (9, 0.10)],
    7: [(0, 0.07), (1, 0.07), (2, 0.07), (3, 0.08), (4, 0.09), (5, 0.10), (6, 0.11), (7, 0.16), (8, 0.13), (9, 0.12)],
    8: [(0, 0.07), (1, 0.07), (2, 0.07), (3, 0.08), (4, 0.08), (5, 0.09), (6, 0.10), (7, 0.12), (8, 0.17), (9, 0.15)],
    9: [(0, 0.08), (1, 0.07), (2, 0.07), (3, 0.07), (4, 0.08), (5, 0.08), (6, 0.09), (7, 0.11), (8, 0.15), (9, 0.20)],
}


def _gen_cpf_markov(
    rng: random.Random,
    region: int | None,
) -> str:
    """Generate CPF using Markov chain digit transitions."""
    first = rng.randint(0, 9)
    base: list[int] = [first]
    current = first

    for _ in range(7):
        transitions = _MARKOV_TRANSITIONS[current]
        digits, probs = zip(*transitions)
        chosen = rng.choices(list(digits), weights=list(probs), k=1)[0]
        base.append(chosen)
        current = chosen

    r = region if region is not None else rng.randint(0, 9)
    full_base = base + [r]
    cpf = _make_cpf(full_base)
    if cpf in _INVALID_SAME_DIGIT_CPFS:
        full_base[0] = (full_base[0] + 1) % 10
        cpf = _make_cpf(full_base)
    return cpf


_PCFG_CPF_PATTERNS: list[tuple[str, float]] = [
    ("DDMMYYNN", 0.25),   # date of birth + region
    ("NNDDMMYY", 0.15),   # number prefix + date
    ("RRRNNNNR", 0.15),   # repeated + numbers + repeated
    ("AABBCCDD", 0.10),   # pairs of digits
    ("NNNNNNN0", 0.10),   # sequential-like ending in zero
    ("12345678", 0.05),   # ascending
    ("98765432", 0.05),   # descending
    ("RNRNRNRN", 0.15),   # alternating repeated and random
]


def _expand_pcfg_cpf(pattern: str, rng: random.Random) -> list[int]:
    """Expand a PCFG pattern string into 8 base digits."""
    result: list[int] = []
    year = rng.randint(1960, 2010)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    r_digit = rng.randint(0, 9)
    n_digit = rng.randint(0, 9)
    a_digit = rng.randint(0, 9)
    b_digit = rng.randint(0, 9)
    c_digit = rng.randint(0, 9)

    date_digits = [int(c) for c in f"{day:02d}{month:02d}{year % 100:02d}"]

    mapping: dict[str, int] = {
        "D": -1, "M": -1, "Y": -1,
        "N": n_digit, "R": r_digit,
        "A": a_digit, "B": b_digit, "C": c_digit,
    }

    date_idx = 0
    for ch in pattern:
        if ch in ("D", "M", "Y") and date_idx < len(date_digits):
            result.append(date_digits[date_idx])
            date_idx += 1
        elif ch.isdigit():
            result.append(int(ch))
        elif ch in mapping:
            result.append(mapping[ch])
        else:
            result.append(rng.randint(0, 9))

    return result[:8]


def _gen_cpf_pcfg(
    rng: random.Random,
    region: int | None,
) -> str:
    """Generate CPF using PCFG structural patterns."""
    patterns, weights = zip(*_PCFG_CPF_PATTERNS)
    chosen = rng.choices(list(patterns), weights=list(weights), k=1)[0]
    base = _expand_pcfg_cpf(chosen, rng)

    r = region if region is not None else rng.randint(0, 9)
    full_base = base + [r]
    cpf = _make_cpf(full_base)
    if cpf in _INVALID_SAME_DIGIT_CPFS:
        full_base[rng.randint(0, 7)] = (full_base[rng.randint(0, 7)] + 1) % 10
        cpf = _make_cpf(full_base)
    return cpf


# ── CNPJ generation algorithms ──────────────────────────────────────────────


def _gen_cnpj_random(rng: random.Random, branch: int = 1) -> str:
    """Generate a random valid CNPJ."""
    base8 = [rng.randint(0, 9) for _ in range(8)]
    cnpj = _make_cnpj(base8, branch)
    while len(set(cnpj)) == 1:
        base8 = [rng.randint(0, 9) for _ in range(8)]
        cnpj = _make_cnpj(base8, branch)
    return cnpj


def _gen_cnpj_sequential(start: int, branch: int = 1) -> Generator[str, None, None]:
    """Generate CNPJs sequentially from a starting 8-digit prefix."""
    prefix = start
    while prefix < 100_000_000:
        base8 = [int(c) for c in f"{prefix:08d}"]
        cnpj = _make_cnpj(base8, branch)
        if len(set(cnpj)) > 1:
            yield cnpj
        prefix += 1


def _gen_cnpj_cogpie(rng: random.Random, branch: int = 1) -> str:
    """Generate CNPJ using CogPIE cognitive bias patterns."""
    pattern = rng.choices(
        ["repeated_pairs", "ascending_root", "round_numbers", "date_root", "mixed"],
        weights=[20, 15, 25, 25, 15],
        k=1,
    )[0]

    if pattern == "repeated_pairs":
        a, b = rng.randint(0, 9), rng.randint(0, 9)
        base8 = [a, b] * 4
    elif pattern == "ascending_root":
        s = rng.randint(1, 5)
        base8 = [(s + i) % 10 for i in range(8)]
    elif pattern == "round_numbers":
        lead = rng.randint(1, 9)
        base8 = [lead] + [0] * 7
        for i in rng.sample(range(1, 8), rng.randint(1, 3)):
            base8[i] = rng.randint(1, 9)
    elif pattern == "date_root":
        year = rng.randint(1990, 2026)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        ds = f"{day:02d}{month:02d}{year:04d}"
        base8 = [int(c) for c in ds[:8]]
    else:
        base8 = [rng.randint(0, 9) for _ in range(8)]

    cnpj = _make_cnpj(base8, branch)
    if len(set(cnpj)) == 1:
        base8[0] = (base8[0] + 1) % 10
        cnpj = _make_cnpj(base8, branch)
    return cnpj


def _gen_cnpj_weighted(rng: random.Random, branch: int = 1) -> str:
    """Generate CNPJ with weighted random digit selection."""
    prev = rng.randint(0, 9)
    base8: list[int] = [prev]
    for _ in range(7):
        w = [1.0] * 10
        w[prev] *= 3.0
        if prev < 9:
            w[prev + 1] *= 2.0
        total = sum(w)
        probs = [x / total for x in w]
        chosen = rng.choices(range(10), weights=probs, k=1)[0]
        base8.append(chosen)
        prev = chosen
    cnpj = _make_cnpj(base8, branch)
    if len(set(cnpj)) == 1:
        base8[0] = (base8[0] + 1) % 10
        cnpj = _make_cnpj(base8, branch)
    return cnpj


def _gen_cnpj_markov(rng: random.Random, branch: int = 1) -> str:
    """Generate CNPJ using Markov chain digit transitions."""
    first = rng.randint(0, 9)
    base8: list[int] = [first]
    current = first
    for _ in range(7):
        transitions = _MARKOV_TRANSITIONS[current]
        digits, probs = zip(*transitions)
        chosen = rng.choices(list(digits), weights=list(probs), k=1)[0]
        base8.append(chosen)
        current = chosen
    cnpj = _make_cnpj(base8, branch)
    if len(set(cnpj)) == 1:
        base8[0] = (base8[0] + 1) % 10
        cnpj = _make_cnpj(base8, branch)
    return cnpj


def _gen_cnpj_pcfg(rng: random.Random, branch: int = 1) -> str:
    """Generate CNPJ using PCFG structural patterns."""
    patterns = [
        ([1, 2, 3, 4, 5, 6, 7, 8], 0.1),
        ([rng.randint(1, 9)] + [0] * 7, 0.3),
    ]
    year = rng.randint(1990, 2026)
    patterns.append(([int(c) for c in f"{year:04d}{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}"], 0.3))
    d = rng.randint(1, 9)
    patterns.append(([d, d, d, d, rng.randint(0, 9), rng.randint(0, 9), rng.randint(0, 9), rng.randint(0, 9)], 0.3))

    bases, weights = zip(*patterns)
    base8 = list(rng.choices(list(bases), weights=list(weights), k=1)[0])
    cnpj = _make_cnpj(base8, branch)
    if len(set(cnpj)) == 1:
        base8[0] = (base8[0] + 1) % 10
        cnpj = _make_cnpj(base8, branch)
    return cnpj


# ── Unified generation interface ─────────────────────────────────────────────


def resolve_region(value: str | int | None) -> int | None:
    """Resolve region from digit, state abbreviation, or None (all regions)."""
    if value is None:
        return None
    if isinstance(value, int):
        if not 0 <= value <= 9:
            raise ValueError(f"Digito de regiao deve ser 0-9, recebido: {value}")
        return value
    value_str = str(value).strip().upper()
    if value_str in ("ALL", "TODAS", ""):
        return None
    if value_str.isdigit() and len(value_str) == 1:
        return int(value_str)
    if value_str in REGION_MAP:
        return REGION_MAP[value_str]
    raise ValueError(
        f"Regiao invalida: {value!r}. "
        f"Use digito 0-9, sigla de estado ({', '.join(sorted(REGION_MAP))}), ou 'all'."
    )


def generate_cpfs(
    count: int,
    *,
    region: int | None = None,
    algorithm: str = "cogpie",
    seed: int | None = None,
) -> Generator[str, None, None]:
    """Generate valid CPFs using the specified algorithm."""
    if count < 1:
        raise ValueError("count deve ser >= 1")
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Algoritmo invalido: {algorithm!r}. Disponiveis: {ALGORITHMS}")

    rng = random.Random(seed)

    if algorithm == "sequential":
        start = rng.randint(0, 50_000_000)
        gen = _gen_cpf_sequential(start, region)
        for _, cpf in zip(range(count), gen):
            yield cpf
        return

    gen_func: dict[str, Any] = {
        "cogpie": _gen_cpf_cogpie,
        "random": _gen_cpf_random,
        "weighted_random": _gen_cpf_weighted_random,
        "markov_prefix": _gen_cpf_markov,
        "pcfg_pattern": _gen_cpf_pcfg,
    }
    func = gen_func[algorithm]
    seen: set[str] = set()
    attempts = 0
    max_attempts = count * 20

    while len(seen) < count and attempts < max_attempts:
        attempts += 1
        cpf = func(rng, region)
        if cpf not in seen:
            seen.add(cpf)
            yield cpf


def generate_cnpjs(
    count: int,
    *,
    branch: int = 1,
    algorithm: str = "cogpie",
    seed: int | None = None,
) -> Generator[str, None, None]:
    """Generate valid CNPJs using the specified algorithm."""
    if count < 1:
        raise ValueError("count deve ser >= 1")
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Algoritmo invalido: {algorithm!r}. Disponiveis: {ALGORITHMS}")
    if not 1 <= branch <= 9999:
        raise ValueError("branch deve ser 1-9999")

    rng = random.Random(seed)

    if algorithm == "sequential":
        start = rng.randint(0, 50_000_000)
        gen = _gen_cnpj_sequential(start, branch)
        for _, cnpj in zip(range(count), gen):
            yield cnpj
        return

    gen_func: dict[str, Any] = {
        "cogpie": _gen_cnpj_cogpie,
        "random": _gen_cnpj_random,
        "weighted_random": _gen_cnpj_weighted,
        "markov_prefix": _gen_cnpj_markov,
        "pcfg_pattern": _gen_cnpj_pcfg,
    }
    func = gen_func[algorithm]
    seen: set[str] = set()
    attempts = 0
    max_attempts = count * 20

    while len(seen) < count and attempts < max_attempts:
        attempts += 1
        cnpj = func(rng, branch)
        if cnpj not in seen:
            seen.add(cnpj)
            yield cnpj


# ── Output helpers ───────────────────────────────────────────────────────────


def format_output(value: str, doc_type: str, fmt: str) -> str:
    """Format a document number for output."""
    if doc_type == "cpf":
        if fmt == "formatted":
            return format_cpf(value)
        if fmt == "both":
            return f"{value}\t{format_cpf(value)}"
        return value
    else:
        if fmt == "formatted":
            return format_cnpj(value)
        if fmt == "both":
            return f"{value}\t{format_cnpj(value)}"
        return value


def write_output(
    values: Generator[str, None, None],
    doc_type: str,
    fmt: str,
    output_path: str | None,
) -> list[str]:
    """Write generated values to file or collect to list."""
    results: list[str] = []
    if output_path:
        with open(output_path, "w", encoding="utf-8") as fh:
            for val in values:
                line = format_output(val, doc_type, fmt)
                fh.write(line + "\n")
                results.append(val)
    else:
        for val in values:
            results.append(val)
    return results


# ── Interactive wizard ───────────────────────────────────────────────────────


def _input_safe(prompt: str) -> str:
    """Wrapper for input() to support non-interactive environments."""
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def interactive_wizard() -> dict[str, Any]:
    """Run the interactive CPF/CNPJ generation wizard.

    Returns a dict with all chosen parameters.
    """
    print("\n=== Gerador de CPF/CNPJ para Wordlists ===\n")

    doc_type = ""
    while doc_type not in ("cpf", "cnpj"):
        doc_type = _input_safe("Tipo de documento [cpf/cnpj]: ").lower()

    count_str = _input_safe("Quantidade a gerar: ")
    try:
        count = int(count_str)
        if count < 1:
            raise ValueError
    except ValueError:
        print("Quantidade invalida. Usando 100.")
        count = 100

    size_est = estimate_file_size(count, doc_type, "plain")
    print(f"\nEstimativa: {count} {doc_type.upper()}s = {size_est}")

    region: int | None = None
    if doc_type == "cpf":
        print("\nRegioes fiscais (9o digito do CPF):")
        for digit, states in sorted(REGION_DIGIT_STATES.items()):
            print(f"  {digit}: {', '.join(states)}")
        print("  all: todas as regioes")
        region_input = _input_safe("\nRegiao [0-9, sigla do estado, ou all]: ")
        try:
            region = resolve_region(region_input if region_input else None)
        except ValueError as e:
            print(f"  {e}. Usando todas as regioes.")
            region = None

    branch = 1
    if doc_type == "cnpj":
        branch_input = _input_safe("Filial [1=matriz, 2-9999=filial, default=1]: ")
        if branch_input.isdigit():
            branch = max(1, min(9999, int(branch_input)))

    print("\nAlgoritmos disponiveis:")
    for i, algo in enumerate(ALGORITHMS):
        default_tag = " (default)" if algo == "cogpie" else ""
        print(f"  {i + 1}. {algo}{default_tag}")
    algo_input = _input_safe("\nAlgoritmo [nome ou numero, default=cogpie]: ")
    algorithm = "cogpie"
    if algo_input:
        if algo_input.isdigit():
            idx = int(algo_input) - 1
            if 0 <= idx < len(ALGORITHMS):
                algorithm = ALGORITHMS[idx]
        elif algo_input.lower() in ALGORITHMS:
            algorithm = algo_input.lower()

    fmt_input = _input_safe("Formato de saida [plain/formatted/both, default=plain]: ").lower()
    fmt = fmt_input if fmt_input in ("plain", "formatted", "both") else "plain"

    output_path = _input_safe("Arquivo de saida (Enter para stdout): ")

    size_est_final = estimate_file_size(count, doc_type, fmt)
    print("\nResumo:")
    print(f"  Tipo: {doc_type.upper()}")
    print(f"  Quantidade: {count}")
    if doc_type == "cpf":
        region_label = f"digito {region}" if region is not None else "todas"
        states = REGION_DIGIT_STATES.get(region, []) if region is not None else []
        if states:
            region_label += f" ({', '.join(states)})"
        print(f"  Regiao: {region_label}")
    else:
        print(f"  Filial: {branch}")
    print(f"  Algoritmo: {algorithm}")
    print(f"  Formato: {fmt}")
    print(f"  Tamanho estimado: {size_est_final}")
    if output_path:
        print(f"  Arquivo: {output_path}")

    confirm = _input_safe("\nConfirmar geracao? [S/n]: ").lower()
    if confirm in ("n", "no", "nao"):
        print("Operacao cancelada.")
        return {"cancelled": True}

    return {
        "doc_type": doc_type,
        "count": count,
        "region": region,
        "branch": branch,
        "algorithm": algorithm,
        "format": fmt,
        "output": output_path or None,
        "cancelled": False,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for CLI mode."""
    parser = argparse.ArgumentParser(
        prog="wlf cpf-cnpj",
        description="Gerador de CPFs e CNPJs validos para wordlists de auditoria",
    )
    parser.add_argument(
        "--type", "-t",
        choices=["cpf", "cnpj"],
        help="Tipo de documento (obrigatorio no modo CLI)",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=100,
        help="Quantidade a gerar (default: 100)",
    )
    parser.add_argument(
        "--region", "-r",
        default=None,
        help="Regiao fiscal do CPF: digito 0-9, sigla UF, ou 'all' (default: all)",
    )
    parser.add_argument(
        "--branch",
        type=int,
        default=1,
        help="Filial do CNPJ: 1=matriz (default: 1)",
    )
    parser.add_argument(
        "--algorithm", "-a",
        choices=ALGORITHMS,
        default="cogpie",
        help="Algoritmo de geracao (default: cogpie)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["plain", "formatted", "both"],
        default="plain",
        dest="fmt",
        help="Formato de saida (default: plain)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Arquivo de saida (default: stdout)",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Seed para reproducibilidade",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Modo interativo (wizard)",
    )
    parser.add_argument(
        "--estimate",
        action="store_true",
        help="Apenas estimar tamanho sem gerar",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.interactive:
        params = interactive_wizard()
        if params.get("cancelled"):
            return 0
        doc_type = params["doc_type"]
        count = params["count"]
        region = params["region"]
        branch = params["branch"]
        algorithm = params["algorithm"]
        fmt = params["format"]
        output_path = params["output"]
        seed = None
    else:
        if not args.type:
            parser.error("--type e obrigatorio no modo nao-interativo")
        doc_type = args.type
        count = args.count
        try:
            region = resolve_region(args.region)
        except ValueError as e:
            parser.error(str(e))
            return 1  # unreachable, but needed for type checker
        branch = args.branch
        algorithm = args.algorithm
        fmt = args.fmt
        output_path = args.output
        seed = args.seed

    if args.estimate:
        est = estimate_file_size(count, doc_type, fmt)
        print(f"{count} {doc_type.upper()}s ({fmt}): {est}")
        return 0

    if doc_type == "cpf":
        gen = generate_cpfs(count, region=region, algorithm=algorithm, seed=seed)
    else:
        gen = generate_cnpjs(count, branch=branch, algorithm=algorithm, seed=seed)

    if output_path:
        written = write_output(gen, doc_type, fmt, output_path)
        print(f"Gerados {len(written)} {doc_type.upper()}s em {output_path}")
    else:
        for val in gen:
            print(format_output(val, doc_type, fmt))

    return 0


# ── WLF module contract ─────────────────────────────────────────────────────


def run(
    doc_type: str = "cpf",
    count: int = 100,
    region: str | int | None = None,
    algorithm: str = "cogpie",
    fmt: str = "plain",
    seed: int | None = None,
    branch: int = 1,
) -> list[str]:
    """WLF standard run() interface.

    Returns a list of generated document strings.
    """
    resolved_region = resolve_region(region)

    if doc_type == "cpf":
        gen = generate_cpfs(count, region=resolved_region, algorithm=algorithm, seed=seed)
    elif doc_type == "cnpj":
        gen = generate_cnpjs(count, branch=branch, algorithm=algorithm, seed=seed)
    else:
        raise ValueError(f"doc_type invalido: {doc_type!r}. Use 'cpf' ou 'cnpj'.")

    results: list[str] = []
    for val in gen:
        results.append(format_output(val, doc_type, fmt))
    return results


if __name__ == "__main__":
    raise SystemExit(main())

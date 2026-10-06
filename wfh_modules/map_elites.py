"""map_elites.py - MAP-Elites quality-diversity algorithm for password generation.

Maintains a grid of "elite" candidates across a behaviour space:
  Dimension 1: password length (6-20)
  Dimension 2: charset diversity (0-4: only_lower, mixed_alpha, alpha+digit, all_classes)
  Dimension 3: entropy band (low/medium/high/very_high)

For each cell in the grid, the algorithm keeps the highest-fitness individual.
Fitness = statistical probability score (Markov+PCFG combined), or 0.5 if models unavailable.

Generation: select a random elite, apply a mutation operator, evaluate fitness,
update the grid if the child beats the current elite in that cell.

Optional LLM-guided mutation (requires ollama/llama.cpp API).

References:
  Mouret & Clune "Illuminating search spaces by mapping elites" (2015)
  arXiv 2604.12601 MAP-Elites + LLM (2026)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import math
import random
import string
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Optional


# ── Behaviour descriptor ──────────────────────────────────────────────────────

def _entropy(pw: str) -> float:
    if not pw:
        return 0.0
    freq = Counter(pw)
    n = len(pw)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def _charset_band(pw: str) -> int:
    lower  = any(c.islower() for c in pw)
    upper  = any(c.isupper() for c in pw)
    digit  = any(c.isdigit() for c in pw)
    special = any(c in string.punctuation for c in pw)
    return sum([lower or upper, lower and upper, digit, special])


def _entropy_band(ent: float) -> int:
    if ent < 2.5:
        return 0
    if ent < 3.3:
        return 1
    if ent < 4.2:
        return 2
    return 3


def behaviour_descriptor(pw: str) -> tuple[int, int, int]:
    """(length_bin, charset_band, entropy_band)"""
    length_bin = max(0, min(len(pw) - 6, 14))  # 0-14 for lengths 6-20
    return (length_bin, _charset_band(pw), _entropy_band(_entropy(pw)))


# ── Mutation operators ────────────────────────────────────────────────────────

_SPECIALS = "!@#$%^&*()_+-="
_LOWER = string.ascii_lowercase
_UPPER = string.ascii_uppercase
_DIGITS = string.digits

_ALL_CHARS = _LOWER + _UPPER + _DIGITS + _SPECIALS


def _mutate_substitute(pw: str, rng: random.Random) -> str:
    if not pw:
        return pw
    pos = rng.randint(0, len(pw) - 1)
    new_c = rng.choice(_ALL_CHARS)
    return pw[:pos] + new_c + pw[pos+1:]


def _mutate_insert(pw: str, rng: random.Random) -> str:
    pos = rng.randint(0, len(pw))
    new_c = rng.choice(_ALL_CHARS)
    return pw[:pos] + new_c + pw[pos:]


def _mutate_delete(pw: str, rng: random.Random) -> str:
    if len(pw) <= 4:
        return pw
    pos = rng.randint(0, len(pw) - 1)
    return pw[:pos] + pw[pos+1:]


def _mutate_leet(pw: str, rng: random.Random) -> str:
    TABLE = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$", "t": "7"}
    chars = list(pw)
    for i, c in enumerate(chars):
        if c.lower() in TABLE and rng.random() < 0.5:
            chars[i] = TABLE[c.lower()]
    return "".join(chars)


def _mutate_capitalise(pw: str, rng: random.Random) -> str:
    if not pw:
        return pw
    pos = rng.randint(0, len(pw) - 1)
    c = pw[pos]
    swapped = c.upper() if c.islower() else c.lower()
    return pw[:pos] + swapped + pw[pos+1:]


def _mutate_append_year(pw: str, rng: random.Random) -> str:
    year = str(rng.randint(2019, 2027))
    if rng.random() < 0.5:
        return pw + year
    sep = rng.choice(["@", "#", "_", "!", ""])
    return pw + sep + year[-2:]


def _mutate_append_special(pw: str, rng: random.Random) -> str:
    return pw + rng.choice(list(_SPECIALS))


_OPERATORS = [
    _mutate_substitute,
    _mutate_insert,
    _mutate_delete,
    _mutate_leet,
    _mutate_capitalise,
    _mutate_append_year,
    _mutate_append_special,
]


def _crossover(pw_a: str, pw_b: str, rng: random.Random) -> str:
    if not pw_a or not pw_b:
        return pw_a or pw_b
    cut = rng.randint(1, max(min(len(pw_a), len(pw_b)) - 1, 1))
    return pw_a[:cut] + pw_b[cut:]


# ── Fitness function ──────────────────────────────────────────────────────────

def _default_fitness(pw: str) -> float:
    """Heuristic fitness when no probabilistic model is available."""
    if not pw or len(pw) < 4:
        return 0.0
    score = min(len(pw), 16) / 16.0
    score += 0.1 * _charset_band(pw) / 4.0
    score += 0.1 * _entropy(pw) / 5.0
    return min(score, 1.0)


# ── MAP-Elites grid ───────────────────────────────────────────────────────────

@dataclass
class Elite:
    password: str
    fitness: float
    descriptor: tuple[int, int, int]


class MAPElites:
    """MAP-Elites quality-diversity grid for passwords.

    Grid shape: 15 (lengths 6-20) × 5 (charset bands 0-4) × 4 (entropy bands)
    """

    GRID_SHAPE = (15, 5, 4)

    def __init__(
        self,
        fitness_fn: Optional[Callable[[str], float]] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.fitness_fn = fitness_fn or _default_fitness
        self.rng = random.Random(seed)
        self.grid: dict[tuple[int,int,int], Elite] = {}
        self._all_elites: list[str] = []

    @property
    def n_filled(self) -> int:
        return len(self.grid)

    def add(self, pw: str) -> bool:
        """Try to add a password to the grid. Returns True if it improved a cell."""
        desc = behaviour_descriptor(pw)
        fit = self.fitness_fn(pw)
        existing = self.grid.get(desc)
        if existing is None or fit > existing.fitness:
            self.grid[desc] = Elite(pw, fit, desc)
            if pw not in self._all_elites:
                self._all_elites.append(pw)
            return True
        return False

    def seed_population(self, passwords: list[str]) -> int:
        """Seed the grid with an initial population."""
        count = 0
        for pw in passwords:
            if self.add(pw):
                count += 1
        return count

    def _select_elite(self) -> Optional[str]:
        if not self.grid:
            return None
        return self.rng.choice(list(self.grid.values())).password

    def evolve_step(self) -> Optional[str]:
        """One MAP-Elites step: select → mutate → evaluate → insert."""
        parent = self._select_elite()
        if parent is None:
            return None
        if self.rng.random() < 0.1 and len(self.grid) >= 2:
            p2 = self._select_elite()
            child = _crossover(parent, p2 or parent, self.rng)
        else:
            op = self.rng.choice(_OPERATORS)
            child = op(parent, self.rng)
        if not child or len(child) < 4 or len(child) > 64:
            return None
        self.add(child)
        return child

    def generate(
        self,
        seed_passwords: Optional[list[str]] = None,
        max_candidates: int = 50_000,
        warmup_steps: int = 5_000,
    ) -> Generator[tuple[str, float], None, None]:
        """Yield (password, fitness) from MAP-Elites evolution."""
        # seed phase
        if seed_passwords:
            self.seed_population(seed_passwords)
        else:
            # generate random seeds
            pool = _ALL_CHARS
            for _ in range(min(500, max_candidates)):
                length = self.rng.randint(6, 16)
                pw = "".join(self.rng.choices(pool, k=length))
                self.add(pw)

        # warmup
        for _ in range(warmup_steps):
            self.evolve_step()

        # harvest
        yielded: set[str] = set()
        count = 0
        while not max_candidates or count < max_candidates:
            child = self.evolve_step()
            if child and child not in yielded:
                yielded.add(child)
                desc = behaviour_descriptor(child)
                elite = self.grid.get(desc)
                fit = elite.fitness if elite else 0.5
                yield (child, fit)
                count += 1
            elif len(yielded) >= 100_000:
                break

    def describe(self) -> str:
        total = sum(self.GRID_SHAPE[0] * self.GRID_SHAPE[1] * self.GRID_SHAPE[2] for _ in [1])
        pct = 100 * self.n_filled / max(total, 1)
        lines = [f"MAP-Elites grid: {self.n_filled}/{total} cells filled ({pct:.1f}%)"]
        if self.grid:
            best = max(self.grid.values(), key=lambda e: e.fitness)
            lines.append(f"Best elite: {best.password!r} fitness={best.fitness:.3f} @{best.descriptor}")
        return "\n".join(lines)

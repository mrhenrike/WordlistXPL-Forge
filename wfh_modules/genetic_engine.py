"""genetic_engine.py - Genetic Algorithm engine for password generation.

Classic GA with tournament selection, uniform crossover, and a suite of
password-specific mutation operators.  Fitness is Markov-based log-probability
when a model is available, otherwise a heuristic charset/entropy score.

Implements:
  - Population initialization (seeded + random)
  - Tournament selection (k=3)
  - Uniform crossover (50% gene exchange)
  - Mutation operators: substitution, insertion, deletion, leet, append, swap
  - Elitism: top-N individuals always survive
  - Multi-objective mode: Pareto-dominance on (fitness, diversity)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import math
import random
import string
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Generator, Optional


# ── Fitness helpers ───────────────────────────────────────────────────────────

_SPECIALS = "!@#$%^&*()_+-="
_ALL_CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits + _SPECIALS


def _entropy(pw: str) -> float:
    if not pw:
        return 0.0
    freq = Counter(pw)
    n = len(pw)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def _charset_score(pw: str) -> float:
    classes = [
        any(c.islower() for c in pw),
        any(c.isupper() for c in pw),
        any(c.isdigit() for c in pw),
        any(c in _SPECIALS for c in pw),
    ]
    return sum(classes) / 4.0


def heuristic_fitness(pw: str) -> float:
    if not pw or len(pw) < 4:
        return 0.0
    len_score = min(len(pw), 20) / 20.0
    ent_score = min(_entropy(pw) / 5.0, 1.0)
    cs_score = _charset_score(pw)
    return 0.5 * len_score + 0.3 * ent_score + 0.2 * cs_score


# ── Mutation operators ────────────────────────────────────────────────────────

def _mut_substitute(pw: str, rng: random.Random) -> str:
    if not pw:
        return pw
    pos = rng.randint(0, len(pw) - 1)
    return pw[:pos] + rng.choice(_ALL_CHARS) + pw[pos+1:]


def _mut_insert(pw: str, rng: random.Random) -> str:
    pos = rng.randint(0, len(pw))
    return pw[:pos] + rng.choice(_ALL_CHARS) + pw[pos:]


def _mut_delete(pw: str, rng: random.Random) -> str:
    if len(pw) <= 4:
        return pw
    pos = rng.randint(0, len(pw) - 1)
    return pw[:pos] + pw[pos+1:]


def _mut_swap(pw: str, rng: random.Random) -> str:
    if len(pw) < 2:
        return pw
    i = rng.randint(0, len(pw) - 2)
    lst = list(pw)
    lst[i], lst[i+1] = lst[i+1], lst[i]
    return "".join(lst)


def _mut_leet(pw: str, rng: random.Random) -> str:
    TABLE = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$", "t": "7", "l": "1"}
    chars = list(pw)
    for i, c in enumerate(chars):
        if c.lower() in TABLE and rng.random() < 0.4:
            chars[i] = TABLE[c.lower()]
    return "".join(chars)


def _mut_append(pw: str, rng: random.Random) -> str:
    suffix = rng.choice([
        str(rng.randint(0, 99)),
        str(rng.randint(2010, 2027)),
        rng.choice(list(_SPECIALS)),
        rng.choice(["!", "123", "1", "@"]),
    ])
    return pw + suffix


def _mut_prepend(pw: str, rng: random.Random) -> str:
    prefix = rng.choice([rng.choice(list(_SPECIALS)), str(rng.randint(1, 9))])
    return prefix + pw


def _mut_capitalise_first(pw: str, rng: random.Random) -> str:
    if not pw:
        return pw
    return pw[0].upper() + pw[1:]


_MUTATIONS = [
    (_mut_substitute,       0.30),
    (_mut_leet,             0.20),
    (_mut_append,           0.15),
    (_mut_insert,           0.10),
    (_mut_delete,           0.08),
    (_mut_swap,             0.07),
    (_mut_capitalise_first, 0.05),
    (_mut_prepend,          0.05),
]
_MUTATION_CDF = []
_acc = 0.0
for _fn, _w in _MUTATIONS:
    _acc += _w
    _MUTATION_CDF.append((_acc, _fn))


def _pick_mutation(rng: random.Random):
    r = rng.random()
    for threshold, fn in _MUTATION_CDF:
        if r <= threshold:
            return fn
    return _MUTATION_CDF[-1][1]


# ── Crossover ─────────────────────────────────────────────────────────────────

def _uniform_crossover(pw_a: str, pw_b: str, rng: random.Random) -> str:
    if not pw_a:
        return pw_b
    if not pw_b:
        return pw_a
    length = rng.randint(
        min(len(pw_a), len(pw_b)),
        max(len(pw_a), len(pw_b)),
    )
    child = []
    for i in range(length):
        if i < len(pw_a) and i < len(pw_b):
            child.append(pw_a[i] if rng.random() < 0.5 else pw_b[i])
        elif i < len(pw_a):
            child.append(pw_a[i])
        else:
            child.append(pw_b[i])
    return "".join(child)


def _two_point_crossover(pw_a: str, pw_b: str, rng: random.Random) -> str:
    n = min(len(pw_a), len(pw_b))
    if n < 3:
        return pw_a if rng.random() < 0.5 else pw_b
    p1, p2 = sorted(rng.sample(range(1, n), 2))
    return pw_a[:p1] + pw_b[p1:p2] + pw_a[p2:]


# ── Individual ────────────────────────────────────────────────────────────────

@dataclass
class Individual:
    password: str
    fitness: float = 0.0

    def __lt__(self, other: "Individual") -> bool:
        return self.fitness < other.fitness


# ── Genetic engine ────────────────────────────────────────────────────────────

class GeneticPasswordEngine:
    """GA-based password generator.

    Args:
        fitness_fn:     Optional external fitness function (markov, pcfg, etc.)
        population_size: Number of individuals per generation.
        elitism:        Number of top individuals to carry over unchanged.
        mutation_rate:  Per-individual mutation probability.
        crossover_rate: Per-pair crossover probability.
        seed:           RNG seed for reproducibility.
    """

    def __init__(
        self,
        fitness_fn: Optional[Callable[[str], float]] = None,
        population_size: int = 500,
        elitism: int = 20,
        mutation_rate: float = 0.85,
        crossover_rate: float = 0.70,
        seed: Optional[int] = None,
        min_len: int = 6,
        max_len: int = 20,
    ) -> None:
        self.fitness_fn = fitness_fn or heuristic_fitness
        self.pop_size = population_size
        self.elitism = elitism
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.rng = random.Random(seed)
        self.min_len = min_len
        self.max_len = max_len
        self.population: list[Individual] = []
        self.generation: int = 0

    def _random_individual(self) -> Individual:
        length = self.rng.randint(self.min_len, self.max_len)
        pw = "".join(self.rng.choices(_ALL_CHARS, k=length))
        return Individual(pw)

    def initialize(self, seed_passwords: Optional[list[str]] = None) -> None:
        self.population = []
        if seed_passwords:
            for pw in seed_passwords[: self.pop_size]:
                ind = Individual(pw)
                ind.fitness = self.fitness_fn(pw)
                self.population.append(ind)
        while len(self.population) < self.pop_size:
            ind = self._random_individual()
            ind.fitness = self.fitness_fn(ind.password)
            self.population.append(ind)
        self.population.sort(reverse=True)

    def _tournament_select(self, k: int = 3) -> Individual:
        candidates = self.rng.choices(self.population, k=k)
        return max(candidates, key=lambda i: i.fitness)

    def _step(self) -> list[Individual]:
        # elites survive unchanged
        new_pop = self.population[: self.elitism]

        while len(new_pop) < self.pop_size:
            parent_a = self._tournament_select()

            if self.rng.random() < self.crossover_rate:
                parent_b = self._tournament_select()
                if self.rng.random() < 0.5:
                    child_pw = _uniform_crossover(parent_a.password, parent_b.password, self.rng)
                else:
                    child_pw = _two_point_crossover(parent_a.password, parent_b.password, self.rng)
            else:
                child_pw = parent_a.password

            if self.rng.random() < self.mutation_rate:
                mut = _pick_mutation(self.rng)
                child_pw = mut(child_pw, self.rng)

            if not child_pw or len(child_pw) < 4 or len(child_pw) > 64:
                continue

            child = Individual(child_pw, self.fitness_fn(child_pw))
            new_pop.append(child)

        new_pop.sort(reverse=True)
        self.generation += 1
        return new_pop

    def evolve(self, generations: int = 1) -> None:
        for _ in range(generations):
            self.population = self._step()

    def generate(
        self,
        seed_passwords: Optional[list[str]] = None,
        max_candidates: int = 50_000,
        warmup_generations: int = 20,
    ) -> Generator[tuple[str, float], None, None]:
        """Yield (password, fitness) from GA evolution."""
        self.initialize(seed_passwords)
        self.evolve(warmup_generations)

        yielded: set[str] = set()
        count = 0

        while not max_candidates or count < max_candidates:
            self.population = self._step()
            for ind in self.population:
                if ind.password not in yielded:
                    yielded.add(ind.password)
                    yield (ind.password, ind.fitness)
                    count += 1
                    if max_candidates and count >= max_candidates:
                        return
            if len(yielded) > 500_000:
                break

    def describe(self) -> str:
        if not self.population:
            return "GeneticPasswordEngine — not initialized"
        best = self.population[0]
        avg = sum(i.fitness for i in self.population) / max(len(self.population), 1)
        return (
            f"GA gen={self.generation} pop={len(self.population)}\n"
            f"  Best : {best.password!r} fit={best.fitness:.3f}\n"
            f"  Mean : {avg:.3f}"
        )

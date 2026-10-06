"""bandit_router.py - Multi-Armed Bandit over generation engines (UCB1).

Arms: markov, pcfg, prince, rules, pattern. Rewards come from sampled
replay hits or synthetic coverage proxies. Selects which engine to run next.

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional


DEFAULT_ARMS = ("markov", "pcfg", "prince", "rules", "pattern")


@dataclass
class ArmStats:
    pulls: int = 0
    reward_sum: float = 0.0

    @property
    def mean(self) -> float:
        return self.reward_sum / self.pulls if self.pulls else 0.0


@dataclass
class BanditRouter:
    arms: tuple[str, ...] = DEFAULT_ARMS
    c: float = 1.414  # UCB exploration constant
    rng: random.Random = field(default_factory=random.Random)
    stats: dict[str, ArmStats] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for a in self.arms:
            self.stats.setdefault(a, ArmStats())

    @property
    def total_pulls(self) -> int:
        return sum(s.pulls for s in self.stats.values())

    def select(self) -> str:
        """UCB1 arm selection."""
        t = self.total_pulls + 1
        # pull each arm at least once
        for a in self.arms:
            if self.stats[a].pulls == 0:
                return a
        best_a, best_score = self.arms[0], -1e18
        for a in self.arms:
            s = self.stats[a]
            bonus = self.c * math.sqrt(math.log(t) / s.pulls)
            score = s.mean + bonus
            if score > best_score:
                best_score, best_a = score, a
        return best_a

    def update(self, arm: str, reward: float) -> None:
        st = self.stats.setdefault(arm, ArmStats())
        st.pulls += 1
        st.reward_sum += reward

    def describe(self) -> str:
        lines = ["=== Bandit arms (UCB1) ==="]
        for a in self.arms:
            s = self.stats[a]
            lines.append(f"  {a:10s} pulls={s.pulls:4d} mean={s.mean:.4f}")
        return "\n".join(lines)


def proxy_reward(candidates: list[str], seeds: list[str]) -> float:
    """Cheap reward: fraction of candidates that share a seed substring."""
    if not candidates:
        return 0.0
    if not seeds:
        # entropy proxy — prefer moderate length + specials
        score = 0.0
        for c in candidates[:500]:
            score += min(len(c), 16) / 16.0
            if any(ch in c for ch in "@#_!"):
                score += 0.2
        return score / max(len(candidates[:500]), 1)
    hits = 0
    low_seeds = [s.lower() for s in seeds if s]
    for c in candidates[:1000]:
        cl = c.lower()
        if any(s in cl for s in low_seeds):
            hits += 1
    return hits / max(len(candidates[:1000]), 1)

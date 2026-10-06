"""pbmp_full.py - Full Probabilistic Behavioral Mutation Predictor.

Implements the complete PBMP model:

    P(Strategy_{t+1} | History, Context, Behavior, Population)

Where:
  History    = [(strategy, coverage_delta, entropy_gain), …]  — past generation batches
  Context    = profile YAML + policy constraints + sector + vocabulary
  Behavior   = corpus statistics + temporal drift (patterns 2015→2026)
  Population = DNA fingerprint + coverage map + charset distribution

Replaces the PBMP-lite in strategy_engine.py with a full online-learning
model. Uses a lightweight gradient-boosted model (or linear model) that
trains incrementally as generation proceeds.

The reward signal is coverage_delta: how many statistically distinct
candidates did this batch introduce relative to the known distribution?

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import math
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


STRATEGIES = (
    "rules_mangle",
    "mask_cartesian",
    "markov_omen",
    "pcfg_structure",
    "semantic_pcfg",
    "prince_chains",
    "pattern_templates",
    "neural_lstm",
    "gan_engine",
    "vae_engine",
    "transformer_engine",
    "diffusion_engine",
    "masked_lm",
    "br_deep",
    "map_elites",
    "genetic_engine",
)

_N_STRATEGIES = len(STRATEGIES)


@dataclass
class BatchRecord:
    strategy: str
    timestamp: float
    coverage_delta: float   # fraction of new/unique structural patterns
    entropy_gain: float     # mean entropy increase over batch
    n_generated: int
    mean_length: float
    charset_diversity: float  # 0-1, fraction of charset classes present


@dataclass
class CorpusBehavior:
    """Running statistics of the generated population."""
    structure_counts: Counter = field(default_factory=Counter)
    length_dist: Counter = field(default_factory=Counter)
    charset_usage: dict[str, float] = field(default_factory=dict)
    total_seen: int = 0
    temporal_drift_score: float = 0.0

    def update(self, candidates: list[str]) -> None:
        for pw in candidates:
            self.total_seen += 1
            self.length_dist[len(pw)] += 1
            template = _structure_template(pw)
            self.structure_counts[template] += 1
        self._update_charset(candidates)

    def _update_charset(self, candidates: list[str]) -> None:
        total = max(len(candidates), 1)
        self.charset_usage = {
            "lower":   sum(1 for pw in candidates if any(c.islower() for c in pw)) / total,
            "upper":   sum(1 for pw in candidates if any(c.isupper() for c in pw)) / total,
            "digit":   sum(1 for pw in candidates if any(c.isdigit() for c in pw)) / total,
            "special": sum(1 for pw in candidates if any(c in "!@#$%^&*()_+-=" for c in pw)) / total,
        }

    def coverage_of(self, candidates: list[str]) -> float:
        """Fraction of candidates with structure templates not yet seen."""
        if not candidates or not self.structure_counts:
            return 1.0
        new = sum(1 for pw in candidates if _structure_template(pw) not in self.structure_counts)
        return new / len(candidates)


def _structure_template(pw: str) -> str:
    """Compact structural signature: e.g. L6D2S1."""
    parts = []
    i = 0
    while i < len(pw):
        c = pw[i]
        if c.isalpha():
            j = i
            while j < len(pw) and pw[j].isalpha():
                j += 1
            parts.append(f"A{j-i}")
            i = j
        elif c.isdigit():
            j = i
            while j < len(pw) and pw[j].isdigit():
                j += 1
            parts.append(f"D{j-i}")
            i = j
        else:
            j = i
            while j < len(pw) and not pw[j].isalnum():
                j += 1
            parts.append(f"S{j-i}")
            i = j
    return "".join(parts)


def _extract_context_features(profile: dict, sector: Optional[str] = None) -> list[float]:
    """Convert profile + sector into a numeric feature vector."""
    has_name      = 1.0 if profile.get("full_name") or profile.get("short_name") else 0.0
    has_pet       = 1.0 if profile.get("pets") else 0.0
    has_company   = 1.0 if profile.get("company_name") else 0.0
    has_dates     = 1.0 if profile.get("special_dates") else 0.0
    has_keywords  = 1.0 if profile.get("keywords") else 0.0
    depth         = min(float(profile.get("depth", 3)) / 5.0, 1.0)
    is_corp       = 1.0 if sector in ("corporate","bank","gov","finance") else 0.0
    is_br         = 1.0 if profile.get("country","").lower() in ("br","brazil","brasil") else 0.0
    return [has_name, has_pet, has_company, has_dates, has_keywords, depth, is_corp, is_br]


def _softmax(logits: list[float]) -> list[float]:
    m = max(logits)
    exp = [math.exp(x - m) for x in logits]
    z = sum(exp) or 1.0
    return [e / z for e in exp]


class PBMPModel:
    """Lightweight online linear model over strategy features.

    State = context_features + history_features + population_features
    Action = distribution over STRATEGIES
    Learning = gradient step on coverage_delta reward.
    """

    def __init__(self, n_features: int = 32, lr: float = 0.05) -> None:
        self._n = n_features
        self._lr = lr
        self._W: list[list[float]] = [
            [0.0] * n_features for _ in range(_N_STRATEGIES)
        ]
        self._b: list[float] = [0.0] * _N_STRATEGIES

    def _featurize(
        self,
        context_feat: list[float],
        history: deque[BatchRecord],
        behavior: CorpusBehavior,
    ) -> list[float]:
        hist_feats = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if history:
            last = history[-1]
            hist_feats[0] = last.coverage_delta
            hist_feats[1] = last.entropy_gain
            hist_feats[2] = last.charset_diversity
            hist_feats[3] = last.mean_length / 20.0
        if len(history) >= 2:
            prev = list(history)[-2]
            hist_feats[4] = prev.coverage_delta
            hist_feats[5] = prev.entropy_gain

        strat_freq = Counter(r.strategy for r in history)
        top_strat = strat_freq.most_common(1)[0][0] if strat_freq else STRATEGIES[0]
        hist_feats[6] = STRATEGIES.index(top_strat) / _N_STRATEGIES if top_strat in STRATEGIES else 0.0
        hist_feats[7] = len(history) / 50.0

        pop_feats = [
            behavior.charset_usage.get("lower", 0.0),
            behavior.charset_usage.get("upper", 0.0),
            behavior.charset_usage.get("digit", 0.0),
            behavior.charset_usage.get("special", 0.0),
            min(behavior.total_seen / 1_000_000, 1.0),
            behavior.temporal_drift_score,
        ]

        # pad/truncate to n_features
        raw = (context_feat + hist_feats + pop_feats)[:self._n]
        while len(raw) < self._n:
            raw.append(0.0)
        return raw

    def predict(
        self,
        context_feat: list[float],
        history: deque[BatchRecord],
        behavior: CorpusBehavior,
    ) -> dict[str, float]:
        feat = self._featurize(context_feat, history, behavior)
        logits = [
            self._b[i] + sum(self._W[i][j] * feat[j] for j in range(self._n))
            for i in range(_N_STRATEGIES)
        ]
        probs = _softmax(logits)
        return {STRATEGIES[i]: probs[i] for i in range(_N_STRATEGIES)}

    def update(
        self,
        strategy: str,
        reward: float,
        context_feat: list[float],
        history: deque[BatchRecord],
        behavior: CorpusBehavior,
    ) -> None:
        if strategy not in STRATEGIES:
            return
        idx = STRATEGIES.index(strategy)
        feat = self._featurize(context_feat, history, behavior)
        probs = list(self.predict(context_feat, history, behavior).values())
        # policy gradient: ∇log π(a|s) * R
        grad = reward * (1.0 - probs[idx])
        for j in range(self._n):
            self._W[idx][j] += self._lr * grad * feat[j]
        self._b[idx] += self._lr * grad

    def save(self, path: str) -> None:
        Path(path).write_text(
            json.dumps({"W": self._W, "b": self._b, "n": self._n, "lr": self._lr}),
            encoding="utf-8",
        )

    def load(self, path: str) -> bool:
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            self._W = d["W"]
            self._b = d["b"]
            self._n = d.get("n", self._n)
            self._lr = d.get("lr", self._lr)
            return True
        except Exception:
            return False


class PBMPFull:
    """Full PBMP controller — maintains state, selects strategies, learns."""

    def __init__(
        self,
        profile: Optional[dict] = None,
        sector: Optional[str] = None,
        model_path: Optional[str] = None,
        history_window: int = 50,
        lr: float = 0.05,
    ) -> None:
        self.profile = profile or {}
        self.sector = sector
        self.history: deque[BatchRecord] = deque(maxlen=history_window)
        self.behavior = CorpusBehavior()
        self.model = PBMPModel(lr=lr)
        self._context_feat = _extract_context_features(self.profile, sector)
        if model_path and Path(model_path).exists():
            self.model.load(model_path)

    def select_strategy(self) -> tuple[str, dict[str, float]]:
        """Select the best strategy and return (name, weight_dict)."""
        weights = self.model.predict(self._context_feat, self.history, self.behavior)
        best = max(weights, key=weights.get)  # type: ignore[arg-type]
        return best, weights

    def record_batch(
        self,
        strategy: str,
        candidates: list[str],
    ) -> float:
        """Record results of a generation batch; return coverage_delta reward."""
        if not candidates:
            return 0.0
        coverage_delta = self.behavior.coverage_of(candidates)
        self.behavior.update(candidates)

        entropies = []
        for pw in candidates[:500]:
            if not pw:
                continue
            freq = Counter(pw)
            n = len(pw)
            e = -sum((c / n) * math.log2(c / n) for c in freq.values())
            entropies.append(e)
        entropy_gain = sum(entropies) / max(len(entropies), 1)
        mean_len = sum(len(pw) for pw in candidates) / max(len(candidates), 1)
        cs = sum(1 for pw in candidates if any(c.isupper() for c in pw)) / max(len(candidates), 1)

        record = BatchRecord(
            strategy=strategy,
            timestamp=time.time(),
            coverage_delta=coverage_delta,
            entropy_gain=entropy_gain,
            n_generated=len(candidates),
            mean_length=mean_len,
            charset_diversity=cs,
        )
        self.history.append(record)
        self.model.update(strategy, coverage_delta, self._context_feat, self.history, self.behavior)
        return coverage_delta

    def plan(self, n_engines: int = 5) -> list[dict[str, Any]]:
        """Return an ordered list of engine specs for the next pipeline."""
        _, weights = self.select_strategy()
        ranked = sorted(weights.items(), key=lambda x: -x[1])
        result = []
        for name, w in ranked[:n_engines]:
            if w < 0.03:
                continue
            result.append({
                "strategy": name,
                "weight": round(w, 4),
                "limit": max(1_000, int(50_000 * w)),
            })
        return result

    def describe(self) -> str:
        _, weights = self.select_strategy()
        lines = ["=== PBMP Full — strategy distribution ==="]
        for name, w in sorted(weights.items(), key=lambda x: -x[1])[:8]:
            bar = "█" * int(w * 30)
            lines.append(f"  {name:22s}  {w:.3f}  {bar}")
        lines.append(f"  History: {len(self.history)} batches | Population: {self.behavior.total_seen:,}")
        return "\n".join(lines)

    def save(self, path: str) -> None:
        self.model.save(path)

    def load(self, path: str) -> bool:
        return self.model.load(path)

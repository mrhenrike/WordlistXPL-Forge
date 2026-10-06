"""score_normalizer.py - Unified score normalization across heterogeneous generation engines.

Each engine emits candidates with a raw score on a different scale:
  Markov/OMEN  : integer cost   (lower = more probable, range 0-100+)
  PCFG         : log-probability (negative, higher = more probable)
  GAN          : discriminator   (higher = more real-like, 0.0-1.0)
  VAE          : log-likelihood  (higher = better, typically -100 to 0)
  Transformer  : log-perplexity  (lower = more probable, 0-20+)
  Semantic     : heuristic float (higher = better, 0.0-1.0)
  Bloom proxy  : coverage proxy  (higher = better, 0.0-1.0)

This module normalises all of them to [0.0, 1.0] where 1.0 = most probable,
allowing the async pipeline to merge streams by a single comparable score.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


# ── Score type registry ────────────────────────────────────────────────────────

SCORE_TYPE_COST       = "cost"         # lower is better (Markov/OMEN)
SCORE_TYPE_LOGPROB    = "logprob"      # negative, higher is better (PCFG)
SCORE_TYPE_PROB       = "prob"         # 0-1, higher is better
SCORE_TYPE_LOGLIK     = "loglik"       # negative float, higher is better (VAE)
SCORE_TYPE_PERPLEXITY = "perplexity"   # lower is better (Transformer)
SCORE_TYPE_HEURISTIC  = "heuristic"    # 0-1, higher is better


@dataclass
class EngineScoreSpec:
    score_type: str = SCORE_TYPE_HEURISTIC
    min_clip: Optional[float] = None
    max_clip: Optional[float] = None
    cost_scale: float = 100.0          # for COST type: typical max cost


_ENGINE_SPECS: dict[str, EngineScoreSpec] = {
    "markov":      EngineScoreSpec(SCORE_TYPE_COST,       min_clip=0.0, max_clip=200.0, cost_scale=200.0),
    "omen":        EngineScoreSpec(SCORE_TYPE_COST,       min_clip=0.0, max_clip=200.0, cost_scale=200.0),
    "pcfg":        EngineScoreSpec(SCORE_TYPE_LOGPROB,    min_clip=-50.0, max_clip=0.0),
    "semantic":    EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "gan":         EngineScoreSpec(SCORE_TYPE_PROB),
    "vae":         EngineScoreSpec(SCORE_TYPE_LOGLIK,     min_clip=-200.0, max_clip=0.0),
    "transformer": EngineScoreSpec(SCORE_TYPE_PERPLEXITY, min_clip=1.0, max_clip=2000.0),
    "diffusion":   EngineScoreSpec(SCORE_TYPE_PROB),
    "masked_lm":   EngineScoreSpec(SCORE_TYPE_PROB),
    "tcn":         EngineScoreSpec(SCORE_TYPE_LOGPROB,    min_clip=-50.0, max_clip=0.0),
    "flow":        EngineScoreSpec(SCORE_TYPE_LOGLIK,     min_clip=-200.0, max_clip=0.0),
    "rules":       EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "mask":        EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "prince":      EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "pattern":     EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "affix":       EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "keyword":     EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "genetic":     EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "map_elites":  EngineScoreSpec(SCORE_TYPE_HEURISTIC),
    "temporal":    EngineScoreSpec(SCORE_TYPE_PROB),
    "br_deep":     EngineScoreSpec(SCORE_TYPE_HEURISTIC),
}


def normalize(engine: str, raw_score: float) -> float:
    """Convert engine-specific raw score to [0.0, 1.0] unified probability.

    1.0 = most probable / highest quality candidate.
    """
    spec = _ENGINE_SPECS.get(engine, EngineScoreSpec())
    lo = spec.min_clip
    hi = spec.max_clip

    if spec.score_type == SCORE_TYPE_COST:
        # invert: lower cost → higher normalized score
        scale = spec.cost_scale or 200.0
        clamped = max(0.0, min(raw_score, scale))
        return 1.0 - (clamped / scale)

    if spec.score_type == SCORE_TYPE_LOGPROB:
        # logprob in [-inf, 0]; map to [0, 1]
        lo = lo if lo is not None else -50.0
        clamped = max(lo, min(0.0, raw_score))
        return 1.0 - abs(clamped) / abs(lo)

    if spec.score_type == SCORE_TYPE_LOGLIK:
        lo = lo if lo is not None else -200.0
        clamped = max(lo, min(0.0, raw_score))
        return 1.0 - abs(clamped) / abs(lo)

    if spec.score_type == SCORE_TYPE_PERPLEXITY:
        # lower perplexity = better; map via exp decay
        lo_p = lo if lo is not None else 1.0
        hi_p = hi if hi is not None else 2000.0
        clamped = max(lo_p, min(hi_p, raw_score))
        # sigmoid-like decay: score = exp(-ppl / scale)
        return math.exp(-clamped / (hi_p * 0.2))

    if spec.score_type == SCORE_TYPE_PROB:
        return max(0.0, min(1.0, raw_score))

    # HEURISTIC: already in [0,1] ideally, but clamp to be safe
    return max(0.0, min(1.0, float(raw_score)))


@dataclass
class RunningStats:
    """Welford online mean/variance for adaptive rescaling."""
    n: int = 0
    mean: float = 0.0
    M2: float = 0.0

    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self.M2 += delta * (x - self.mean)

    @property
    def variance(self) -> float:
        return self.M2 / (self.n - 1) if self.n > 1 else 1.0

    @property
    def std(self) -> float:
        return math.sqrt(max(self.variance, 1e-9))


@dataclass
class AdaptiveNormalizer:
    """Per-engine adaptive normalizer using online statistics.

    After warm-up (min_samples), uses z-score clamped to [-3, 3] to
    produce [0, 1] scores that are calibrated to the engine's actual output
    distribution rather than hard-coded clip bounds.
    """
    engine: str = "unknown"
    stats: RunningStats = field(default_factory=RunningStats)
    min_samples: int = 500

    def update_and_normalize(self, raw_score: float) -> float:
        self.stats.update(raw_score)
        if self.stats.n < self.min_samples:
            return normalize(self.engine, raw_score)
        z = (raw_score - self.stats.mean) / self.stats.std
        return max(0.0, min(1.0, (z + 3.0) / 6.0))


class MultiEngineNormalizer:
    """Registry of per-engine adaptive normalizers."""

    def __init__(self) -> None:
        self._normalizers: dict[str, AdaptiveNormalizer] = {}

    def score(self, engine: str, raw_score: float) -> float:
        if engine not in self._normalizers:
            self._normalizers[engine] = AdaptiveNormalizer(engine=engine)
        return self._normalizers[engine].update_and_normalize(raw_score)

    def baseline_score(self, engine: str) -> float:
        """Return the mean normalized score seen so far, or 0.5 for unseen engines."""
        if engine not in self._normalizers:
            return 0.5
        n = self._normalizers[engine]
        if n.stats.n < n.min_samples:
            return 0.5
        return normalize(engine, n.stats.mean)

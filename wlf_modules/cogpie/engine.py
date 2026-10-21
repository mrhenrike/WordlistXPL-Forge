"""
engine.py - CogPIE main engine: orchestrates all 5 layers.

Pipeline:
  Layer 1 (Semantic Expansion)  -> expanded token banks
  Layer 2 (Cognitive Transforms) -> raw candidate set
  Layer 3 (Probabilistic Ranking) -> scored candidates
  Layer 4 (Entropy Scoring)       -> guessability metadata
  Layer 5 (Policy Filtering)      -> final output

The engine accepts a target profile and optional training corpus,
then generates password candidates ordered by estimated probability.

Complexity analysis:
  Let N = |profile tokens|, E = avg expansion factor (Layer 1),
      T = avg transforms per token (Layer 2), K = output budget.
  - Layer 1: O(N * E) where E ~ 20-50 per token
  - Layer 2: O(N * E * T) where T ~ 100-200 per token
  - Layer 3: O(C * log C) where C = total candidates (scoring + sorting)
  - Layer 4: O(C) (linear scan)
  - Layer 5: O(C) (linear filter with CRC32 dedup)
  Total: O(N * E * T * log(N * E * T))

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import itertools
import logging
import time
from collections.abc import Generator
from typing import Any

from wlf_modules.cogpie.cognitive_transforms import (
    apply_capitalization,
    apply_leet_partial,
    apply_numeric_suffixes,
    apply_prefix_transforms,
    transform_pair,
    transform_token,
)
from wlf_modules.cogpie.markov_pcfg_hybrid import HybridRanker
from wlf_modules.cogpie.policy_filter import PasswordPolicy, filter_candidates
from wlf_modules.cogpie.scorer import practical_entropy, score_candidate
from wlf_modules.cogpie.semantic_expander import expand_date, expand_profile, expand_token

logger = logging.getLogger(__name__)


class CogPIEEngine:
    """Cognitive Pattern Inference Engine.

    Orchestrates the 5-layer pipeline for targeted password generation
    based on cognitive bias modeling.
    """

    def __init__(
        self,
        alpha: float = 0.4,
        beta: float = 0.2,
        markov_order: int = 3,
        max_pair_depth: int = 2,
    ) -> None:
        self.ranker = HybridRanker(alpha=alpha, beta=beta, markov_order=markov_order)
        self.max_pair_depth = max_pair_depth
        self._stats: dict[str, Any] = {}

    def train(self, corpus_path: str, max_lines: int = 0) -> int:
        """Train the probabilistic model from a password corpus file.

        Args:
            corpus_path: Path to newline-delimited password file.
            max_lines: Max lines to process (0 = unlimited).

        Returns:
            Number of passwords trained on.
        """
        count = self.ranker.train_from_file(corpus_path, max_lines)
        logger.info("Trained on %d passwords from %s", count, corpus_path)
        return count

    def generate(
        self,
        profile: dict[str, Any],
        policy: PasswordPolicy | None = None,
        max_candidates: int = 100_000,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Execute the full 5-layer pipeline.

        Args:
            profile: Target profile dict with keys:
                names, dates, keywords, pets, companies, phones,
                emails, old_passwords, numbers.
            policy: Target system password policy.
            max_candidates: Maximum candidates in final output.

        Returns:
            List of (candidate, metadata) tuples, sorted by probability.
        """
        t0 = time.monotonic()

        # Layer 1: Semantic Expansion
        banks = expand_profile(profile)
        all_tokens: set[str] = set()
        for category_tokens in banks.values():
            all_tokens.update(category_tokens)

        self._stats["layer1_tokens"] = len(all_tokens)
        self._stats["layer1_time"] = time.monotonic() - t0
        logger.info("Layer 1: %d expanded tokens", len(all_tokens))

        # Layer 2: Cognitive Transforms
        t1 = time.monotonic()
        raw_candidates: set[str] = set()

        for token in all_tokens:
            if len(token) < 2 or len(token) > 40:
                continue
            raw_candidates.update(transform_token(token))

        name_tokens = sorted(banks.get("names", set()), key=len, reverse=True)[:15]
        date_tokens = sorted(banks.get("dates", set()), key=len, reverse=True)[:10]
        kw_tokens = sorted(banks.get("keywords", set()), key=len, reverse=True)[:8]
        pet_tokens = sorted(banks.get("pets", set()), key=len, reverse=True)[:5]
        co_tokens = sorted(banks.get("companies", set()), key=len, reverse=True)[:5]

        for name_t in name_tokens:
            for date_t in date_tokens:
                raw_candidates.update(transform_pair(name_t, date_t))
            for kw_t in kw_tokens:
                raw_candidates.update(transform_pair(name_t, kw_t))
            for pet_t in pet_tokens:
                raw_candidates.update(transform_pair(name_t, pet_t))

        for kw_t in kw_tokens:
            for date_t in date_tokens:
                raw_candidates.update(transform_pair(kw_t, date_t))

        for pet_t in pet_tokens:
            for date_t in date_tokens:
                raw_candidates.update(transform_pair(pet_t, date_t))

        for co_t in co_tokens:
            for date_t in date_tokens:
                raw_candidates.update(transform_pair(co_t, date_t))

        for old_pw in banks.get("old_passwords", set()):
            raw_candidates.add(old_pw)
            raw_candidates.update(transform_token(old_pw))

        self._stats["layer2_candidates"] = len(raw_candidates)
        self._stats["layer2_time"] = time.monotonic() - t1
        logger.info("Layer 2: %d raw candidates", len(raw_candidates))

        # Layer 3: Probabilistic Ranking
        t2 = time.monotonic()
        candidate_list = list(raw_candidates)
        scored = self.ranker.rank(candidate_list)

        self._stats["layer3_time"] = time.monotonic() - t2
        logger.info("Layer 3: ranked %d candidates", len(scored))

        # Layer 4 + Layer 5: Score and Filter
        t3 = time.monotonic()
        results: list[tuple[str, dict[str, Any]]] = []
        for candidate, hybrid_score in filter_candidates(
            scored, policy=policy, max_candidates=max_candidates
        ):
            meta = score_candidate(candidate, hybrid_log_prob=hybrid_score)
            results.append((candidate, meta))

        self._stats["layer45_time"] = time.monotonic() - t3
        self._stats["total_time"] = time.monotonic() - t0
        self._stats["output_count"] = len(results)
        logger.info(
            "Pipeline complete: %d candidates in %.2fs",
            len(results),
            self._stats["total_time"],
        )

        return results

    def generate_stream(
        self,
        profile: dict[str, Any],
        policy: PasswordPolicy | None = None,
        max_candidates: int = 0,
    ) -> Generator[str, None, None]:
        """Stream-mode: yields candidates one at a time (password strings only).

        Useful for piping to hashcat or writing large wordlists.
        """
        results = self.generate(profile, policy, max_candidates or 500_000)
        for candidate, _ in results:
            yield candidate

    @property
    def stats(self) -> dict[str, Any]:
        return dict(self._stats)

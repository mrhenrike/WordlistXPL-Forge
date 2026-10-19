"""Fase 5 — BRDeepEngine tests (diminutives, verb conjugations)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.br_deep_engine import BRDeepEngine


class TestBRDeepEngine:
    def test_instantiate(self) -> None:
        eng = BRDeepEngine()
        assert eng is not None

    def test_generate_yields_tuples(self) -> None:
        eng = BRDeepEngine(profile={"first_name": "maria"})
        results = list(eng.generate(max_candidates=50))
        assert len(results) > 0
        for cand, score in results:
            assert isinstance(cand, str)
            assert isinstance(score, (int, float))

    def test_generate_respects_limit(self) -> None:
        eng = BRDeepEngine(profile={"first_name": "joao"})
        results = list(eng.generate(max_candidates=30))
        assert len(results) <= 30

    def test_empty_profile_still_generates(self) -> None:
        eng = BRDeepEngine()
        results = list(eng.generate(max_candidates=100))
        assert len(results) > 0

    def test_diminutives_present(self) -> None:
        eng = BRDeepEngine(profile={"first_name": "clara"})
        results = [c for c, _ in eng.generate(max_candidates=500)]
        has_dim = any("inha" in r or "inho" in r for r in results)
        assert has_dim, "Expected diminutive forms (inha/inho)"

    def test_no_empty_candidates(self) -> None:
        eng = BRDeepEngine(profile={"first_name": "pedro"})
        for cand, _ in eng.generate(max_candidates=100):
            assert cand.strip(), "Empty candidate generated"

    def test_scores_between_0_and_1(self) -> None:
        eng = BRDeepEngine(profile={"first_name": "ana"})
        for _, score in eng.generate(max_candidates=100):
            assert 0.0 <= score <= 1.0, f"Score out of range: {score}"

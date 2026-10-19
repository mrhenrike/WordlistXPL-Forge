"""Fase 5 — Locale engine tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.locales import (
    BaseLocaleEngine,
    LOCALE_REGISTRY,
    get_engine,
    list_locales,
)

EXPECTED_LOCALES = [
    "ar", "de", "en-gb", "en-us", "es", "fr", "hi", "ja", "ko", "pt-br", "pt-pt", "zh",
]


class TestLocaleRegistry:
    def test_all_12_locales_registered(self) -> None:
        codes = list_locales()
        for lc in EXPECTED_LOCALES:
            assert lc in codes, f"Missing locale: {lc}"

    def test_list_locales_returns_sorted(self) -> None:
        codes = list_locales()
        assert codes == sorted(codes)

    def test_get_engine_returns_instance(self) -> None:
        eng = get_engine("en-us")
        assert eng is not None
        assert isinstance(eng, BaseLocaleEngine)

    def test_get_engine_unknown_returns_none(self) -> None:
        eng = get_engine("xx-xx")
        assert eng is None

    def test_get_engine_case_insensitive(self) -> None:
        eng1 = get_engine("EN-US")
        eng2 = get_engine("en-us")
        assert eng1 is not None
        assert type(eng1) is type(eng2)


class TestLocaleEngineGenerate:
    @pytest.mark.parametrize("locale_code", EXPECTED_LOCALES)
    def test_engine_generates_output(self, locale_code: str) -> None:
        eng = get_engine(locale_code, max_candidates=50)
        assert eng is not None
        results = list(eng.generate())
        assert len(results) > 0, f"Locale {locale_code} produced nothing"

    @pytest.mark.parametrize("locale_code", EXPECTED_LOCALES)
    def test_engine_yields_tuples(self, locale_code: str) -> None:
        eng = get_engine(locale_code, max_candidates=10)
        assert eng is not None
        for item in eng.generate():
            assert isinstance(item, tuple), f"Expected tuple, got {type(item)}"
            assert len(item) == 2
            cand, score = item
            assert isinstance(cand, str)
            assert isinstance(score, (int, float))

    @pytest.mark.parametrize("locale_code", EXPECTED_LOCALES)
    def test_engine_respects_max_candidates(self, locale_code: str) -> None:
        limit = 25
        eng = get_engine(locale_code, max_candidates=limit)
        assert eng is not None
        results = list(eng.generate())
        assert len(results) <= limit, (
            f"Locale {locale_code}: expected <= {limit}, got {len(results)}"
        )

    @pytest.mark.parametrize("locale_code", EXPECTED_LOCALES)
    def test_engine_no_empty_candidates(self, locale_code: str) -> None:
        eng = get_engine(locale_code, max_candidates=50)
        assert eng is not None
        for cand, _ in eng.generate():
            assert cand.strip(), f"Empty candidate in {locale_code}"

    @pytest.mark.parametrize("locale_code", EXPECTED_LOCALES)
    def test_engine_has_locale_code(self, locale_code: str) -> None:
        eng = get_engine(locale_code)
        assert eng is not None
        assert eng.locale_code.lower() == locale_code

    @pytest.mark.parametrize("locale_code", EXPECTED_LOCALES)
    def test_engine_has_locale_name(self, locale_code: str) -> None:
        eng = get_engine(locale_code)
        assert eng is not None
        assert eng.locale_name, f"Missing locale_name for {locale_code}"


class TestEmitBlock:
    def test_emit_block_basic(self) -> None:
        eng = get_engine("en-us", max_candidates=1000)
        assert eng is not None
        seen: set[str] = set()
        count = [0]
        results = list(eng._emit_block(
            bases=["alice", "bob"],
            years=["2024"],
            suffixes=["!"],
            separators=[""],
            score=0.8,
            seen=seen,
            count=count,
        ))
        candidates = [r[0] for r in results]
        assert "alice" in candidates
        assert "bob" in candidates
        assert "alice2024" in candidates
        assert "alice!" in candidates

    def test_emit_block_deduplicates(self) -> None:
        eng = get_engine("en-us", max_candidates=1000)
        assert eng is not None
        seen: set[str] = set()
        count = [0]
        results = list(eng._emit_block(
            bases=["test", "test"],
            years=[],
            suffixes=[],
            separators=[],
            score=0.5,
            seen=seen,
            count=count,
        ))
        assert len(results) == 1

    def test_emit_block_respects_limit(self) -> None:
        eng = get_engine("en-us", max_candidates=3)
        assert eng is not None
        seen: set[str] = set()
        count = [0]
        results = list(eng._emit_block(
            bases=[f"w{i}" for i in range(100)],
            years=["2024"],
            suffixes=["!"],
            separators=[""],
            score=0.7,
            seen=seen,
            count=count,
        ))
        assert len(results) <= 3

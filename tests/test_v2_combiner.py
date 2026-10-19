"""Fase 5 — Combiner and theme/noun tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.combiner import combine_keywords
from wlf_modules.theme_packs import get_theme, list_themes
from wlf_modules.noun_dictionary import get_nouns, NOUNS_EN, NOUNS_PT


class TestCombiner:
    def test_basic_combination(self) -> None:
        results = list(combine_keywords(["alpha", "beta"]))
        assert "alpha" in results
        assert "beta" in results
        assert any("alpha" in r and "beta" in r for r in results)

    def test_fixed_suffix(self) -> None:
        results = list(combine_keywords(["test"], fixed_suffix="2024"))
        assert "test2024" in results

    def test_fixed_prefix(self) -> None:
        results = list(combine_keywords(["test"], fixed_prefix="pre_"))
        assert "pre_test" in results

    def test_max_depth_limits_output(self) -> None:
        r1 = list(combine_keywords(["a", "b", "c"], max_depth=1))
        r2 = list(combine_keywords(["a", "b", "c"], max_depth=3))
        assert len(r1) <= len(r2)

    def test_min_max_length_filter(self) -> None:
        results = list(combine_keywords(["ab", "cd"], min_length=4, max_length=6))
        for r in results:
            assert 4 <= len(r) <= 6

    def test_empty_keywords(self) -> None:
        results = list(combine_keywords([]))
        assert results == []

    def test_single_keyword(self) -> None:
        results = list(combine_keywords(["solo"]))
        assert "solo" in results

    def test_use_leet(self) -> None:
        count = 0
        for _ in combine_keywords(["password"], use_leet=True):
            count += 1
            if count >= 50:
                break
        assert count > 1

    def test_use_reverse(self) -> None:
        results = list(combine_keywords(["hello"], use_reverse=True))
        assert "olleh" in results


class TestThemePacks:
    def test_list_themes_not_empty(self) -> None:
        themes = list_themes()
        assert len(themes) > 0

    def test_get_gaming_theme(self) -> None:
        words = get_theme("gaming")
        assert words is not None
        assert len(words) > 0
        assert all(isinstance(w, str) for w in words)

    def test_get_unknown_theme_returns_empty(self) -> None:
        words = get_theme("nonexistent_theme_xyz")
        assert words is not None
        assert len(words) == 0


class TestNounDictionary:
    def test_nouns_en_is_list(self) -> None:
        assert isinstance(NOUNS_EN, list)
        assert len(NOUNS_EN) > 0

    def test_nouns_pt_is_list(self) -> None:
        assert isinstance(NOUNS_PT, list)

    def test_get_nouns_en_returns_list(self) -> None:
        result = get_nouns("en")
        assert isinstance(result, list)

    def test_get_nouns_pt_returns_list(self) -> None:
        result = get_nouns("pt")
        assert isinstance(result, list)

    def test_get_unknown_lang_returns_empty(self) -> None:
        result = get_nouns("nonexistent_xyz")
        assert result == []

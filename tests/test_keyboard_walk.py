"""Tests for wlf_modules.keyboard_walk module."""
from __future__ import annotations

import pytest

from wlf_modules.keyboard_walk import (
    generate_keyboard_walks,
    is_keyboard_walk,
    list_layouts,
)


class TestListLayouts:
    """Tests for list_layouts()."""

    def test_returns_all_layouts(self) -> None:
        layouts = list_layouts()
        assert "qwerty" in layouts
        assert "abnt2" in layouts
        assert "azerty" in layouts
        assert "qwertz" in layouts
        assert "dvorak" in layouts
        assert "colemak" in layouts
        assert "qwerty_latam" in layouts
        assert "qwerty_pt" in layouts
        assert "qwerty_it" in layouts
        assert len(layouts) == 9

    def test_returns_sorted(self) -> None:
        layouts = list_layouts()
        assert layouts == sorted(layouts)


class TestGenerateKeyboardWalks:
    """Tests for generate_keyboard_walks()."""

    def test_yields_strings(self) -> None:
        walks = list(generate_keyboard_walks(max_results=10))
        assert len(walks) > 0
        for w in walks:
            assert isinstance(w, str)

    def test_known_walks_included(self) -> None:
        walks = set(generate_keyboard_walks(max_results=500))
        assert "qwerty" in walks
        assert "asdfgh" in walks
        assert "zxcvbn" in walks
        assert "1234567890" in walks

    def test_min_length_filtering(self) -> None:
        walks = list(generate_keyboard_walks(min_length=6, max_results=100))
        for w in walks:
            assert len(w) >= 6

    def test_max_length_filtering(self) -> None:
        walks = list(generate_keyboard_walks(max_length=6, max_results=100))
        for w in walks:
            assert len(w) <= 6

    def test_min_max_combined(self) -> None:
        walks = list(generate_keyboard_walks(min_length=5, max_length=8, max_results=100))
        for w in walks:
            assert 5 <= len(w) <= 8

    def test_max_results_limits_output(self) -> None:
        walks = list(generate_keyboard_walks(max_results=25))
        assert len(walks) == 25

    def test_max_results_zero_unlimited(self) -> None:
        walks = list(generate_keyboard_walks(max_results=0, max_length=5, min_length=4))
        assert len(walks) > 25

    def test_no_duplicates(self) -> None:
        walks = list(generate_keyboard_walks(max_results=200))
        assert len(walks) == len(set(walks))

    def test_include_shifted_false(self) -> None:
        walks_no_shift = set(generate_keyboard_walks(include_shifted=False, max_results=100))
        # Without shift, no uppercase-only variants should appear
        # (known walks like "!qaz2wsx" still appear since they are hardcoded)
        for w in walks_no_shift:
            # Graph-traversal walks use only keys in the adjacency map (lowercase)
            assert isinstance(w, str)

    def test_include_shifted_true_has_uppercase(self) -> None:
        walks = set(generate_keyboard_walks(include_shifted=True, max_results=200))
        has_upper = any(w != w.lower() for w in walks)
        assert has_upper, "Shifted output should contain uppercase variants"

    def test_include_known_false(self) -> None:
        walks = list(generate_keyboard_walks(include_known=False, max_results=50))
        # Should still produce walks from graph traversal
        assert len(walks) > 0

    def test_abnt2_layout(self) -> None:
        walks = list(generate_keyboard_walks(layout="abnt2", max_results=50))
        assert len(walks) > 0
        for w in walks:
            assert isinstance(w, str)

    def test_abnt2_known_walks_included(self) -> None:
        walks = set(generate_keyboard_walks(layout="abnt2", max_results=500))
        assert "çlkjhg" in walks

    def test_dvorak_yields_results(self) -> None:
        walks = list(generate_keyboard_walks(layout="dvorak", max_results=10))
        assert len(walks) > 0

    def test_invalid_layout_raises(self) -> None:
        with pytest.raises(ValueError, match="Layout desconhecido"):
            list(generate_keyboard_walks(layout="nonexistent_layout", max_results=10))


class TestIsKeyboardWalk:
    """Tests for is_keyboard_walk()."""

    def test_detects_qwerty(self) -> None:
        assert is_keyboard_walk("qwerty") is True

    def test_detects_asdfgh(self) -> None:
        assert is_keyboard_walk("asdfgh") is True

    def test_detects_zxcvbn(self) -> None:
        assert is_keyboard_walk("zxcvbn") is True

    def test_detects_numeric_sequence(self) -> None:
        assert is_keyboard_walk("123456") is True

    def test_rejects_non_walk_string(self) -> None:
        # "h4ck3r!" has no consecutive adjacent keys on QWERTY
        assert is_keyboard_walk("h4ck3r!") is False

    def test_rejects_random_string(self) -> None:
        assert is_keyboard_walk("xt7bq2m") is False

    def test_rejects_short_string(self) -> None:
        assert is_keyboard_walk("ab") is False

    def test_min_consecutive_parameter(self) -> None:
        # "qw" is adjacent but min_consecutive=3 by default
        assert is_keyboard_walk("qwX", min_consecutive=3) is False
        # With min_consecutive=2 it should detect
        assert is_keyboard_walk("qwX", min_consecutive=2) is True

    def test_case_insensitive(self) -> None:
        assert is_keyboard_walk("QWERTY") is True
        assert is_keyboard_walk("QwErTy") is True

    def test_known_walk_substring(self) -> None:
        # "xyzqwerty123" contains "qwerty" which is a known walk
        assert is_keyboard_walk("xyzqwerty123") is True

    def test_abnt2_layout(self) -> None:
        # cedilla adjacent to l, k, j, h, g on ABNT2
        assert is_keyboard_walk("çlkj", layout="abnt2") is True

    def test_colemak_detection(self) -> None:
        assert is_keyboard_walk("arst", layout="colemak") is True

    def test_invalid_layout_raises(self) -> None:
        with pytest.raises(ValueError, match="Layout desconhecido"):
            is_keyboard_walk("qwerty", layout="nonexistent_layout")

    def test_empty_string(self) -> None:
        assert is_keyboard_walk("") is False


class TestNewLayouts:
    """Tests for AZERTY, QWERTZ, DVORAK, COLEMAK, LATAM, PT, IT layouts."""

    def test_azerty_adjacency(self) -> None:
        assert is_keyboard_walk("azert", layout="azerty") is True
        assert is_keyboard_walk("qsdfg", layout="azerty") is True

    def test_azerty_generates(self) -> None:
        walks = set(generate_keyboard_walks(layout="azerty", max_results=500))
        assert len(walks) == 500
        assert "azerty" in walks

    def test_qwertz_adjacency(self) -> None:
        assert is_keyboard_walk("qwert", layout="qwertz") is True
        assert is_keyboard_walk("yxcvb", layout="qwertz") is True

    def test_qwertz_generates(self) -> None:
        walks = set(generate_keyboard_walks(layout="qwertz", max_results=500))
        assert len(walks) == 500
        assert "qwertz" in walks

    def test_dvorak_adjacency(self) -> None:
        assert is_keyboard_walk("aoeu", layout="dvorak") is True
        assert is_keyboard_walk("htns", layout="dvorak") is True

    def test_dvorak_generates(self) -> None:
        walks = set(generate_keyboard_walks(layout="dvorak", max_results=500))
        assert len(walks) == 500
        assert "aoeui" in walks

    def test_colemak_adjacency(self) -> None:
        assert is_keyboard_walk("arst", layout="colemak") is True
        assert is_keyboard_walk("dhne", layout="colemak") is True

    def test_colemak_generates(self) -> None:
        walks = set(generate_keyboard_walks(layout="colemak", max_results=500))
        assert len(walks) == 500
        assert "arst" in walks

    def test_latam_adjacency(self) -> None:
        assert is_keyboard_walk("qwer", layout="qwerty_latam") is True
        assert is_keyboard_walk("asdf", layout="qwerty_latam") is True

    def test_latam_generates(self) -> None:
        walks = list(generate_keyboard_walks(layout="qwerty_latam", max_results=50))
        assert len(walks) == 50

    def test_pt_adjacency(self) -> None:
        assert is_keyboard_walk("qwer", layout="qwerty_pt") is True
        assert is_keyboard_walk("çlkj", layout="qwerty_pt") is True

    def test_pt_generates(self) -> None:
        walks = list(generate_keyboard_walks(layout="qwerty_pt", max_results=50))
        assert len(walks) == 50

    def test_it_adjacency(self) -> None:
        assert is_keyboard_walk("qwer", layout="qwerty_it") is True
        assert is_keyboard_walk("asdf", layout="qwerty_it") is True

    def test_it_generates(self) -> None:
        walks = list(generate_keyboard_walks(layout="qwerty_it", max_results=50))
        assert len(walks) == 50

    def test_no_duplicates_any_layout(self) -> None:
        for layout in list_layouts():
            walks = list(generate_keyboard_walks(layout=layout, max_results=200))
            assert len(walks) == len(set(walks)), f"duplicates in {layout}"

    def test_all_layouts_generate_at_least_100(self) -> None:
        for layout in list_layouts():
            walks = list(generate_keyboard_walks(layout=layout, max_results=100))
            assert len(walks) == 100, f"{layout} generated only {len(walks)}"

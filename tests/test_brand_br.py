"""Tests for wlf_modules.brand_br - Brazilian brand password generator."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.brand_br import (
    _CATEGORY_MAP,
    _DIGITAL_BANKS,
    _ECOMMERCE,
    _FOOD_DELIVERY,
    _FOOTBALL_CLUBS,
    _GOV_SERVICES,
    _SOCIAL_BR,
    _STREAMING,
    _TECH_BRANDS,
    _TELECOM,
    _TRANSPORT,
    _apply_leet,
    available_categories,
    generate_brand_br,
    get_brands,
)


class TestConstants:
    """All category constant lists must be non-empty."""

    @pytest.mark.parametrize(
        "cat_list",
        [
            _DIGITAL_BANKS,
            _TELECOM,
            _ECOMMERCE,
            _TECH_BRANDS,
            _FOOD_DELIVERY,
            _STREAMING,
            _SOCIAL_BR,
            _TRANSPORT,
            _GOV_SERVICES,
            _FOOTBALL_CLUBS,
        ],
        ids=[
            "digital_banks",
            "telecom",
            "ecommerce",
            "tech_brands",
            "food_delivery",
            "streaming",
            "social_br",
            "transport",
            "gov_services",
            "football_clubs",
        ],
    )
    def test_category_list_non_empty(self, cat_list: list[str]) -> None:
        assert len(cat_list) > 0

    def test_category_map_has_all_categories(self) -> None:
        expected = {
            "digital_banks", "telecom", "ecommerce", "tech_brands",
            "food_delivery", "streaming", "social_br", "transport",
            "gov_services", "football_clubs",
        }
        assert set(_CATEGORY_MAP.keys()) == expected

    def test_all_brands_are_lowercase_strings(self) -> None:
        for cat, brands in _CATEGORY_MAP.items():
            for brand in brands:
                assert isinstance(brand, str), f"{cat}: {brand} is not str"
                assert brand == brand.lower(), f"{cat}: {brand} is not lowercase"
                assert brand.strip() == brand, f"{cat}: {brand} has whitespace"


class TestGetBrands:
    def test_all_brands_returns_nonempty(self) -> None:
        result = get_brands()
        assert len(result) > 0

    def test_all_brands_are_strings(self) -> None:
        for brand in get_brands():
            assert isinstance(brand, str)

    def test_category_filter(self) -> None:
        result = get_brands(["telecom"])
        assert set(result) == set(_TELECOM)

    def test_multiple_categories(self) -> None:
        result = get_brands(["telecom", "transport"])
        expected = set(_TELECOM) | set(_TRANSPORT)
        assert set(result) == expected

    def test_unknown_category_returns_empty(self) -> None:
        result = get_brands(["nonexistent_category"])
        assert result == []

    def test_deduplication(self) -> None:
        result = get_brands()
        assert len(result) == len(set(result))


class TestGenerateBrandBr:
    def test_yields_strings(self) -> None:
        for candidate in generate_brand_br(max_results=50):
            assert isinstance(candidate, str)

    def test_yields_nonempty_strings(self) -> None:
        for candidate in generate_brand_br(max_results=50):
            assert len(candidate) > 0

    def test_max_results_limits_output(self) -> None:
        results = list(generate_brand_br(max_results=100))
        assert len(results) <= 100

    def test_max_results_zero_is_unlimited(self) -> None:
        list(generate_brand_br(max_results=50))
        unlimited = list(generate_brand_br(max_results=0, categories=["telecom"]))
        assert len(unlimited) > 50

    def test_category_filtering(self) -> None:
        results = list(generate_brand_br(categories=["telecom"], max_results=500))
        # Collect stripped base forms for sanity check
        telecom_set = set(_TELECOM)
        bases = {r.lower().rstrip("!@#*.0123456789") for r in results}
        # At least one raw telecom brand must appear among the base forms
        assert bases & telecom_set, "No telecom brand base found in results"
        # Raw brand names should also be present
        assert any(brand in results for brand in _TELECOM)

    def test_casing_variants(self) -> None:
        results = list(generate_brand_br(
            categories=["food_delivery"],
            with_numbers=False,
            with_leet=False,
            with_year=False,
            max_results=500,
        ))
        assert "ifood" in results
        assert "Ifood" in results
        assert "IFOOD" in results

    def test_numeric_suffixes_present(self) -> None:
        results = list(generate_brand_br(
            categories=["food_delivery"],
            with_numbers=True,
            with_leet=False,
            with_year=False,
            max_results=500,
        ))
        assert "ifood123" in results
        assert "Ifood123" in results

    def test_special_char_suffixes(self) -> None:
        results = list(generate_brand_br(
            categories=["food_delivery"],
            with_numbers=False,
            with_leet=False,
            with_year=False,
            max_results=500,
        ))
        assert "ifood!" in results
        assert "ifood@" in results

    def test_leet_variants_present(self) -> None:
        results = list(generate_brand_br(
            categories=["streaming"],
            with_numbers=False,
            with_leet=True,
            with_year=False,
            max_results=2000,
        ))
        # "netflix" -> leet "n3tfl1x"
        assert "n3tfl1x" in results

    def test_year_suffixes(self) -> None:
        results = list(generate_brand_br(
            categories=["food_delivery"],
            with_numbers=False,
            with_leet=False,
            with_year=True,
            max_results=500,
        ))
        assert "ifood2024" in results
        assert "Ifood2025" in results

    def test_football_fan_patterns(self) -> None:
        results = list(generate_brand_br(
            categories=["football_clubs"],
            with_numbers=False,
            with_leet=False,
            with_year=False,
            max_results=5000,
        ))
        assert "meuflamengo" in results
        assert "vaiflamengo" in results
        assert "flamengocampeao" in results
        assert "eu_amo_flamengo" in results
        assert "flamengoate_morrer" in results

    def test_no_duplicates(self) -> None:
        results = list(generate_brand_br(
            categories=["food_delivery"],
            max_results=500,
        ))
        assert len(results) == len(set(results))

    def test_disable_all_extras(self) -> None:
        results = list(generate_brand_br(
            categories=["food_delivery"],
            with_numbers=False,
            with_leet=False,
            with_year=False,
            max_results=500,
        ))
        # Should still have base variants and special chars
        assert len(results) > 0
        # Should NOT have numeric suffixes
        assert "ifood123" not in results


class TestApplyLeet:
    def test_basic_substitution(self) -> None:
        # a->4, e->3, i->1, o->0, s->5; u is not mapped
        assert _apply_leet("aeios") == "43105"

    def test_no_change_for_non_mapped(self) -> None:
        assert _apply_leet("xyz") == "xyz"

    def test_mixed(self) -> None:
        assert _apply_leet("samsung") == "54m5ung"

    def test_empty_string(self) -> None:
        assert _apply_leet("") == ""


class TestAvailableCategories:
    def test_returns_sorted_list(self) -> None:
        cats = available_categories()
        assert cats == sorted(cats)

    def test_has_ten_categories(self) -> None:
        assert len(available_categories()) == 10

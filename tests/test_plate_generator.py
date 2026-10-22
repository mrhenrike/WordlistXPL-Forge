"""Tests for plate_generator module: license plate password candidate generation."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.plate_generator import (
    generate_country_plates,
    generate_from_plate,
    generate_from_plates,
    list_countries,
    list_formats,
    load_plate_patterns,
    sanitize_plate,
)

# ── Sanitization ─────────────────────────────────────────────────────────────

class TestSanitizePlate:
    def test_strips_dash(self) -> None:
        assert sanitize_plate("ABC-1D23") == "ABC1D23"

    def test_strips_slash(self) -> None:
        assert sanitize_plate("ABC/1234") == "ABC1234"

    def test_strips_backslash(self) -> None:
        assert sanitize_plate("ABC\\1234") == "ABC1234"

    def test_strips_underscore(self) -> None:
        assert sanitize_plate("ABC_1234") == "ABC1234"

    def test_strips_dot(self) -> None:
        assert sanitize_plate("AB.12.CD") == "AB12CD"

    def test_strips_space(self) -> None:
        assert sanitize_plate("AB 123 CD") == "AB123CD"

    def test_strips_multiple_separators(self) -> None:
        assert sanitize_plate("A-B.C 1/2\\3_4") == "ABC1234"

    def test_empty_input(self) -> None:
        assert sanitize_plate("") == ""

    def test_only_separators(self) -> None:
        assert sanitize_plate("---...___") == ""

    def test_preserves_case(self) -> None:
        assert sanitize_plate("aBc1D23") == "aBc1D23"

    def test_removes_non_alnum_special(self) -> None:
        assert sanitize_plate("AB@#1234") == "AB1234"


# ── Pattern loading ──────────────────────────────────────────────────────────

class TestLoadPlatePatterns:
    def test_loads_json_and_returns_dict(self) -> None:
        data = load_plate_patterns()
        assert isinstance(data, dict)
        assert "countries" in data
        assert "version" in data

    def test_countries_is_list(self) -> None:
        data = load_plate_patterns()
        assert isinstance(data["countries"], list)
        assert len(data["countries"]) > 0

    def test_country_entry_has_required_fields(self) -> None:
        data = load_plate_patterns()
        for country in data["countries"][:5]:
            assert "code" in country
            assert "name" in country
            assert "continent" in country
            assert "formats" in country

    def test_format_entry_has_pattern(self) -> None:
        data = load_plate_patterns()
        br = next(c for c in data["countries"] if c["code"] == "BR")
        for fmt in br["formats"]:
            assert "pattern" in fmt
            assert "era" in fmt
            assert "example" in fmt

    def test_custom_path(self) -> None:
        json_path = ROOT / "data" / "plate_patterns_worldwide.json"
        data = load_plate_patterns(json_path=json_path)
        assert isinstance(data, dict)
        assert len(data["countries"]) > 0

    def test_missing_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_plate_patterns(json_path=Path("/nonexistent/path.json"))


# ── Per-plate generation ─────────────────────────────────────────────────────

class TestGenerateFromPlate:
    def test_yields_candidates(self) -> None:
        candidates = list(generate_from_plate("ABC1D23"))
        assert len(candidates) > 0

    def test_includes_sanitized_form(self) -> None:
        candidates = list(generate_from_plate("ABC-1D23"))
        assert "ABC1D23" in candidates

    def test_includes_uppercase(self) -> None:
        candidates = list(generate_from_plate("abc1d23"))
        assert "ABC1D23" in candidates

    def test_includes_lowercase(self) -> None:
        candidates = list(generate_from_plate("ABC1D23"))
        assert "abc1d23" in candidates

    def test_includes_reversed(self) -> None:
        candidates = list(generate_from_plate("ABC1D23"))
        assert "32D1CBA" in candidates

    def test_includes_suffix_variants(self) -> None:
        candidates = list(generate_from_plate("ABC1D23"))
        assert "ABC1D23!" in candidates
        assert "ABC1D23123" in candidates

    def test_includes_letter_part(self) -> None:
        candidates = list(generate_from_plate("ABC1D23"))
        assert "ABCD" in candidates

    def test_includes_digit_part(self) -> None:
        candidates = list(generate_from_plate("ABC1D23"))
        assert "123" in candidates

    def test_no_duplicates(self) -> None:
        candidates = list(generate_from_plate("ABC1234"))
        assert len(candidates) == len(set(candidates))

    def test_empty_plate_yields_nothing(self) -> None:
        candidates = list(generate_from_plate(""))
        assert candidates == []

    def test_separator_only_yields_nothing(self) -> None:
        candidates = list(generate_from_plate("---"))
        assert candidates == []

    def test_all_candidates_are_strings(self) -> None:
        for candidate in generate_from_plate("XYZ9876"):
            assert isinstance(candidate, str)
            break  # just check first

    def test_without_case_variants(self) -> None:
        candidates = list(generate_from_plate("ABC1234", with_case_variants=False))
        # Should still contain the original but fewer total
        assert "ABC1234" in candidates

    def test_without_numbers(self) -> None:
        candidates = list(generate_from_plate("ABC1234", with_numbers=False))
        # Should not have year suffixes
        assert "ABC12341990" not in candidates

    def test_without_specials(self) -> None:
        candidates = list(generate_from_plate("ABC1234", with_specials=False))
        # Should not have special char prefix/suffix combos like $ABC1234
        assert "$ABC1234" not in candidates

    def test_candidate_count_reasonable(self) -> None:
        """A 7-char plate should produce a substantial but bounded set."""
        candidates = list(generate_from_plate("ABC1D23"))
        assert 50 < len(candidates) < 5000


# ── Country-based generation ─────────────────────────────────────────────────

class TestGenerateCountryPlates:
    def test_generates_for_brazil(self) -> None:
        plates = list(generate_country_plates("BR", max_per_format=10, seed=42))
        assert len(plates) > 0

    def test_br_current_matches_mercosul(self) -> None:
        """BR current format: 3 letters + 1 digit + 1 letter + 2 digits."""
        pattern = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")
        for plate in generate_country_plates("BR", era="current", max_per_format=20, seed=42):
            assert pattern.match(plate), f"Plate '{plate}' does not match Mercosul format"

    def test_br_legacy_matches_old_format(self) -> None:
        """BR legacy format: 3 letters + 4 digits."""
        pattern = re.compile(r"^[A-Z]{3}[0-9]{4}$")
        for plate in generate_country_plates("BR", era="legacy", max_per_format=20, seed=42):
            assert pattern.match(plate), f"Plate '{plate}' does not match legacy format"

    def test_generates_for_us(self) -> None:
        plates = list(generate_country_plates("US", max_per_format=10, seed=42))
        assert len(plates) > 0

    def test_generates_for_germany(self) -> None:
        plates = list(generate_country_plates("DE", max_per_format=10, seed=42))
        assert len(plates) > 0

    def test_era_all_includes_both(self) -> None:
        all_plates = list(generate_country_plates("BR", era="all", max_per_format=5, seed=42))
        current_plates = list(generate_country_plates("BR", era="current", max_per_format=5, seed=42))
        legacy_plates = list(generate_country_plates("BR", era="legacy", max_per_format=5, seed=42))
        assert len(all_plates) >= len(current_plates)
        assert len(all_plates) >= len(legacy_plates)

    def test_unknown_country_yields_nothing(self) -> None:
        plates = list(generate_country_plates("ZZ", max_per_format=10))
        assert plates == []

    def test_seed_reproducibility(self) -> None:
        run1 = list(generate_country_plates("BR", max_per_format=20, seed=123))
        run2 = list(generate_country_plates("BR", max_per_format=20, seed=123))
        assert run1 == run2

    def test_max_per_format_respected(self) -> None:
        plates = list(generate_country_plates("BR", era="current", max_per_format=5, seed=42))
        assert len(plates) <= 5

    def test_all_outputs_are_strings(self) -> None:
        for plate in generate_country_plates("JP", max_per_format=5, seed=42):
            assert isinstance(plate, str)
            assert len(plate) > 0


# ── Listing ──────────────────────────────────────────────────────────────────

class TestListCountries:
    def test_returns_non_empty_list(self) -> None:
        countries = list_countries()
        assert len(countries) > 0

    def test_br_in_list(self) -> None:
        codes = [c["code"] for c in list_countries()]
        assert "BR" in codes

    def test_us_in_list(self) -> None:
        codes = [c["code"] for c in list_countries()]
        assert "US" in codes

    def test_entry_has_required_keys(self) -> None:
        for entry in list_countries()[:5]:
            assert "code" in entry
            assert "name" in entry
            assert "continent" in entry

    def test_count_at_least_50(self) -> None:
        assert len(list_countries()) >= 50


class TestListFormats:
    def test_br_has_formats(self) -> None:
        formats = list_formats("BR")
        assert len(formats) >= 2

    def test_unknown_country_empty(self) -> None:
        assert list_formats("ZZ") == []

    def test_format_has_pattern(self) -> None:
        for fmt in list_formats("BR"):
            assert "pattern" in fmt
            assert len(fmt["pattern"]) > 0


# ── Batch generation ─────────────────────────────────────────────────────────

class TestGenerateFromPlates:
    def test_handles_multiple_plates(self) -> None:
        candidates = list(generate_from_plates(["ABC1234", "XYZ5678"]))
        assert len(candidates) > 0

    def test_includes_candidates_from_all_plates(self) -> None:
        candidates = list(generate_from_plates(["ABC1234", "XYZ5678"]))
        assert "ABC1234" in candidates
        assert "XYZ5678" in candidates

    def test_no_duplicates_across_plates(self) -> None:
        candidates = list(generate_from_plates(["ABC1234", "ABC1234"]))
        assert len(candidates) == len(set(candidates))

    def test_empty_list_yields_nothing(self) -> None:
        candidates = list(generate_from_plates([]))
        assert candidates == []

    def test_forwards_kwargs(self) -> None:
        with_specials = list(generate_from_plates(["ABC1234"], with_specials=True))
        without_specials = list(generate_from_plates(["ABC1234"], with_specials=False))
        assert len(with_specials) > len(without_specials)

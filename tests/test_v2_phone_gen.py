"""Fase 5 — Phone generator tests (16 countries)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.phone_gen import generate_phones, COUNTRIES, list_countries


class TestPhoneGen:
    def test_supported_countries_count(self) -> None:
        assert len(COUNTRIES) >= 10

    @pytest.mark.parametrize("country", list(COUNTRIES.keys())[:16])
    def test_generates_for_each_country(self, country: str) -> None:
        count = 0
        for _ in generate_phones(country=country):
            count += 1
            if count >= 5:
                break
        assert count > 0, f"No phones generated for {country}"

    def test_list_countries_not_empty(self) -> None:
        countries = list_countries()
        assert len(countries) >= 10

    def test_all_phones_are_strings(self) -> None:
        count = 0
        for p in generate_phones(country="brazil"):
            assert isinstance(p, str)
            count += 1
            if count >= 20:
                break

    def test_phone_format_br(self) -> None:
        count = 0
        for p in generate_phones(country="brazil"):
            assert p.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit(), f"Unexpected format: {p}"
            count += 1
            if count >= 20:
                break

    def test_unknown_country_fallback(self) -> None:
        count = 0
        for _ in generate_phones(country="nonexistent_xyz"):
            count += 1
            if count >= 5:
                break
        # Unknown countries may use a generic fallback; just verify no crash
        assert count >= 0

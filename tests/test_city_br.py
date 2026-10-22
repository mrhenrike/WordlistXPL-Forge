"""Tests for generate_city_br in br_deep_engine."""
from __future__ import annotations

from wlf_modules.br_deep_engine import (
    _CAPITAIS_BR,
    _CAPITAL_UF,
    _CIDADES_TOP100,
    generate_city_br,
)


class TestGenerateCityBr:
    """Validate city-based password generation."""

    def test_yields_strings(self) -> None:
        results = list(generate_city_br(max_results=20))
        assert len(results) > 0
        assert all(isinstance(r, str) for r in results)

    def test_capitals_included_when_flag_true(self) -> None:
        results = set(generate_city_br(include_capitals=True, include_top100=False))
        for cap in _CAPITAIS_BR:
            assert cap in results, f"Capital '{cap}' missing from results"

    def test_capitals_excluded_when_flag_false(self) -> None:
        results = set(
            generate_city_br(
                include_capitals=False,
                include_top100=True,
                with_suffixes=False,
            )
        )
        # Capitals that are NOT also in top100 should be absent
        top100_set = set(_CIDADES_TOP100)
        for cap in _CAPITAIS_BR:
            if cap not in top100_set:
                assert cap not in results, (
                    f"Capital '{cap}' should not appear with include_capitals=False"
                )

    def test_top100_included_when_flag_true(self) -> None:
        results = set(generate_city_br(include_capitals=False, include_top100=True))
        for city in _CIDADES_TOP100:
            assert city in results, f"City '{city}' missing from results"

    def test_top100_excluded_when_flag_false(self) -> None:
        results = set(
            generate_city_br(
                include_capitals=True,
                include_top100=False,
                with_suffixes=False,
            )
        )
        capitais_set = set(_CAPITAIS_BR)
        for city in _CIDADES_TOP100:
            if city not in capitais_set:
                assert city not in results, (
                    f"City '{city}' should not appear with include_top100=False"
                )

    def test_max_results_limits_output(self) -> None:
        for limit in (1, 10, 50, 100):
            results = list(generate_city_br(max_results=limit))
            assert len(results) == limit, (
                f"Expected {limit} results, got {len(results)}"
            )

    def test_unlimited_when_max_zero(self) -> None:
        results = list(generate_city_br(max_results=0))
        assert len(results) > 100

    def test_uf_suffixes_for_capitals(self) -> None:
        results = set(generate_city_br(include_capitals=True, include_top100=False))
        for capital, uf in _CAPITAL_UF.items():
            expected = f"{capital}_{uf}"
            assert expected in results, (
                f"UF suffix '{expected}' missing for capital '{capital}'"
            )

    def test_no_duplicates(self) -> None:
        results = list(generate_city_br())
        assert len(results) == len(set(results)), "Duplicate entries found"

    def test_case_variants_present(self) -> None:
        results = set(generate_city_br(include_capitals=True, include_top100=False))
        assert "brasilia" in results
        assert "Brasilia" in results
        assert "BRASILIA" in results

    def test_underscore_removal_variants(self) -> None:
        """Cities with underscores should also appear without them."""
        results = set(generate_city_br(include_capitals=False, include_top100=True))
        assert "praia_grande" in results
        assert "praiagrande" in results

    def test_fan_patterns(self) -> None:
        results = set(generate_city_br(include_capitals=True, include_top100=False))
        assert "eu_amo_brasilia" in results
        assert "sou_de_saopaulo" in results
        assert "nascido_em_curitiba" in results

    def test_suffix_patterns(self) -> None:
        results = set(generate_city_br(include_capitals=True, include_top100=False))
        assert "brasilia123" in results
        assert "brasilia!" in results
        assert "brasilia2025" in results

    def test_empty_when_both_flags_false(self) -> None:
        results = list(
            generate_city_br(include_capitals=False, include_top100=False)
        )
        assert len(results) == 0

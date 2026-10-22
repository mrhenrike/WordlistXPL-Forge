"""Tests for wlf_modules/cpf_cnpj_gen.py: CPF/CNPJ generator."""
from __future__ import annotations

import pytest

from wlf_modules.cpf_cnpj_gen import (
    ALGORITHMS,
    REGION_DIGIT_STATES,
    REGION_MAP,
    __info__,
    _cpf_check_digits,
    _cnpj_check_digits,
    estimate_file_size,
    format_cnpj,
    format_cpf,
    format_output,
    generate_cnpjs,
    generate_cpfs,
    resolve_region,
    run,
    validate_cnpj,
    validate_cpf,
)


# ── __info__ and run() contract ──────────────────────────────────────────────


class TestModuleContract:
    def test_info_dict_has_required_keys(self) -> None:
        assert "name" in __info__
        assert "version" in __info__
        assert "description" in __info__
        assert "author" in __info__
        assert __info__["name"] == "cpf_cnpj_gen"

    def test_run_returns_list_of_strings_cpf(self) -> None:
        result = run(doc_type="cpf", count=10, seed=42)
        assert isinstance(result, list)
        assert len(result) == 10
        assert all(isinstance(s, str) for s in result)

    def test_run_returns_list_of_strings_cnpj(self) -> None:
        result = run(doc_type="cnpj", count=10, seed=42)
        assert isinstance(result, list)
        assert len(result) == 10
        assert all(isinstance(s, str) for s in result)

    def test_run_invalid_doc_type(self) -> None:
        with pytest.raises(ValueError, match="doc_type invalido"):
            run(doc_type="rg", count=5)

    def test_run_with_region_string(self) -> None:
        result = run(doc_type="cpf", count=5, region="SP", seed=1)
        assert len(result) == 5
        for cpf in result:
            digits = "".join(c for c in cpf if c.isdigit())
            assert digits[8] == "8"

    def test_run_with_region_int(self) -> None:
        result = run(doc_type="cpf", count=5, region=7, seed=1)
        assert len(result) == 5
        for cpf in result:
            digits = "".join(c for c in cpf if c.isdigit())
            assert digits[8] == "7"


# ── CPF check digit calculation ──────────────────────────────────────────────


class TestCPFCheckDigits:
    @pytest.mark.parametrize(
        ("base9", "expected_d1", "expected_d2"),
        [
            ([5, 2, 9, 9, 8, 2, 2, 4, 6], 4, 4),
            ([1, 1, 1, 4, 4, 4, 7, 7, 7], 3, 5),
            ([0, 0, 0, 0, 0, 0, 0, 0, 1], 9, 1),
        ],
    )
    def test_known_cpf_check_digits(
        self, base9: list[int], expected_d1: int, expected_d2: int
    ) -> None:
        d1, d2 = _cpf_check_digits(base9)
        assert d1 == expected_d1
        assert d2 == expected_d2

    def test_all_same_digits_rejected(self) -> None:
        for d in range(10):
            cpf_str = str(d) * 11
            assert not validate_cpf(cpf_str)


# ── CNPJ check digit calculation ─────────────────────────────────────────────


class TestCNPJCheckDigits:
    @pytest.mark.parametrize(
        ("base12", "expected_d1", "expected_d2"),
        [
            ([1, 1, 2, 2, 2, 3, 3, 3, 0, 0, 0, 1], 8, 1),
            ([1, 1, 4, 4, 4, 7, 7, 7, 0, 0, 0, 1], 6, 1),
        ],
    )
    def test_known_cnpj_check_digits(
        self, base12: list[int], expected_d1: int, expected_d2: int
    ) -> None:
        d1, d2 = _cnpj_check_digits(base12)
        assert d1 == expected_d1
        assert d2 == expected_d2


# ── Validation ───────────────────────────────────────────────────────────────


class TestValidation:
    def test_validate_valid_cpf(self) -> None:
        assert validate_cpf("52998224644")
        assert validate_cpf("11144477735")

    def test_validate_invalid_cpf(self) -> None:
        assert not validate_cpf("12345678901")
        assert not validate_cpf("00000000000")
        assert not validate_cpf("1234")

    def test_validate_valid_cnpj(self) -> None:
        assert validate_cnpj("11222333000181")
        assert validate_cnpj("11444777000161")

    def test_validate_invalid_cnpj(self) -> None:
        assert not validate_cnpj("12345678000100")
        assert not validate_cnpj("11111111111111")
        assert not validate_cnpj("123")


# ── Region resolution ────────────────────────────────────────────────────────


class TestRegionResolution:
    def test_resolve_by_digit(self) -> None:
        for d in range(10):
            assert resolve_region(d) == d

    def test_resolve_by_string_digit(self) -> None:
        assert resolve_region("7") == 7

    def test_resolve_by_state(self) -> None:
        assert resolve_region("SP") == 8
        assert resolve_region("RJ") == 7
        assert resolve_region("RS") == 0
        assert resolve_region("PA") == 2
        assert resolve_region("BA") == 5
        assert resolve_region("PR") == 9

    def test_resolve_case_insensitive(self) -> None:
        assert resolve_region("sp") == 8
        assert resolve_region("Rj") == 7

    def test_resolve_all(self) -> None:
        assert resolve_region("all") is None
        assert resolve_region("TODAS") is None
        assert resolve_region(None) is None

    def test_resolve_invalid(self) -> None:
        with pytest.raises(ValueError):
            resolve_region("XX")
        with pytest.raises(ValueError):
            resolve_region(10)

    def test_all_states_mapped(self) -> None:
        all_states = set()
        for states in REGION_DIGIT_STATES.values():
            all_states.update(states)
        assert all_states == set(REGION_MAP.keys())
        assert len(REGION_MAP) == 27


# ── Formatting ───────────────────────────────────────────────────────────────


class TestFormatting:
    def test_format_cpf(self) -> None:
        assert format_cpf("52998224680") == "529.982.246-80"

    def test_format_cnpj(self) -> None:
        assert format_cnpj("11222333000181") == "11.222.333/0001-81"

    def test_format_output_plain(self) -> None:
        assert format_output("52998224680", "cpf", "plain") == "52998224680"

    def test_format_output_formatted(self) -> None:
        assert format_output("52998224680", "cpf", "formatted") == "529.982.246-80"

    def test_format_output_both(self) -> None:
        result = format_output("52998224680", "cpf", "both")
        assert "52998224680" in result
        assert "529.982.246-80" in result


# ── Size estimation ──────────────────────────────────────────────────────────


class TestSizeEstimation:
    def test_small_cpf(self) -> None:
        est = estimate_file_size(10, "cpf", "plain")
        assert "B" in est

    def test_medium_cpf(self) -> None:
        est = estimate_file_size(10000, "cpf", "plain")
        assert "KB" in est

    def test_large_cpf(self) -> None:
        est = estimate_file_size(10_000_000, "cpf", "plain")
        assert "MB" in est

    def test_formatted_larger(self) -> None:
        plain = estimate_file_size(1000, "cpf", "plain")
        fmtd = estimate_file_size(1000, "cpf", "formatted")
        both = estimate_file_size(1000, "cpf", "both")
        p_val = float(plain.replace("~", "").split()[0])
        f_val = float(fmtd.replace("~", "").split()[0])
        b_val = float(both.replace("~", "").split()[0])
        assert f_val > p_val
        assert b_val > f_val


# ── CPF generation algorithms ────────────────────────────────────────────────


class TestCPFGeneration:
    @pytest.mark.parametrize("algorithm", ALGORITHMS)
    def test_all_algorithms_produce_valid_cpfs(self, algorithm: str) -> None:
        cpfs = list(generate_cpfs(50, algorithm=algorithm, seed=42))
        assert len(cpfs) == 50
        for cpf in cpfs:
            assert len(cpf) == 11
            assert cpf.isdigit()
            assert validate_cpf(cpf), f"Invalid CPF: {cpf} (algo={algorithm})"

    @pytest.mark.parametrize("algorithm", ALGORITHMS)
    def test_all_algorithms_respect_region(self, algorithm: str) -> None:
        cpfs = list(generate_cpfs(20, region=3, algorithm=algorithm, seed=7))
        for cpf in cpfs:
            assert cpf[8] == "3", f"Wrong region in {cpf} (algo={algorithm})"

    def test_no_duplicates(self) -> None:
        cpfs = list(generate_cpfs(500, algorithm="random", seed=99))
        assert len(cpfs) == len(set(cpfs))

    def test_reproducible_with_seed(self) -> None:
        a = list(generate_cpfs(100, algorithm="cogpie", seed=12345))
        b = list(generate_cpfs(100, algorithm="cogpie", seed=12345))
        assert a == b

    def test_different_seeds_differ(self) -> None:
        a = list(generate_cpfs(50, algorithm="random", seed=1))
        b = list(generate_cpfs(50, algorithm="random", seed=2))
        assert a != b

    def test_invalid_algorithm_raises(self) -> None:
        with pytest.raises(ValueError, match="Algoritmo invalido"):
            list(generate_cpfs(10, algorithm="nonexistent"))

    def test_invalid_count_raises(self) -> None:
        with pytest.raises(ValueError, match="count"):
            list(generate_cpfs(0))

    def test_no_same_digit_cpfs(self) -> None:
        cpfs = list(generate_cpfs(1000, algorithm="random", seed=42))
        for cpf in cpfs:
            assert len(set(cpf)) > 1

    def test_region_0_is_rs(self) -> None:
        cpfs = list(generate_cpfs(10, region=0, seed=42))
        for cpf in cpfs:
            assert cpf[8] == "0"

    def test_all_regions_reachable(self) -> None:
        for region in range(10):
            cpfs = list(generate_cpfs(5, region=region, seed=42))
            assert len(cpfs) == 5
            assert all(cpf[8] == str(region) for cpf in cpfs)


# ── CNPJ generation algorithms ───────────────────────────────────────────────


class TestCNPJGeneration:
    @pytest.mark.parametrize("algorithm", ALGORITHMS)
    def test_all_algorithms_produce_valid_cnpjs(self, algorithm: str) -> None:
        cnpjs = list(generate_cnpjs(50, algorithm=algorithm, seed=42))
        assert len(cnpjs) == 50
        for cnpj in cnpjs:
            assert len(cnpj) == 14
            assert cnpj.isdigit()
            assert validate_cnpj(cnpj), f"Invalid CNPJ: {cnpj} (algo={algorithm})"

    def test_branch_embedded(self) -> None:
        cnpjs = list(generate_cnpjs(10, branch=1, algorithm="random", seed=42))
        for cnpj in cnpjs:
            assert cnpj[8:12] == "0001"

    def test_custom_branch(self) -> None:
        cnpjs = list(generate_cnpjs(10, branch=42, algorithm="random", seed=42))
        for cnpj in cnpjs:
            assert cnpj[8:12] == "0042"

    def test_invalid_branch_raises(self) -> None:
        with pytest.raises(ValueError, match="branch"):
            list(generate_cnpjs(10, branch=0))
        with pytest.raises(ValueError, match="branch"):
            list(generate_cnpjs(10, branch=10000))

    def test_no_duplicates(self) -> None:
        cnpjs = list(generate_cnpjs(500, algorithm="random", seed=99))
        assert len(cnpjs) == len(set(cnpjs))

    def test_reproducible_with_seed(self) -> None:
        a = list(generate_cnpjs(100, algorithm="cogpie", seed=12345))
        b = list(generate_cnpjs(100, algorithm="cogpie", seed=12345))
        assert a == b


# ── Integration: run() with all algorithms ───────────────────────────────────


class TestRunIntegration:
    @pytest.mark.parametrize("algorithm", ALGORITHMS)
    def test_run_cpf_all_algorithms(self, algorithm: str) -> None:
        result = run(doc_type="cpf", count=20, algorithm=algorithm, seed=42)
        assert len(result) == 20
        for item in result:
            digits = "".join(c for c in item if c.isdigit())
            assert validate_cpf(digits)

    @pytest.mark.parametrize("algorithm", ALGORITHMS)
    def test_run_cnpj_all_algorithms(self, algorithm: str) -> None:
        result = run(doc_type="cnpj", count=20, algorithm=algorithm, seed=42)
        assert len(result) == 20
        for item in result:
            digits = "".join(c for c in item if c.isdigit())
            assert validate_cnpj(digits)

    def test_run_formatted_cpf(self) -> None:
        result = run(doc_type="cpf", count=5, fmt="formatted", seed=42)
        for item in result:
            assert "." in item
            assert "-" in item

    def test_run_formatted_cnpj(self) -> None:
        result = run(doc_type="cnpj", count=5, fmt="formatted", seed=42)
        for item in result:
            assert "." in item
            assert "/" in item
            assert "-" in item

    def test_run_both_format(self) -> None:
        result = run(doc_type="cpf", count=5, fmt="both", seed=42)
        for item in result:
            assert "\t" in item

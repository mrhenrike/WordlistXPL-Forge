"""Tests for benchmark_integrity module."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from wlf_modules.benchmark_integrity import (
    DuplicateJSONKey,
    load_benchmark_strict,
    validate_hit_rates,
)


def test_duplicate_keys_raise() -> None:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bad.json"
        p.write_text(
            '{"benchmarks": {"case": {"hit@10": 1}, "case": {"hit@10": 2}}}',
            encoding="utf-8",
        )
        with pytest.raises(DuplicateJSONKey):
            load_benchmark_strict(p)


def test_valid_report() -> None:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "ok.json"
        p.write_text(
            json.dumps({"benchmarks": {"test": {"hit@10": 1, "hit@100": 2}}}),
            encoding="utf-8",
        )
        assert validate_hit_rates(load_benchmark_strict(p)) == []


def test_non_monotonic_is_reported() -> None:
    assert len(validate_hit_rates({"hit@10": 5, "hit@100": 4})) == 1


def test_run_contract() -> None:
    from wlf_modules.benchmark_integrity import run

    result = run("")
    assert len(result) == 1 and "Usage" in result[0]


def test_nested_non_monotonic() -> None:
    data = {"outer": {"hit@10": 10, "hit@100": 5, "hit@1000": 20}}
    warnings = validate_hit_rates(data)
    assert len(warnings) == 1
    assert "hit@100 below hit@10" in warnings[0]

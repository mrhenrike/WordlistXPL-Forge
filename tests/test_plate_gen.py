"""Tests for PlateXPL: structural plate catalog, normalization and synthetic generation."""
from __future__ import annotations

import json
from typing import Any

import pytest

from wlf_modules.plate_gen import (
    UnsupportedPlatePattern,
    catalog,
    check_plate,
    country_charsets,
    generate_synthetic_plates,
    normalize_plate,
    normalize_profile_plates,
    parse_plate_pattern,
)

DB: dict[str, Any] = catalog()


def test_total_country_catalog() -> None:
    assert len(DB["countries"]) == 250
    with_patterns = sum(1 for x in DB["countries"].values() if x["patterns"])
    assert with_patterns == 185


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("abc-1234", "ABC1234"),
        ("ABC/1C_34", "ABC1C34"),
        ("Ab C .1 D-23", "ABC1D23"),
        ("abc\n1234", "ABC1234"),
    ],
)
def test_ascii_normalization(raw: str, expected: str) -> None:
    assert normalize_plate(raw) == expected


def test_nonascii_characters_stripped() -> None:
    result = normalize_plate("AB1234")
    assert result == "AB1234"


@pytest.mark.parametrize("bad", ["", "---", "x" * 25])
def test_bad_input(bad: str) -> None:
    with pytest.raises(ValueError):
        normalize_plate(bad)


@pytest.mark.parametrize(
    ("plate", "country", "is_match"),
    [
        ("ABC-1234", "BR", True),
        ("ABC1C34", "BR", True),
        ("ZZ99ZZZ", "GB", True),
        ("ZZZ9Z99", "BR", True),
        ("A1BC234", "BR", False),
        ("123ABC4", "GB", False),
    ],
)
def test_structural_formats(plate: str, country: str, is_match: bool) -> None:
    d = check_plate(plate, country, DB)
    assert d["structural_match"] is is_match
    assert d["verified_issuance"] is False


def test_non_western_countries_have_no_patterns() -> None:
    for code in ("CN", "KR"):
        entry = DB["countries"][code]
        assert entry["status"] == "non_western_charset"
        assert entry["patterns"] == []


def test_no_non_ascii_in_any_regex() -> None:
    for _code, entry in DB["countries"].items():
        for pattern in entry.get("patterns", []):
            regex = pattern.get("regex", "")
            assert regex.isascii(), f"Non-ASCII in {_code}: {regex[:40]}"


def test_unknown_pattern_is_explicitly_not_supported() -> None:
    assert not DB["countries"]["AQ"]["patterns"]
    with pytest.raises(ValueError):
        list(generate_synthetic_plates("AQ", db=DB))


def test_profile_multiple_plates_no_inference() -> None:
    profile: dict[str, Any] = {
        "vehicles": [
            {"plate": "abc-1234", "country": "BR"},
            {"plate": "ABC_1234", "country": "BR"},
            {"plate": "zx/90", "country": ""},
        ]
    }
    result = normalize_profile_plates(profile)
    assert len(result) == 2
    assert result[-1] == {"plate": "ZX90", "country": None, "source": "operator_input"}


def test_profile_optional_plates_omitted() -> None:
    assert normalize_profile_plates({"full_name": "Teste"}) == []


def test_legacy_plain_list_profile_plates() -> None:
    result = normalize_profile_plates({"plates": ["ABC1D23", "abc-1234"]})
    assert [x["plate"] for x in result] == ["ABC1D23", "ABC1234"]


def test_bounded_synthetic_reproducible() -> None:
    a = list(generate_synthetic_plates("BR", limit=50, seed=7, db=DB))
    b = list(generate_synthetic_plates("BR", limit=50, seed=7, db=DB))
    assert a == b
    assert len(a) == len(set(a)) == 50
    assert all(check_plate(s, "BR", DB)["structural_match"] for s in a)


def test_limit_guard() -> None:
    for limit in (0, 10001, -1):
        with pytest.raises(ValueError):
            list(generate_synthetic_plates("BR", limit=limit, db=DB))


def test_charset_masks_br() -> None:
    charsets = country_charsets("BR", DB)
    all_shapes = [s for c in charsets for s in c["shapes"]]
    assert "LLLNLNN" in all_shapes
    assert "LLLNNNN" in all_shapes


def test_charset_masks_gb() -> None:
    charsets = country_charsets("GB", DB)
    assert charsets[0]["shapes"] == ["LLNNLLL"]


def test_grammar_rejects_unbounded_or_unsafe() -> None:
    for pattern in (r"^[A-Z]+$", r"^.*$", r"^(?:A)\d$", r"^[A-Z]{3,}$"):
        with pytest.raises(UnsupportedPlatePattern):
            parse_plate_pattern(pattern)


def test_every_imported_country_regex_parses_and_generates() -> None:
    for country, record in DB["countries"].items():
        if not record["patterns"]:
            continue
        shapes = country_charsets(country, DB)
        assert shapes
        generated = list(generate_synthetic_plates(country, limit=5, seed=15, db=DB))
        assert generated
        assert all(check_plate(p, country, DB)["structural_match"] for p in generated)


def test_source_attribution() -> None:
    assert DB["source"]["license"] == "MIT"
    assert "PlateGeo" in DB["source"]["name"]
    assert all("source" in p for entry in DB["countries"].values() for p in entry["patterns"])


def test_catalog_json_is_valid_and_immutable_data() -> None:
    assert json.loads(json.dumps(DB))["schema_version"] == "1.0.0"


def test_run_contract() -> None:
    from wlf_modules.plate_gen import run
    result = run(iso2="BR", command="synthetic", limit=10, seed=42)
    assert isinstance(result, list)
    assert len(result) == 10


def test_info_dict() -> None:
    from wlf_modules.plate_gen import __info__
    assert __info__["name"] == "plate_gen"
    assert "version" in __info__

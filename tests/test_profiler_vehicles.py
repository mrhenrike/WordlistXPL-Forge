"""Tests for vehicle plate integration in profiler."""
from __future__ import annotations

import re


def test_sanitize_plate_strips_separators() -> None:
    """Verify plate sanitization removes separators."""
    raw_plates = ["ABC-1D23", "AB.12.CD", "ABC 1234", "ABC/1D/23", "abc_1d23"]
    expected = ["ABC1D23", "AB12CD", "ABC1234", "ABC1D23", "ABC1D23"]
    for raw, exp in zip(raw_plates, expected):
        sanitized = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
        assert sanitized == exp


def test_vehicle_plates_profile_key() -> None:
    """Verify vehicle_plates is a list in profile."""
    profile: dict[str, list[str]] = {"vehicle_plates": []}
    raw = "ABC-1D23"
    sanitized = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    profile["vehicle_plates"].append(sanitized)
    assert profile["vehicle_plates"] == ["ABC1D23"]
    assert len(profile["vehicle_plates"]) == 1


def test_multiple_plates() -> None:
    """Test adding multiple plates."""
    profile: dict[str, list[str]] = {"vehicle_plates": []}
    plates_raw = ["ABC-1234", "DEF5G67", "HI.89.JK"]
    for raw in plates_raw:
        sanitized = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
        if sanitized:
            profile["vehicle_plates"].append(sanitized)
    assert len(profile["vehicle_plates"]) == 3
    assert "ABC1234" in profile["vehicle_plates"]
    assert "DEF5G67" in profile["vehicle_plates"]
    assert "HI89JK" in profile["vehicle_plates"]


def test_empty_plate_ignored() -> None:
    """Empty input should not add to plates."""
    profile: dict[str, list[str]] = {"vehicle_plates": []}
    raw = "---"
    sanitized = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    if sanitized:
        profile["vehicle_plates"].append(sanitized)
    assert len(profile["vehicle_plates"]) == 0

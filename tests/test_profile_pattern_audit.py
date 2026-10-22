"""Tests for profile_pattern_audit module."""
from __future__ import annotations

import pytest

from wlf_modules.profile_pattern_audit import ProfileContext, audit_password


@pytest.fixture()
def ctx() -> ProfileContext:
    return ProfileContext.from_mapping(
        {
            "full_name": "Ana Exemplo",
            "partner_name": "Bruno",
            "birth_year": 1990,
            "phones": ["000-000-0000"],
            "company_name": "EmpresaDemo",
            "nicknames": ["Aninha"],
        },
        reference_year=2026,
    )


def _has(ctx: ProfileContext, pw: str, rule: str) -> None:
    assert rule in audit_password(pw, ctx)["risk_indicators"]


def test_explicit_year_policy(ctx: ProfileContext) -> None:
    assert ctx.years == (
        "2022", "22", "2023", "23", "2024", "24",
        "2025", "25", "2026", "26", "1990", "90",
    )
    _has(ctx, "Ana2022Exemplo", "FIRST_YEAR_LAST_COMBINATION")
    _has(ctx, "Exemplo90Ana", "FIRST_YEAR_LAST_COMBINATION")
    assert "FIRST_YEAR_LAST_COMBINATION" not in audit_password(
        "Ana2021Exemplo", ctx
    )["risk_indicators"]


def test_digits_prefix_and_suffix(ctx: ProfileContext) -> None:
    for count in range(2, 7):
        _has(ctx, "Ana" + "0" * count, "NAME_NUMERIC_AFFIX_2_TO_6")
        _has(ctx, "0" * count + "Ana", "NAME_NUMERIC_AFFIX_2_TO_6")
    assert not audit_password("Ana0", ctx)["contains_profile_pattern"]


def test_sandwich_specific_widths(ctx: ProfileContext) -> None:
    for count in (2, 4, 6):
        _has(ctx, "Ana" + "0" * count + "Exemplo", "FIRST_DIGITS_2_4_6_LAST_COMBINATION")
    assert not audit_password("Ana000Exemplo", ctx)["contains_profile_pattern"]


def test_spouse_and_company(ctx: ProfileContext) -> None:
    _has(ctx, "BrunoAna", "NAME_SPOUSE_COMBINATION")
    _has(ctx, "EmpresaDemo2026", "COMPANY_YEAR_COMBINATION")


def test_phone_explicit_only(ctx: ProfileContext) -> None:
    _has(ctx, "Ana0000000000Exemplo", "FIRST_EXPLICIT_PHONE_LAST_COMBINATION")
    _has(ctx, "Ana0000000000", "NAME_EXPLICIT_PHONE_COMBINATION")
    assert not audit_password("Ana550000000000", ctx)["contains_profile_pattern"]
    empty = ProfileContext.from_mapping({"name": "Ana"}, reference_year=2026)
    assert not audit_password("Ana0000000000", empty)["contains_profile_pattern"]


def test_year_is_dynamic() -> None:
    later = ProfileContext.from_mapping({"name": "Ana"}, reference_year=2030)
    assert "2030" in later.years
    assert "2025" not in later.years


def test_no_echo(ctx: ProfileContext) -> None:
    assert "Ana00" not in str(audit_password("Ana00", ctx))


def test_invalid_year() -> None:
    with pytest.raises(ValueError):
        ProfileContext.from_mapping({"birth_year": 2050}, reference_year=2026)


def test_run_contract() -> None:
    from wlf_modules.profile_pattern_audit import run

    result = run("Ana2026", {"name": "Ana"}, reference_year=2026)
    assert "NAME_YEAR_COMBINATION" in result
    assert run("") == []


def test_nickname_year(ctx: ProfileContext) -> None:
    _has(ctx, "Aninha2026", "NICKNAME_YEAR_COMBINATION")


def test_first_last_combination(ctx: ProfileContext) -> None:
    _has(ctx, "AnaExemplo", "FIRST_LAST_COMBINATION")
    _has(ctx, "ExemploAna", "FIRST_LAST_COMBINATION")

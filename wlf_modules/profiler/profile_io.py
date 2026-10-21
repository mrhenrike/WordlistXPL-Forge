"""
profiler/profile_io.py - Profile loading and output path resolution.

Author: Andre Henrique (@mrhenrike)
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .constants import DEFAULT_OUTPUT_DIR
from .utils import _format_extension, _slug_from_name


def load_profile_yaml(filepath: str) -> dict[str, Any]:
    """
    Load a personal profile from a YAML file.

    This allows non-interactive, scripted use of the profiler.
    The YAML structure mirrors the keys returned by interactive_profile().

    Example YAML::

        full_name: "PessoaX"
        short_name: "PessoaX"
        nicknames:
          - "robotx"
          - "pxcorpx"
        birth_day: 15
        birth_month: 3
        birth_year: 1990
        pets:
          - "petx"
          - name: "robotx"
            year: 2025
        pet_adoptions:
          - name: "petx"
            year: 2026
        keywords:
          - "soccer"
          - "hacker"
        leet_mode: "basic"
        min_len: 6
        max_len: 32
        year_start: 2000
        year_end: 2026
        suffix_range_start: 0
        suffix_range_end: 99
        suffix_range_zero_pad: 2

    Args:
        filepath: Path to the YAML profile file.

    Returns:
        Profile dict, same structure as interactive_profile() output.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        ImportError: If PyYAML is not installed.
    """
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required for --profile-file. Install: pip install pyyaml"
        ) from exc

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Profile file not found: {filepath}")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Normalize list fields that might be given as strings
    for list_field in ("nicknames", "phones", "social_handles", "keywords",
                       "special_dates", "pets", "children", "phrases"):
        val = data.get(list_field)
        if isinstance(val, str):
            data[list_field] = [v.strip() for v in val.split(",") if v.strip()]
        elif val is None:
            data[list_field] = []

    data = _normalize_profile_pets(data)
    data = _normalize_date_fields(data)
    return data


def _normalize_date_fields(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normaliza campos de data do perfil YAML para o formato legado esperado pelo profiler.

    Suporta dois formatos:
      - Legado: birth_day, birth_month, birth_year como inteiros separados.
      - Estruturado: birth: {mode: age_sign, age: 26, sign: touro} ou birth: "dd/mm/yyyy".

    Tambem processa ``hire`` para entidades corporativas (mesma logica).
    """
    try:
        from wlf_modules.date_profile import build_date_tokens, date_profile_from_yaml
        from wlf_modules.i18n import get_session_locale
    except ImportError:
        return data

    locale = data.get("locale") or get_session_locale()

    # ---- Campo birth ----------------------------------------------------------
    birth_raw = data.get("birth")
    if birth_raw is not None and not isinstance(birth_raw, int):
        dp = date_profile_from_yaml(birth_raw, locale)
        if dp:
            dp_dict = dp.to_dict()
            # Preservar campos legados: so sobrescrever se ainda em zero (nao definidos)
            if not data.get("birth_day"):
                data["birth_day"] = dp_dict["birth_day"]
            if not data.get("birth_month"):
                data["birth_month"] = dp_dict["birth_month"]
            if not data.get("birth_year"):
                data["birth_year"] = dp_dict["birth_year"]
            # Campos novos (sem conflito com legado)
            data["birth_mode"] = dp_dict["birth_mode"]
            data["birth_age"] = dp_dict["birth_age"]
            data["birth_sign_index"] = dp_dict["birth_sign_index"]
            data["birth_year_min"] = dp_dict["birth_year_min"]
            data["birth_year_max"] = dp_dict["birth_year_max"]
            data["birth_locale"] = dp_dict["birth_locale"]
            # Pre-calcular tokens de data para uso posterior
            data.setdefault("_date_tokens", [])
            data["_date_tokens"] = build_date_tokens(dp, locale)

    # ---- Campo hire (empresa) -------------------------------------------------
    hire_raw = data.get("hire")
    if hire_raw is not None and not isinstance(hire_raw, int):
        dp = date_profile_from_yaml(hire_raw, locale)
        if dp:
            dp_dict = dp.to_dict()
            data["hire_day"] = dp_dict["birth_day"]
            data["hire_month"] = dp_dict["birth_month"]
            data["hire_year"] = dp_dict["birth_year"]
            data["hire_mode"] = dp_dict["birth_mode"]
            data["hire_age"] = dp_dict["birth_age"]
            data["hire_sign_index"] = dp_dict["birth_sign_index"]
            data["hire_year_min"] = dp_dict["birth_year_min"]
            data["hire_year_max"] = dp_dict["birth_year_max"]
            data.setdefault("_hire_date_tokens", [])
            data["_hire_date_tokens"] = build_date_tokens(dp, locale)

    # ---- Normalizar partner birth estruturado ---------------------------------
    if isinstance(data.get("partner"), dict):
        partner = data["partner"]
        pb_raw = partner.get("birth")
        if pb_raw is not None and not isinstance(pb_raw, int):
            dp = date_profile_from_yaml(pb_raw, locale)
            if dp:
                dp_dict = dp.to_dict()
                partner.setdefault("birth_day", dp_dict["birth_day"])
                partner.setdefault("birth_month", dp_dict["birth_month"])
                partner.setdefault("birth_year", dp_dict["birth_year"])
                partner["_date_tokens"] = build_date_tokens(dp, locale)

    return data


def _normalize_pet_entries(
    pets_raw: list[Any],
) -> tuple[list[str], dict[str, list[str]]]:
    """
    Parse pet list entries (plain strings or dicts with adoption year).

    Returns:
        (pet names, map of lower(name) -> year token strings e.g. ["2025", "25"])
    """
    names: list[str] = []
    year_map: dict[str, list[str]] = {}

    for item in pets_raw or []:
        if isinstance(item, dict):
            name = (item.get("name") or item.get("pet") or "").strip()
            if not name:
                continue
            names.append(name)
            yr_raw = item.get("year") or item.get("since") or item.get("adoption_year")
            if yr_raw is not None and str(yr_raw).strip().isdigit():
                ys = str(int(str(yr_raw).strip()))
                if len(ys) == 4:
                    year_map[name.lower()] = list(dict.fromkeys([ys, ys[-2:]]))
        elif isinstance(item, str) and item.strip():
            names.append(item.strip())

    return names, year_map


def _normalize_profile_pets(data: dict[str, Any]) -> dict[str, Any]:
    """Merge ``pet_adoptions`` into ``pets`` and keep dict entries intact."""
    pets_raw = list(data.get("pets") or [])
    for adop in data.get("pet_adoptions") or []:
        if isinstance(adop, dict) and (adop.get("name") or adop.get("pet")):
            pets_raw.append(adop)
    data["pets"] = pets_raw
    return data


def suggested_profile_output_path(profile: dict[str, Any], fmt: str = "lst") -> str:
    """Default output path in cwd: <name-slug>.<ext> from export format."""
    slug = _slug_from_name(profile.get("full_name", "") or "")
    if not slug:
        slug = f"profile_{uuid.uuid4().hex[:8]}"
    return str(Path.cwd() / f"{slug}{_format_extension(fmt)}")


def default_profile_output_path(profile: dict[str, Any]) -> str:
    """Legacy default (lst in /tmp) - prefer suggested_profile_output_path."""
    slug = _slug_from_name(profile.get("full_name", "") or "")
    if not slug:
        slug = f"profile_{uuid.uuid4().hex[:8]}"
    return str(DEFAULT_OUTPUT_DIR / f"{slug}.lst")


def normalize_profile_output_path(
    raw: str,
    profile: dict[str, Any],
    fmt: str = "lst",
) -> str:
    """
    Resolve interactive output path.

    - Empty -> suggested path in cwd using profile name + format extension
    - Absolute path or path with directory -> use as-is (mkdir on write)
    - Bare filename -> current working directory; adds extension if missing
    """
    raw = (raw or "").strip()
    if not raw:
        return suggested_profile_output_path(profile, fmt)
    p = Path(raw).expanduser()
    target = p if (p.is_absolute() or p.parent != Path(".")) else Path.cwd() / p.name
    if not target.suffix and fmt in ("lst", "txt", "zip", "tar"):
        ext = _format_extension(fmt)
        if ext == ".tar.gz":
            target = target.with_name(target.name + ext)
        else:
            target = target.with_suffix(ext)
    return str(target)


def resolve_profile_output(cli_output: str | None, profile: dict[str, Any]) -> str | None:
    """CLI -o wins; else interactive output_path; else None (stdout)."""
    fmt = (profile.get("output") or {}).get("format", "lst")
    if cli_output:
        return normalize_profile_output_path(cli_output, profile, fmt)
    if profile.get("output_path"):
        return profile["output_path"]  # type: ignore[no-any-return]
    return None

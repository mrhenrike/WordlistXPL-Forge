"""PlateXPL: offline structural plate catalog, normalization and synthetic data.

This module does not query vehicle registries and does not determine actual issuance.
Input plate identifiers are only processed when explicitly supplied by the user.
Only western charsets (A-Z, 0-9) are supported; oriental scripts are excluded.

Autor: Andre Henrique (@mrhenrike) | Uniao Geek
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__info__: dict[str, Any] = {
    "name": "plate_gen",
    "version": "1.0.0",
    "category": "generation",
    "description": "Structural vehicle plate catalog, normalization and synthetic data (western charsets only)",
    "author": "Andre Henrique (@mrhenrike)",
}

ALPHABET: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS: str = "0123456789"


class UnsupportedPlatePattern(ValueError):
    """Regex syntax exceeds the bounded supported grammar."""


def normalize_plate(value: str) -> str:
    """Upper case and remove all non-ASCII-letter/non-digit characters.

    Only western (ASCII) letters and digits are accepted.
    """
    if not isinstance(value, str):
        raise TypeError("plate must be a string")
    clean = "".join(c.upper() for c in value if c.isascii() and (c.isalpha() or c.isdigit()))
    if not clean or len(clean) > 24:
        raise ValueError("plate must contain 1 to 24 ASCII alphanumeric characters")
    return clean


def catalog(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        default_path = Path(__file__).parent / "data" / "license_plate_patterns.json"
        content = default_path.read_text(encoding="utf-8")
    else:
        content = Path(path).read_text(encoding="utf-8")
    result: dict[str, Any] = json.loads(content)
    if result.get("schema_version") != "1.0.0":
        raise ValueError("unsupported plate catalog schema")
    return result


def country_record(iso2: str, db: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source = db if db is not None else catalog()
    code = iso2.strip().upper()
    countries: Any = source["countries"]
    try:
        result: dict[str, Any] = countries[code]
        return result
    except KeyError as exc:
        raise ValueError(f"unknown ISO2 code: {code}") from exc


def check_plate(
    plate: str,
    iso2: str,
    db: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate structural shape only, never actual registration/ownership."""
    normalized = normalize_plate(plate)
    entry = country_record(iso2, db)
    matched: list[dict[str, str]] = []
    for rule in entry["patterns"]:
        if re.fullmatch(rule["regex"], normalized) is not None:
            matched.append({"id": rule["id"], "status": rule["status"], "category": rule["category"]})
    return {
        "country": entry["iso2"],
        "normalized": normalized,
        "matches": matched,
        "structural_match": bool(matched),
        "verified_issuance": False,
        "catalog_status": entry["status"],
        "notes": "A regex match is not evidence the plate was issued or belongs to anyone.",
    }


def normalize_profile_plates(profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Parse plates supplied voluntarily in personal/corporate profile JSON/YAML.

    Accepted forms: ``plates: ["ABC-1234", ...]`` or
    ``vehicles: [{plate: "ABC-1234", country: "BR"}, ...]``.
    Never infers other plates or makes reverse lookups.
    """
    inputs: list[Any] = []
    for field_name in ("plates", "vehicles"):
        value = profile.get(field_name, [])
        if value is None:
            continue
        if isinstance(value, (str, dict)):
            value = [value]
        if not isinstance(value, list):
            raise TypeError(f"{field_name} must be a string, mapping or list")
        inputs.extend(value)
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for value in inputs:
        if isinstance(value, str):
            value = {"plate": value}
        if not isinstance(value, dict) or not isinstance(value.get("plate"), str):
            raise TypeError("vehicle entry must contain string plate")
        plate = normalize_plate(value["plate"])
        country = str(value.get("country") or profile.get("country") or "").strip().upper()
        if country and (len(country) != 2 or not country.isascii() or not country.isalpha()):
            raise ValueError(f"invalid country ISO2: {country}")
        key = (country, plate)
        if key not in seen:
            seen.add(key)
            result.append({"plate": plate, "country": country or None, "source": "operator_input"})
    return result


@dataclass(frozen=True)
class PatternShape:
    charsets: tuple[str, ...]

    def notation(self) -> str:
        def label(chars: str) -> str:
            if chars == ALPHABET:
                return "L"
            if chars == DIGITS:
                return "N"
            if len(chars) == 1:
                return "{" + chars + "}"
            return "X"
        return "".join(label(chars) for chars in self.charsets)


def _parse_charset(text: str) -> str:
    """Supports simple character classes and ranges (ASCII only)."""
    chars: list[str] = []
    i = 0
    while i < len(text):
        if i + 2 < len(text) and text[i + 1] == "-":
            lo, hi = ord(text[i]), ord(text[i + 2])
            if lo > hi or hi - lo > 200:
                raise UnsupportedPlatePattern("invalid/oversized character range")
            if hi > 127:
                raise UnsupportedPlatePattern("non-ASCII character range not supported")
            chars.extend(map(chr, range(lo, hi + 1)))
            i += 3
        else:
            if text[i] in "]\\^":
                raise UnsupportedPlatePattern("unsupported character class syntax")
            if ord(text[i]) > 127:
                raise UnsupportedPlatePattern("non-ASCII character not supported")
            chars.append(text[i])
            i += 1
    return "".join(dict.fromkeys(chars))


def parse_plate_pattern(regex: str, *, max_shapes: int = 300) -> list[PatternShape]:
    """Convert a restricted community regex into positional charsets.

    Supports alternatives, letters, digits, classes, ?, {n}, {m,n}.
    Rejects lookarounds, groups, unbounded repetition and arbitrary regexes.
    """
    shapes: list[PatternShape] = []
    for branch in regex.split("|"):
        branch = branch.removeprefix("^").removesuffix("$")
        i = 0
        all_slots: list[tuple[str, int, int]] = []
        while i < len(branch):
            c = branch[i]
            if c == "[":
                end = branch.find("]", i + 1)
                if end == -1:
                    raise UnsupportedPlatePattern("unclosed class")
                chars = _parse_charset(branch[i + 1 : end])
                i = end + 1
            elif branch.startswith(r"\d", i):
                chars = DIGITS
                i += 2
            elif c in ALPHABET or c in DIGITS:
                chars = c
                i += 1
            else:
                raise UnsupportedPlatePattern(f"unsupported regex token {c!r}")
            if i < len(branch) and branch[i] == "?":
                low, high = 0, 1
                i += 1
            elif i < len(branch) and branch[i] == "{":
                end = branch.find("}", i + 1)
                if end == -1:
                    raise UnsupportedPlatePattern("unclosed repetition")
                quant = branch[i + 1 : end]
                if not re.fullmatch(r"\d{1,2}(,\d{1,2})?", quant):
                    raise UnsupportedPlatePattern("unbounded repetition")
                vals = [int(v) for v in quant.split(",")]
                low, high = (vals[0], vals[-1])
                i = end + 1
            else:
                low = high = 1
            if high < low or high > 15:
                raise UnsupportedPlatePattern("bad repeat bounds")
            all_slots.append((chars, low, high))
        partial: list[tuple[str, ...]] = [()]
        for chars, low, high in all_slots:
            next_shapes: list[tuple[str, ...]] = []
            for shape in partial:
                for n in range(low, high + 1):
                    if len(next_shapes) >= max_shapes:
                        raise UnsupportedPlatePattern("too many expanded shapes")
                    next_shapes.append(shape + (chars,) * n)
            partial = next_shapes
        shapes.extend(PatternShape(x) for x in partial if x)
        if len(shapes) > max_shapes:
            raise UnsupportedPlatePattern("too many expanded shapes")
    return shapes


def country_charsets(iso2: str, db: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    record = country_record(iso2, db)
    result: list[dict[str, Any]] = []
    for item in record["patterns"]:
        shapes = parse_plate_pattern(item["regex"])
        result.append(
            {
                "id": item["id"],
                "source": item["source"],
                "status": item["status"],
                "shapes": sorted({s.notation() for s in shapes}),
                "charset_sizes": sorted({len(c) for s in shapes for c in s.charsets}),
                "variant_count": len(shapes),
            }
        )
    return result


def generate_synthetic_plates(
    iso2: str,
    *,
    limit: int = 25,
    seed: int | None = None,
    db: Mapping[str, Any] | None = None,
) -> Iterator[str]:
    """Bounded synthetic plate-shaped identifiers for QA/regex tests.

    Does not generate an authoritative registry or guarantee identifiers are unissued.
    Numeric/letter streams are sampled rather than exhausted.
    """
    if not 1 <= limit <= 10_000:
        raise ValueError("limit must be between 1 and 10000")
    entry = country_record(iso2, db)
    if not entry["patterns"]:
        raise ValueError(f"no research-backed patterns are available for {iso2}")
    shapes = [s for p in entry["patterns"] for s in parse_plate_pattern(p["regex"])]
    rng = random.Random(seed)
    emitted: set[str] = set()
    attempts = 0
    while len(emitted) < limit and attempts < max(500, limit * 30):
        attempts += 1
        shape = rng.choice(shapes)
        value = "".join(rng.choice(chars) for chars in shape.charsets)
        if value not in emitted:
            emitted.add(value)
            yield value


def ask_vehicle_plates(*, locale: str = "en") -> list[dict[str, Any]]:
    """Optional wizard to capture zero, one or many explicitly provided plates."""
    portuguese = locale.lower().startswith("pt")
    header = (
        "Placas de veiculos (pessoal ou empresarial). Enter para encerrar: "
        if portuguese
        else "Vehicle plates (personal or company). Enter to finish: "
    )
    country_prompt = (
        "Pais ISO2 da placa (ex.: BR, opcional): "
        if portuguese
        else "Plate country ISO2 (e.g., BR, optional): "
    )
    inputs: list[dict[str, str]] = []
    while True:
        raw = input(header).strip()
        if not raw:
            break
        try:
            plate = normalize_plate(raw)
            cc = input(country_prompt).strip().upper()
            if cc and (len(cc) != 2 or not cc.isascii() or not cc.isalpha()):
                raise ValueError("country must be two ISO letters")
            inputs.append({"plate": plate, "country": cc})
        except ValueError as exc:
            print(f"  Invalid plate: {exc}")
    return normalize_profile_plates({"vehicles": inputs})


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="PlateXPL structural plate catalog / synthetic QA generator"
    )
    parser.add_argument("--db", help="Alternate local JSON catalog")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("countries", help="List countries and catalog statuses")
    p = sub.add_parser("check", help="Check a plate against an explicitly specified country")
    p.add_argument("--country", required=True)
    p.add_argument("--plate", required=True)
    p = sub.add_parser("charsets", help="Show positional charsets/masks")
    p.add_argument("--country", required=True)
    p = sub.add_parser("synthetic", help="Generate limited synthetic plate-like values for QA")
    p.add_argument("--country", required=True)
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    db = catalog(args.db)
    if args.command == "countries":
        for iso, entry in db["countries"].items():
            print(f"{iso}\t{entry['name']}\t{entry['status']}")
    elif args.command == "check":
        print(json.dumps(check_plate(args.plate, args.country, db), ensure_ascii=False, indent=2))
    elif args.command == "charsets":
        print(json.dumps(country_charsets(args.country, db), ensure_ascii=False, indent=2))
    elif args.command == "synthetic":
        for value in generate_synthetic_plates(args.country, limit=args.limit, seed=args.seed, db=db):
            print(value)
    return 0


def run(
    iso2: str = "BR",
    command: str = "synthetic",
    limit: int = 25,
    seed: int | None = None,
    db_path: str = "",
) -> list[str]:
    """WLF module contract: generate synthetic plates or check structural patterns."""
    db = catalog(db_path or None)
    if command == "countries":
        return [f"{iso}\t{e['name']}\t{e['status']}" for iso, e in db["countries"].items()]
    if command == "synthetic":
        return list(generate_synthetic_plates(iso2, limit=limit, seed=seed, db=db))
    if command == "charsets":
        return [json.dumps(c, ensure_ascii=False) for c in country_charsets(iso2, db)]
    return []


if __name__ == "__main__":
    raise SystemExit(main())

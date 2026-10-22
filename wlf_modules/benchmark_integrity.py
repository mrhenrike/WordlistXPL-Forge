"""Read-only integrity checks for WordlistXPL benchmark reports.

Autor: Andre Henrique (@mrhenrike) | Uniao Geek
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__info__: dict[str, Any] = {
    "name": "benchmark_integrity",
    "version": "1.0.0",
    "category": "audit",
    "description": "Rejects duplicate JSON keys and flags non-monotonic hit@N metrics",
    "author": "Andre Henrique (@mrhenrike)",
}


class DuplicateJSONKey(ValueError):
    """A JSON object has a repeated member name, which would discard data."""


def _reject_duplicate_object_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateJSONKey(f"Duplicate JSON key: {key}")
        out[key] = value
    return out


def load_benchmark_strict(path: str | Path) -> Any:
    """Load JSON with duplicate-key rejection (no credentials processed)."""
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(
            handle, object_pairs_hook=_reject_duplicate_object_keys
        )


def validate_hit_rates(payload: Any) -> list[str]:
    """Flag inconsistent hit@N ordering; leaves metric scaling unchanged."""
    warnings: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            rates = [
                (int(k.split("@", 1)[1]), float(v))
                for k, v in value.items()
                if isinstance(k, str)
                and k.startswith("hit@")
                and k.split("@", 1)[1].isdigit()
                and isinstance(v, (int, float))
            ]
            rates.sort()
            for (prev_n, prev_v), (next_n, next_v) in zip(rates, rates[1:]):  # noqa: RUF007
                if next_v < prev_v:
                    warnings.append(
                        f"{path}: hit@{next_n} below hit@{prev_n}"
                    )
            for k, v in value.items():
                walk(v, path + "." + str(k))
        elif isinstance(value, list):
            for i, child in enumerate(value):
                walk(child, path + f"[{i}]")

    walk(payload, "$")
    return warnings


def run(path: str = "") -> list[str]:
    """WLF module contract: validate a benchmark JSON file."""
    if not path:
        return ["Usage: provide path to benchmark JSON file"]
    report = load_benchmark_strict(path)
    return validate_hit_rates(report)

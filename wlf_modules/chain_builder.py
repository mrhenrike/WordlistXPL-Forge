"""
chain_builder.py: Multi-stage rule chain builder for password generation.

Defines transformation chains where each stage holds a list of transforms.
The engine computes the cartesian product across stages, generating all
combinations of transformations applied in sequence to each base word.

Inspired by Mentalist (sc0tfree/mentalist) chain architecture.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
import math
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

_LEET_MAP: dict[str, str] = {
    "a": "4", "e": "3", "i": "1", "o": "0",
    "s": "5", "t": "7", "g": "9", "b": "8",
}

_COMMON_SPECIALS = ["!", "@", "#", "$", "%", ".", "*", "_", "-", "?"]
_COMMON_YEARS = [str(y) for y in range(2015, 2027)]
_COMMON_NUMS = [str(n) for n in range(100)]


def _apply_leet(word: str) -> str:
    result = word.lower()
    for orig, repl in _LEET_MAP.items():
        result = result.replace(orig, repl)
    return result


def _apply_capitalize(word: str) -> str:
    return word.capitalize()


def _apply_upper(word: str) -> str:
    return word.upper()


def _apply_lower(word: str) -> str:
    return word.lower()


def _apply_reverse(word: str) -> str:
    return word[::-1]


def _apply_toggle(word: str) -> str:
    return word.swapcase()


def _apply_duplicate(word: str) -> str:
    return word + word


_TRANSFORM_REGISTRY: dict[str, Any] = {
    "noop": lambda w: w,
    "capitalize": _apply_capitalize,
    "upper": _apply_upper,
    "lower": _apply_lower,
    "leet": _apply_leet,
    "reverse": _apply_reverse,
    "toggle": _apply_toggle,
    "duplicate": _apply_duplicate,
}


def _expand_transform(name: str, args: dict[str, Any] | None = None) -> list[Any]:
    """Expand a named transform into callable(s).

    Special multi-value transforms:
      - append_special: one callable per special char
      - append_year: one callable per common year
      - append_num: one callable per number 0-99
      - prepend_special: one callable per special char
      - append_custom: requires args['values']
      - prepend_custom: requires args['values']
    """
    args = args or {}

    if name in _TRANSFORM_REGISTRY:
        return [_TRANSFORM_REGISTRY[name]]

    if name == "append_special":
        chars = args.get("chars", _COMMON_SPECIALS)
        return [lambda w, s=s: w + s for s in chars]

    if name == "append_year":
        years = args.get("years", _COMMON_YEARS)
        return [lambda w, y=y: w + y for y in years]

    if name == "append_num":
        nums = args.get("range", _COMMON_NUMS)
        return [lambda w, n=n: w + n for n in nums]

    if name == "prepend_special":
        chars = args.get("chars", _COMMON_SPECIALS)
        return [lambda w, s=s: s + w for s in chars]

    if name == "append_custom":
        values = args.get("values", [])
        return [lambda w, v=v: w + str(v) for v in values]

    if name == "prepend_custom":
        values = args.get("values", [])
        return [lambda w, v=v: str(v) + w for v in values]

    raise ValueError(f"Unknown transform: {name}")


@dataclass
class Stage:
    """A single stage in a transformation chain."""

    name: str
    transforms: list[dict[str, Any]]

    def expand(self) -> list[Any]:
        """Expand all transforms in this stage into callables."""
        callables: list[Any] = []
        for t in self.transforms:
            tname = t.get("name", t.get("type", ""))
            targs = t.get("args", {})
            callables.extend(_expand_transform(tname, targs))
        return callables

    @property
    def width(self) -> int:
        return len(self.expand())


@dataclass
class Chain:
    """Multi-stage transformation chain."""

    name: str
    stages: list[Stage] = field(default_factory=list)
    description: str = ""

    def add_stage(self, name: str, transforms: list[dict[str, Any]]) -> "Chain":
        self.stages.append(Stage(name=name, transforms=transforms))
        return self

    def total_combinations(self) -> int:
        """Total number of transform combinations across all stages."""
        if not self.stages:
            return 0
        total = 1
        for stage in self.stages:
            total *= stage.width
        return total

    def estimate_candidates(self, base_count: int) -> int:
        """Estimate total candidates: base_words x combinations."""
        return base_count * self.total_combinations()

    def estimate_size_mb(self, base_count: int, avg_len: int = 10) -> float:
        """Rough estimate of output size in MB."""
        candidates = self.estimate_candidates(base_count)
        return round(candidates * (avg_len + 1) / (1024 * 1024), 2)

    def generate(self, base_words: Iterable[str]) -> Generator[str, None, None]:
        """Apply the chain to base words, yielding all candidates."""
        if not self.stages:
            yield from base_words
            return

        stage_callables = [s.expand() for s in self.stages]

        for word in base_words:
            word = word.rstrip("\n\r")
            if not word:
                continue
            for combo in product(*stage_callables):
                result = word
                for fn in combo:
                    result = fn(result)
                yield result

    def dry_run(self, sample_words: list[str], limit: int = 20) -> list[str]:
        """Generate a small sample for chain preview."""
        results: list[str] = []
        gen = self.generate(iter(sample_words))
        for _ in range(limit):
            try:
                results.append(next(gen))
            except StopIteration:
                break
        return results


def chain_from_dict(data: dict[str, Any]) -> Chain:
    """Build a Chain from a dictionary (JSON/YAML parsed)."""
    chain = Chain(
        name=data.get("name", "unnamed"),
        description=data.get("description", ""),
    )
    for stage_data in data.get("stages", []):
        chain.add_stage(
            name=stage_data.get("name", "stage"),
            transforms=stage_data.get("transforms", []),
        )
    return chain


def chain_from_json(path: Path) -> Chain:
    """Load a chain definition from a JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return chain_from_dict(data)


def chain_to_dict(chain: Chain) -> dict[str, Any]:
    """Serialize a Chain to a dictionary."""
    return {
        "name": chain.name,
        "description": chain.description,
        "stages": [
            {
                "name": s.name,
                "transforms": s.transforms,
            }
            for s in chain.stages
        ],
    }


def chain_to_json(chain: Chain, path: Path) -> None:
    """Save a chain definition to a JSON file."""
    path.write_text(json.dumps(chain_to_dict(chain), indent=2), encoding="utf-8")


# Pre-built chains for common scenarios

def chain_basic_mangling() -> Chain:
    """Standard password mangling: case + leet + suffix."""
    return (
        Chain(name="basic_mangling", description="Case variations + leet + number/special suffix")
        .add_stage("case", [
            {"name": "noop"},
            {"name": "capitalize"},
            {"name": "upper"},
            {"name": "toggle"},
        ])
        .add_stage("leet", [
            {"name": "noop"},
            {"name": "leet"},
        ])
        .add_stage("suffix", [
            {"name": "noop"},
            {"name": "append_special"},
            {"name": "append_year"},
        ])
    )


def chain_corporate_pattern() -> Chain:
    """Corporate password patterns: capitalize + year + special."""
    return (
        Chain(name="corporate", description="Corporate password patterns (Name2024!, etc.)")
        .add_stage("case", [
            {"name": "capitalize"},
        ])
        .add_stage("year", [
            {"name": "noop"},
            {"name": "append_year"},
        ])
        .add_stage("special", [
            {"name": "noop"},
            {"name": "append_special"},
        ])
    )


def chain_aggressive() -> Chain:
    """Aggressive chain: all transforms x all suffixes. Large output."""
    return (
        Chain(name="aggressive", description="Exhaustive combination of all transforms and suffixes")
        .add_stage("case", [
            {"name": "noop"},
            {"name": "capitalize"},
            {"name": "upper"},
            {"name": "lower"},
            {"name": "toggle"},
        ])
        .add_stage("mutation", [
            {"name": "noop"},
            {"name": "leet"},
            {"name": "reverse"},
            {"name": "duplicate"},
        ])
        .add_stage("suffix", [
            {"name": "noop"},
            {"name": "append_special"},
            {"name": "append_year"},
            {"name": "append_num"},
        ])
    )

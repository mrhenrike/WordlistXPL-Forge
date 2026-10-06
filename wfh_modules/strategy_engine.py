"""strategy_engine.py - Lightweight PBMP-style mutation-strategy planner.

Infers which generator families should dominate given profile / DNA / population
priors, without requiring a full neural stack.

P(Strategy | History, Context, Behavior, Population) ≈ softmax(weights)

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


STRATEGIES = (
    "rules_mangle",
    "mask_cartesian",
    "markov_omen",
    "pcfg_structure",
    "semantic_pcfg",
    "prince_chains",
    "pattern_templates",
    "neural_lstm",
)


@dataclass
class StrategyPlan:
    weights: dict[str, float] = field(default_factory=dict)
    engines: list[dict[str, Any]] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)

    def top(self, k: int = 3) -> list[tuple[str, float]]:
        return sorted(self.weights.items(), key=lambda x: -x[1])[:k]


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    m = max(scores.values())
    ex = {k: math.exp(v - m) for k, v in scores.items()}
    z = sum(ex.values()) or 1.0
    return {k: v / z for k, v in ex.items()}


def plan_from_profile(profile: dict, has_model_markov: bool = False,
                      has_model_pcfg: bool = False,
                      has_neural: bool = False) -> StrategyPlan:
    """Derive engine mix from a personal/corporate profile dict."""
    raw: dict[str, float] = {s: 0.5 for s in STRATEGIES}
    notes: list[str] = []

    pets = profile.get("pets") or []
    keywords = profile.get("keywords") or []
    company = profile.get("company_name") or ""
    years = profile.get("special_dates") or []
    leet = (profile.get("leet_mode") or "basic").lower()

    if pets or keywords or company:
        raw["semantic_pcfg"] += 2.0
        raw["pattern_templates"] += 1.5
        raw["rules_mangle"] += 1.0
        notes.append("PII/tokens present → semantic PCFG + pattern templates")
    if years or profile.get("include_recent_years"):
        raw["pcfg_structure"] += 1.0
        raw["pattern_templates"] += 0.8
        notes.append("Temporal tokens → structure/year patterns")
    if leet in ("medium", "aggressive"):
        raw["rules_mangle"] += 1.2
        notes.append(f"leet_mode={leet} → mangling weight up")
    if has_model_markov:
        raw["markov_omen"] += 1.5
        notes.append("Markov model on disk")
    else:
        raw["markov_omen"] -= 0.5
    if has_model_pcfg:
        raw["pcfg_structure"] += 1.5
        notes.append("PCFG grammar on disk")
    else:
        raw["pcfg_structure"] -= 0.3
    if has_neural:
        raw["neural_lstm"] += 1.0
    else:
        raw["neural_lstm"] -= 1.0

    # Always keep a little exploration on prince/mask
    raw["prince_chains"] += 0.4
    raw["mask_cartesian"] += 0.3

    weights = _softmax(raw)
    engines: list[dict[str, Any]] = []
    for name, w in sorted(weights.items(), key=lambda x: -x[1]):
        if w < 0.05:
            continue
        engines.append(_engine_spec(name, w, profile))
    return StrategyPlan(weights=weights, engines=engines, rationale=notes)


def _engine_spec(name: str, weight: float, profile: dict) -> dict[str, Any]:
    depth = int(profile.get("depth") or 3)
    limit = max(1_000, int(50_000 * weight * (depth / 3)))
    base = {"strategy": name, "weight": round(weight, 4), "limit": limit}
    if name == "pattern_templates":
        company = profile.get("company_name") or "BrandX"
        pets = profile.get("pets") or [{"name": "PetX"}]
        pet = pets[0]["name"] if isinstance(pets[0], dict) else str(pets[0])
        base["templates"] = [
            f"{{company}}#{{pet}}{{yy}}",
            f"_{{company}}@{{year}}#{{pet}}",
            f"#{{company}}@{{tag}}",
        ]
        base["vars"] = {
            "company": company,
            "pet": pet,
            "yy": "25",
            "year": "2026",
            "tag": "CS",
        }
    if name == "semantic_pcfg":
        base["semantic"] = True
    return base


def bayesian_structure_priors(profile: dict) -> dict[str, float]:
    """TarGuess-lite: P(H|E) over structure hypotheses given profile evidence."""
    hyps = {
        "NAME_YEAR": 0.2,
        "NAME_PET_YEAR": 0.15,
        "COMPANY_SEP_YEAR": 0.15,
        "WORD_DIGIT_SYMBOL": 0.25,
        "KEYBOARD_WALK": 0.1,
        "OTHER": 0.15,
    }
    if profile.get("pets"):
        hyps["NAME_PET_YEAR"] += 0.25
    if profile.get("company_name"):
        hyps["COMPANY_SEP_YEAR"] += 0.2
    if profile.get("full_name") or profile.get("short_name"):
        hyps["NAME_YEAR"] += 0.2
    z = sum(hyps.values()) or 1.0
    return {k: v / z for k, v in hyps.items()}


def format_plan(plan: StrategyPlan, priors: Optional[dict[str, float]] = None) -> str:
    lines = ["=== Generation strategy plan (PBMP-lite) ==="]
    for n, w in plan.top(8):
        lines.append(f"  {n:20s}  p={w:.3f}")
    if plan.rationale:
        lines.append("-- rationale --")
        for r in plan.rationale:
            lines.append(f"  * {r}")
    if priors:
        lines.append("-- structure hypotheses P(H|E) --")
        for h, p in sorted(priors.items(), key=lambda x: -x[1]):
            lines.append(f"  {h:20s}  {p:.3f}")
    lines.append("-- engine queue --")
    for e in plan.engines[:6]:
        lines.append(f"  {e}")
    return "\n".join(lines)


def models_on_disk(root: Path | None = None) -> dict[str, bool]:
    root = root or Path(".")
    return {
        "markov": (root / ".model" / "markov_model.json").exists(),
        "pcfg": (root / ".model" / "pcfg_grammar.json").exists(),
        "neural": (root / ".model" / "neural_lstm.pt").exists()
        or (root / ".model" / "char_lstm.pt").exists(),
    }

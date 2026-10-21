#!/usr/bin/env python3
"""
cogpie_real_benchmark.py - Benchmark CogPIE with real leak data.

Trains the HybridRanker on a processed corpus, then evaluates
hit rates across multiple budget tiers (hit@10, hit@100, hit@1k,
hit@10k, hit@100k) using held-out target passwords.

The benchmark simulates online attack scenarios where an attacker
has PII about the target and a limited number of guesses.

Evaluation protocol:
  1. Split corpus into train (90%) and test (10%)
  2. For each test password, extract PII features
  3. Generate CogPIE candidates using those features
  4. Measure if the real password appears within budget K

Usage:
  python tools/cogpie_real_benchmark.py --corpus ./corpus/processed_corpus.txt
  python tools/cogpie_real_benchmark.py --corpus ./corpus/processed_corpus.txt --budget 100000

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wlf_modules.cogpie.engine import CogPIEEngine
from wlf_modules.cogpie.pii_correlator import _detect_date, _detect_name, correlate_password

logger = logging.getLogger("cogpie.benchmark")

BUDGET_TIERS = [10, 100, 1_000, 10_000, 100_000]


def _extract_synthetic_profile(password: str) -> dict | None:
    """Extract a synthetic target profile from a password's PII content.

    This simulates the scenario where an attacker has PII matching
    what the user embedded in their password. Returns None if no
    PII is detectable (can't build a meaningful profile).
    """
    name, lang = _detect_name(password)
    date_val, date_type = _detect_date(password)

    if not name and not date_val:
        return None

    profile: dict = {
        "names": [],
        "dates": [],
        "keywords": [],
        "pets": [],
        "companies": [],
        "phones": [],
        "emails": [],
        "old_passwords": [],
        "numbers": [],
    }

    if name:
        profile["names"].append(name)
    if date_val:
        profile["dates"].append(date_val)
        profile["numbers"].append(date_val)

    residue = password.lower()
    if name:
        residue = residue.replace(name, "")
    if date_val:
        residue = residue.replace(date_val, "")
    residue = residue.strip()
    if residue and len(residue) >= 3 and residue.isalpha():
        profile["keywords"].append(residue)

    return profile


def load_corpus(filepath: str, max_lines: int = 0) -> list[str]:
    """Load passwords from a file."""
    passwords = []
    with open(filepath, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            pw = line.rstrip("\n\r")
            if pw:
                passwords.append(pw)
                if max_lines and len(passwords) >= max_lines:
                    break
    return passwords


def split_corpus(
    passwords: list[str],
    test_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[list[str], list[str]]:
    """Split into train/test with PII-only test set."""
    rng = random.Random(seed)
    shuffled = list(passwords)
    rng.shuffle(shuffled)

    pii_passwords = []
    non_pii_passwords = []

    for pw in shuffled:
        result = correlate_password(pw)
        if result.category in ("name_based", "date_based", "hybrid"):
            pii_passwords.append(pw)
        else:
            non_pii_passwords.append(pw)

    test_size = max(int(len(pii_passwords) * test_ratio), 50)
    test_set = pii_passwords[:test_size]
    train_set = pii_passwords[test_size:] + non_pii_passwords

    return train_set, test_set


def run_benchmark(
    corpus_path: str,
    output_dir: str,
    max_train: int = 0,
    max_test: int = 500,
    budgets: list[int] | None = None,
    seed: int = 42,
) -> dict:
    """Execute the full benchmark.

    Returns results dict with hit rates per budget tier.
    """
    if budgets is None:
        budgets = list(BUDGET_TIERS)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    logger.info("Loading corpus: %s", corpus_path)
    all_passwords = load_corpus(corpus_path, max_lines=max_train if max_train else 0)
    logger.info("Loaded %d passwords", len(all_passwords))

    logger.info("Splitting train/test (test PII-only)...")
    train_set, test_set = split_corpus(all_passwords, test_ratio=0.1, seed=seed)
    if len(test_set) > max_test:
        test_set = test_set[:max_test]
    logger.info("Train: %d, Test: %d (PII-bearing)", len(train_set), len(test_set))

    train_path = out / "_train_split.txt"
    with open(train_path, "w", encoding="utf-8") as f:
        for pw in train_set:
            f.write(pw + "\n")

    logger.info("Training CogPIE engine...")
    t0 = time.monotonic()
    engine = CogPIEEngine(alpha=0.4, beta=0.2, markov_order=3)
    trained = engine.train(str(train_path), max_lines=0)
    train_time = time.monotonic() - t0
    logger.info("Trained on %d passwords in %.1fs", trained, train_time)

    max_budget = max(budgets)
    hits_at: dict[int, int] = {k: 0 for k in budgets}
    test_details: list[dict] = []

    logger.info("Evaluating %d test targets (max budget %d)...", len(test_set), max_budget)
    t1 = time.monotonic()

    for idx, target_pw in enumerate(test_set):
        profile = _extract_synthetic_profile(target_pw)
        if profile is None:
            continue

        candidates = engine.generate(
            profile=profile,
            policy=None,
            max_candidates=max_budget,
        )

        candidate_set = [c for c, _ in candidates]
        found_at = None
        for rank, c in enumerate(candidate_set, 1):
            if c == target_pw:
                found_at = rank
                break

        detail = {
            "target": target_pw,
            "profile": profile,
            "found_at_rank": found_at,
            "total_candidates": len(candidate_set),
        }
        test_details.append(detail)

        if found_at is not None:
            for k in budgets:
                if found_at <= k:
                    hits_at[k] += 1

        if (idx + 1) % 50 == 0:
            logger.info(
                "  ... %d/%d evaluated (hit@%d so far: %.1f%%)",
                idx + 1, len(test_set), max_budget,
                hits_at[max_budget] / (idx + 1) * 100,
            )

    eval_time = time.monotonic() - t1
    total_evaluated = len(test_details)

    results: dict[str, float] = {}
    for k in budgets:
        rate = hits_at[k] / max(total_evaluated, 1) * 100
        results[f"hit@{k}"] = round(rate, 2)

    summary = {
        "corpus": corpus_path,
        "train_size": len(train_set),
        "test_size": total_evaluated,
        "train_time_seconds": round(train_time, 2),
        "eval_time_seconds": round(eval_time, 2),
        "budget_tiers": budgets,
        "hit_rates": results,
        "hits_raw": {f"hit@{k}": hits_at[k] for k in budgets},
        "engine_params": {
            "alpha": 0.4,
            "beta": 0.2,
            "markov_order": 3,
        },
    }

    results_path = out / "benchmark_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    details_path = out / "benchmark_details.json"
    with open(details_path, "w", encoding="utf-8") as f:
        json.dump(test_details, f, indent=2, ensure_ascii=False)

    logger.info("Benchmark complete in %.1fs", eval_time)
    for k in budgets:
        logger.info("  hit@%d: %.2f%% (%d/%d)", k, results[f"hit@{k}"], hits_at[k], total_evaluated)
    logger.info("Results: %s", results_path)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CogPIE Real Benchmark: evaluate with real leak data"
    )
    parser.add_argument(
        "--corpus", "-c",
        required=True,
        help="Path to processed corpus file",
    )
    parser.add_argument(
        "--output", "-o",
        default="./benchmark_output",
        help="Output directory for results",
    )
    parser.add_argument(
        "--max-train",
        type=int,
        default=0,
        help="Max training passwords (0 = all)",
    )
    parser.add_argument(
        "--max-test",
        type=int,
        default=500,
        help="Max test targets to evaluate",
    )
    parser.add_argument(
        "--budgets",
        nargs="+",
        type=int,
        default=None,
        help="Budget tiers to evaluate (default: 10 100 1000 10000 100000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    summary = run_benchmark(
        corpus_path=args.corpus,
        output_dir=args.output,
        max_train=args.max_train,
        max_test=args.max_test,
        budgets=args.budgets,
        seed=args.seed,
    )

    print("\nBenchmark Results:")
    print(f"  Train: {summary['train_size']:,} | Test: {summary['test_size']:,}")
    print(f"  Train time: {summary['train_time_seconds']:.1f}s")
    print(f"  Eval time: {summary['eval_time_seconds']:.1f}s")
    for k, v in summary["hit_rates"].items():
        print(f"  {k}: {v:.2f}%")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
cogpie_comparison_benchmark.py - Compare CogPIE against baseline algorithms.

Evaluates password guessing algorithms on the same corpus and test set:
  - CogPIE (5-layer hybrid)
  - Pure Markov (character-level n-gram, order 3)
  - Frequency baseline (top-N from training set)
  - Levenshtein-based (edit distance from profile tokens)
  - CUPP-style (simple concatenation heuristics)
  - Random baseline (random sample from training vocab)

Produces JSON results and comparison tables for the research paper.

Usage:
  python tools/cogpie_comparison_benchmark.py \
    --corpus ./corpus/rockyou/processed_corpus.txt \
    --output ./benchmark/comparison \
    --max-test 500 -v

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
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wlf_modules.cogpie.engine import CogPIEEngine
from wlf_modules.cogpie.markov_pcfg_hybrid import HybridRanker
from wlf_modules.cogpie.pii_correlator import _detect_date, _detect_name, correlate_password

logger = logging.getLogger("cogpie.comparison")

BUDGET_TIERS = [10, 100, 1_000, 10_000, 100_000]


def _extract_profile(password: str) -> dict | None:
    """Extract synthetic PII profile from a password."""
    name, lang = _detect_name(password)
    date_val, date_type = _detect_date(password)
    if not name and not date_val:
        return None
    profile: dict = {
        "names": [], "dates": [], "keywords": [], "pets": [],
        "companies": [], "phones": [], "emails": [],
        "old_passwords": [], "numbers": [],
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


def load_and_split(
    corpus_path: str,
    max_lines: int = 0,
    test_ratio: float = 0.1,
    max_test: int = 500,
    seed: int = 42,
) -> tuple[list[str], list[str]]:
    """Load corpus and split into train/test (PII-bearing test set)."""
    passwords = []
    with open(corpus_path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            pw = line.rstrip("\n\r")
            if pw:
                passwords.append(pw)
                if max_lines and len(passwords) >= max_lines:
                    break

    rng = random.Random(seed)
    rng.shuffle(passwords)

    pii_passwords = []
    non_pii = []
    for pw in passwords:
        result = correlate_password(pw)
        if result.category in ("name_based", "date_based", "hybrid"):
            pii_passwords.append(pw)
        else:
            non_pii.append(pw)

    test_size = min(max_test, max(int(len(pii_passwords) * test_ratio), 50))
    test_set = pii_passwords[:test_size]
    train_set = pii_passwords[test_size:] + non_pii

    logger.info("Split: %d train, %d test (PII-bearing)", len(train_set), len(test_set))
    return train_set, test_set


# --- Baseline algorithms ---

class FrequencyBaseline:
    """Top-N most frequent passwords from training corpus."""

    def __init__(self) -> None:
        self.ranked: list[str] = []

    def train(self, passwords: list[str]) -> None:
        freq = Counter(passwords)
        self.ranked = [pw for pw, _ in freq.most_common()]

    def generate(self, profile: dict, budget: int) -> list[str]:
        return self.ranked[:budget]


class MarkovBaseline:
    """Pure character-level Markov chain generator."""

    def __init__(self, order: int = 3) -> None:
        self.ranker = HybridRanker(alpha=1.0, beta=0.0, markov_order=order)

    def train(self, passwords: list[str]) -> None:
        for pw in passwords:
            self.ranker.train(pw)

    def generate(self, profile: dict, budget: int) -> list[str]:
        all_tokens = []
        for key in ("names", "keywords", "dates", "numbers"):
            all_tokens.extend(profile.get(key, []))
        if not all_tokens:
            return []

        candidates = set()
        base = all_tokens[0] if all_tokens else "password"

        for length in range(4, 16):
            for _ in range(budget // 10):
                candidate = self._markov_generate(base, length)
                if candidate:
                    candidates.add(candidate)
                if len(candidates) >= budget:
                    break
            if len(candidates) >= budget:
                break

        scored = [(c, self.ranker.score(c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:budget]]

    def _markov_generate(self, seed: str, length: int) -> str | None:
        """Generate password seeded from a token using Markov transitions."""
        import random as rmod
        result = seed[:min(3, len(seed))]
        markov = self.ranker._markov
        for pos in range(len(result), length):
            ctx_len = min(markov.order, pos)
            ctx = result[-ctx_len:] if ctx_len > 0 else ""
            ngrams = markov._ngrams.get(pos, {}).get(ctx, None)
            if ngrams:
                chars = list(ngrams.keys())
                weights = list(ngrams.values())
                result += rmod.choices(chars, weights=weights, k=1)[0]
            else:
                result += rmod.choice("abcdefghijklmnopqrstuvwxyz0123456789")
        return result


class LevenshteinBaseline:
    """Edit-distance based ranking from profile tokens."""

    def __init__(self) -> None:
        self.vocab: list[str] = []

    def train(self, passwords: list[str]) -> None:
        self.vocab = list(set(passwords))

    def generate(self, profile: dict, budget: int) -> list[str]:
        tokens = []
        for key in ("names", "keywords", "dates", "numbers"):
            tokens.extend(profile.get(key, []))
        if not tokens:
            return self.vocab[:budget]

        primary = tokens[0].lower()
        scored = []
        sample_size = min(len(self.vocab), budget * 10)
        sample = self.vocab[:sample_size]

        for pw in sample:
            dist = self._levenshtein(primary, pw.lower())
            scored.append((pw, dist))

        scored.sort(key=lambda x: x[1])
        return [pw for pw, _ in scored[:budget]]

    @staticmethod
    def _levenshtein(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return LevenshteinBaseline._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                ins = prev[j + 1] + 1
                dele = curr[j] + 1
                sub = prev[j] + (0 if c1 == c2 else 1)
                curr.append(min(ins, dele, sub))
            prev = curr
        return prev[-1]


class CUPPBaseline:
    """CUPP-style concatenation: name + date, name + 123, etc."""

    SUFFIXES = [
        "", "1", "12", "123", "1234", "!", "@", "#",
        "01", "11", "13", "23", "69", "007",
        "2024", "2025", "2026",
    ]
    LEET_MAP = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$", "t": "7"}

    def train(self, passwords: list[str]) -> None:
        pass

    def generate(self, profile: dict, budget: int) -> list[str]:
        candidates = set()
        tokens = []
        for key in ("names", "keywords", "pets", "companies"):
            tokens.extend(profile.get(key, []))
        dates = profile.get("dates", []) + profile.get("numbers", [])

        for token in tokens:
            base_variants = [
                token, token.lower(), token.upper(), token.capitalize(),
            ]
            leet = token.lower()
            for c, r in self.LEET_MAP.items():
                leet = leet.replace(c, r)
            base_variants.append(leet)

            for base in base_variants:
                for suffix in self.SUFFIXES:
                    candidates.add(base + suffix)
                    if len(candidates) >= budget:
                        break
                for date in dates:
                    candidates.add(base + date)
                    candidates.add(date + base)
                    candidates.add(base + date[-2:] if len(date) >= 2 else base)
                if len(candidates) >= budget:
                    break

        for i, t1 in enumerate(tokens):
            for t2 in tokens[i + 1:]:
                candidates.add(t1 + t2)
                candidates.add(t2 + t1)
                candidates.add(t1.capitalize() + t2)
                candidates.add(t1 + t2.capitalize())

        return list(candidates)[:budget]


class RandomBaseline:
    """Random sampling from training vocabulary."""

    def __init__(self) -> None:
        self.vocab: list[str] = []

    def train(self, passwords: list[str]) -> None:
        self.vocab = list(set(passwords))

    def generate(self, profile: dict, budget: int) -> list[str]:
        rng = random.Random(42)
        if len(self.vocab) <= budget:
            return list(self.vocab)
        return rng.sample(self.vocab, budget)


def evaluate_algorithm(
    name: str,
    generate_fn,
    test_set: list[str],
    budgets: list[int],
) -> dict:
    """Evaluate a single algorithm across budget tiers."""
    max_budget = max(budgets)
    hits_at: dict[int, int] = {k: 0 for k in budgets}
    evaluated = 0
    total_time = 0.0

    for idx, target_pw in enumerate(test_set):
        profile = _extract_profile(target_pw)
        if profile is None:
            continue

        t0 = time.monotonic()
        candidates = generate_fn(profile, max_budget)
        total_time += time.monotonic() - t0
        evaluated += 1

        found_at = None
        for rank, c in enumerate(candidates, 1):
            if c == target_pw:
                found_at = rank
                break

        if found_at is not None:
            for k in budgets:
                if found_at <= k:
                    hits_at[k] += 1

        if (idx + 1) % 100 == 0:
            logger.info("  [%s] %d/%d evaluated", name, idx + 1, len(test_set))

    results = {}
    for k in budgets:
        rate = hits_at[k] / max(evaluated, 1) * 100
        results[f"hit@{k}"] = round(rate, 2)

    return {
        "algorithm": name,
        "evaluated": evaluated,
        "total_time_seconds": round(total_time, 2),
        "avg_time_per_target_ms": round(total_time / max(evaluated, 1) * 1000, 2),
        "hit_rates": results,
        "hits_raw": {f"hit@{k}": hits_at[k] for k in budgets},
    }


def run_comparison(
    corpus_path: str,
    output_dir: str,
    max_lines: int = 0,
    max_test: int = 500,
    budgets: list[int] | None = None,
    seed: int = 42,
) -> dict:
    """Run full comparison benchmark."""
    if budgets is None:
        budgets = list(BUDGET_TIERS)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    train_set, test_set = load_and_split(
        corpus_path, max_lines=max_lines, max_test=max_test, seed=seed,
    )

    train_path = out / "_train_split.txt"
    with open(train_path, "w", encoding="utf-8") as f:
        for pw in train_set:
            f.write(pw + "\n")

    logger.info("Training CogPIE...")
    cogpie = CogPIEEngine(alpha=0.4, beta=0.2, markov_order=3)
    cogpie.train(str(train_path), max_lines=0)

    logger.info("Training Markov baseline...")
    markov = MarkovBaseline(order=3)
    markov.train(train_set)

    logger.info("Training Frequency baseline...")
    freq = FrequencyBaseline()
    freq.train(train_set)

    logger.info("Training Levenshtein baseline...")
    lev = LevenshteinBaseline()
    lev.train(train_set)

    logger.info("Preparing CUPP baseline...")
    cupp = CUPPBaseline()

    logger.info("Preparing Random baseline...")
    rand = RandomBaseline()
    rand.train(train_set)

    algorithms = [
        ("CogPIE", lambda p, b: [c for c, _ in cogpie.generate(profile=p, policy=None, max_candidates=b)]),
        ("Markov-3", markov.generate),
        ("Frequency", freq.generate),
        ("Levenshtein", lev.generate),
        ("CUPP-style", cupp.generate),
        ("Random", rand.generate),
    ]

    all_results = []
    for name, gen_fn in algorithms:
        logger.info("Evaluating %s...", name)
        result = evaluate_algorithm(name, gen_fn, test_set, budgets)
        all_results.append(result)
        for k, v in result["hit_rates"].items():
            logger.info("  %s %s: %.2f%%", name, k, v)

    summary = {
        "corpus": corpus_path,
        "train_size": len(train_set),
        "test_size": len(test_set),
        "budget_tiers": budgets,
        "algorithms": all_results,
    }

    results_path = out / "comparison_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    table_path = out / "comparison_table.md"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write("# CogPIE Comparison Benchmark\n\n")
        f.write(f"Corpus: {corpus_path}\n")
        f.write(f"Train: {len(train_set):,} | Test: {len(test_set):,}\n\n")

        headers = ["Algorithm"] + [f"hit@{k}" for k in budgets] + ["Avg ms/target"]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"] * len(headers)) + "|\n")

        for r in all_results:
            row = [r["algorithm"]]
            for k in budgets:
                row.append(f"{r['hit_rates'][f'hit@{k}']:.2f}%")
            row.append(f"{r['avg_time_per_target_ms']:.1f}")
            f.write("| " + " | ".join(row) + " |\n")

    logger.info("Results: %s", results_path)
    logger.info("Table: %s", table_path)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CogPIE Comparison Benchmark: evaluate against baseline algorithms"
    )
    parser.add_argument("--corpus", "-c", required=True, help="Processed corpus file")
    parser.add_argument("--output", "-o", default="./benchmark/comparison", help="Output dir")
    parser.add_argument("--max-lines", type=int, default=0, help="Max training lines (0=all)")
    parser.add_argument("--max-test", type=int, default=500, help="Max test targets")
    parser.add_argument("--budgets", nargs="+", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    summary = run_comparison(
        corpus_path=args.corpus,
        output_dir=args.output,
        max_lines=args.max_lines,
        max_test=args.max_test,
        budgets=args.budgets,
        seed=args.seed,
    )

    print("\n=== Comparison Results ===")
    print(f"Train: {summary['train_size']:,} | Test: {summary['test_size']:,}\n")
    for r in summary["algorithms"]:
        rates = " | ".join(f"{k}: {v:.1f}%" for k, v in r["hit_rates"].items())
        print(f"  {r['algorithm']:15s} | {rates} | {r['avg_time_per_target_ms']:.1f}ms/target")


if __name__ == "__main__":
    main()

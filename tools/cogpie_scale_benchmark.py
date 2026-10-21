#!/usr/bin/env python3
"""
cogpie_scale_benchmark.py - Large-scale benchmark with real leak PII:password pairs.

Reads PII:password pairs extracted by cogpie_leak_extractor.py, feeds the PII
into each algorithm, and checks if the real password appears in the candidate
list. This is the definitive evaluation: real PII, real passwords, real scale.

Algorithms compared:
  - CogPIE (5-layer hybrid)
  - Pure Markov (character-level n-gram)
  - PCFG-only (structural decomposition)
  - Frequency baseline (top-N from corpus)
  - Levenshtein distance-based ranking
  - CUPP-style (simple concatenation)
  - Random baseline

Metrics:
  - hit@K for K in {10, 100, 1000, 10000, 100000}
  - Mean Reciprocal Rank (MRR)
  - Median rank of successful hits
  - Time per target (ms)
  - Coverage (% of targets hit at any budget)

Usage:
  python tools/cogpie_scale_benchmark.py \
    --pairs ./extracted/pii_password_pairs.jsonl \
    --train-corpus ./corpus/rockyou_full/processed_corpus.txt \
    --output ./benchmark/scale \
    --max-targets 1000 -v

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wlf_modules.cogpie.engine import CogPIEEngine
from wlf_modules.cogpie.markov_pcfg_hybrid import HybridRanker

logger = logging.getLogger("cogpie.scale_benchmark")

BUDGET_TIERS = [10, 100, 1_000, 10_000, 100_000]


# --- Baseline Algorithms (same as comparison but with train() API) ---

class FrequencyBaseline:
    def __init__(self):
        self.ranked = []

    def train(self, passwords):
        freq = Counter(passwords)
        self.ranked = [pw for pw, _ in freq.most_common()]

    def generate(self, profile, budget):
        return self.ranked[:budget]


class MarkovBaseline:
    def __init__(self, order=3):
        self.ranker = HybridRanker(alpha=1.0, beta=0.0, markov_order=order)

    def train(self, passwords):
        for pw in passwords:
            self.ranker.train(pw)

    def generate(self, profile, budget):
        tokens = []
        for key in ("names", "keywords", "dates", "numbers"):
            tokens.extend(profile.get(key, []))
        if not tokens:
            return []

        candidates = set()
        base = tokens[0]

        for length in range(4, 16):
            for _ in range(budget // 8):
                c = self._markov_gen(base, length)
                if c:
                    candidates.add(c)
                if len(candidates) >= budget:
                    break
            if len(candidates) >= budget:
                break

        scored = [(c, self.ranker.score(c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:budget]]

    def _markov_gen(self, seed, length):
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


class CUPPBaseline:
    SUFFIXES = ["", "1", "12", "123", "1234", "!", "@", "#", "01", "11", "13", "23", "69", "007",
                "2024", "2025", "2026"]
    LEET = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$", "t": "7"}

    def train(self, passwords):
        pass

    def generate(self, profile, budget):
        candidates = set()
        tokens = []
        for key in ("names", "keywords", "pets", "companies"):
            tokens.extend(profile.get(key, []))
        dates = profile.get("dates", []) + profile.get("numbers", [])

        for token in tokens:
            variants = [token, token.lower(), token.upper(), token.capitalize()]
            leet = token.lower()
            for c, r in self.LEET.items():
                leet = leet.replace(c, r)
            variants.append(leet)

            for base in variants:
                for suffix in self.SUFFIXES:
                    candidates.add(base + suffix)
                for date in dates:
                    candidates.add(base + date)
                    candidates.add(date + base)
                    if len(date) >= 2:
                        candidates.add(base + date[-2:])
                        candidates.add(base + date[-4:] if len(date) >= 4 else base)
                if len(candidates) >= budget:
                    break
            if len(candidates) >= budget:
                break

        for i, t1 in enumerate(tokens[:3]):
            for t2 in tokens[i + 1:4]:
                for sep in ("", "_", "."):
                    candidates.add(t1 + sep + t2)
                    candidates.add(t2 + sep + t1)
                    candidates.add(t1.capitalize() + sep + t2)
                    candidates.add(t1 + sep + t2.capitalize())

        return list(candidates)[:budget]


class LevenshteinBaseline:
    def __init__(self):
        self.vocab = []

    def train(self, passwords):
        self.vocab = list(set(passwords))

    def generate(self, profile, budget):
        tokens = []
        for key in ("names", "keywords", "dates", "numbers"):
            tokens.extend(profile.get(key, []))
        if not tokens:
            return self.vocab[:budget]

        primary = tokens[0].lower()
        sample_size = min(len(self.vocab), budget * 5)
        sample = self.vocab[:sample_size]

        scored = []
        for pw in sample:
            d = self._lev(primary, pw.lower())
            scored.append((pw, d))
        scored.sort(key=lambda x: x[1])
        return [pw for pw, _ in scored[:budget]]

    @staticmethod
    def _lev(s1, s2):
        if len(s1) < len(s2):
            return LevenshteinBaseline._lev(s2, s1)
        if not s2:
            return len(s1)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (0 if c1 == c2 else 1)))
            prev = curr
        return prev[-1]


class RandomBaseline:
    def __init__(self):
        self.vocab = []

    def train(self, passwords):
        self.vocab = list(set(passwords))

    def generate(self, profile, budget):
        rng = random.Random(42)
        if len(self.vocab) <= budget:
            return list(self.vocab)
        return rng.sample(self.vocab, budget)


def load_pairs(filepath: str, max_targets: int = 0, seed: int = 42) -> list[dict]:
    """Load PII:password pairs from JSONL."""
    pairs = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get("pii") and record.get("password"):
                    pairs.append(record)
            except json.JSONDecodeError:
                continue
            if max_targets and len(pairs) >= max_targets * 3:
                break

    if max_targets and len(pairs) > max_targets:
        rng = random.Random(seed)
        rng.shuffle(pairs)
        pairs = pairs[:max_targets]

    return pairs


def evaluate_algorithm(
    name: str,
    gen_fn,
    pairs: list[dict],
    budgets: list[int],
) -> dict:
    """Evaluate one algorithm on all pairs."""
    max_budget = max(budgets)
    hits_at = {k: 0 for k in budgets}
    ranks = []
    total_time = 0.0
    evaluated = 0

    for idx, record in enumerate(pairs):
        profile = record["pii"]
        target_pw = record["password"]

        t0 = time.monotonic()
        try:
            candidates = gen_fn(profile, max_budget)
        except Exception as exc:
            logger.debug("  [%s] error on target %d: %s", name, idx, exc)
            continue
        total_time += time.monotonic() - t0
        evaluated += 1

        found_at = None
        for rank, c in enumerate(candidates, 1):
            if c == target_pw:
                found_at = rank
                break

        if found_at is not None:
            ranks.append(found_at)
            for k in budgets:
                if found_at <= k:
                    hits_at[k] += 1

        if (idx + 1) % 200 == 0:
            logger.info(
                "  [%s] %d/%d (hit@%d: %.1f%%)",
                name, idx + 1, len(pairs), max_budget,
                hits_at[max_budget] / max(evaluated, 1) * 100,
            )

    hit_rates = {}
    for k in budgets:
        hit_rates[f"hit@{k}"] = round(hits_at[k] / max(evaluated, 1) * 100, 2)

    mrr = 0.0
    if ranks:
        mrr = sum(1.0 / r for r in ranks) / evaluated

    return {
        "algorithm": name,
        "evaluated": evaluated,
        "total_hits": len(ranks),
        "coverage_pct": round(len(ranks) / max(evaluated, 1) * 100, 2),
        "mrr": round(mrr, 6),
        "median_rank": int(statistics.median(ranks)) if ranks else None,
        "mean_rank": round(statistics.mean(ranks), 1) if ranks else None,
        "total_time_seconds": round(total_time, 2),
        "avg_time_per_target_ms": round(total_time / max(evaluated, 1) * 1000, 2),
        "hit_rates": hit_rates,
        "hits_raw": {f"hit@{k}": hits_at[k] for k in budgets},
    }


def run_scale_benchmark(
    pairs_path: str,
    train_corpus_path: str,
    output_dir: str,
    max_targets: int = 1000,
    max_train: int = 0,
    budgets: list[int] | None = None,
    seed: int = 42,
) -> dict:
    """Run full scale benchmark."""
    if budgets is None:
        budgets = list(BUDGET_TIERS)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    logger.info("Loading PII:password pairs...")
    pairs = load_pairs(pairs_path, max_targets=max_targets, seed=seed)
    logger.info("Loaded %d targets", len(pairs))

    logger.info("Loading training corpus...")
    train_passwords = []
    with open(train_corpus_path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            pw = line.rstrip("\n\r")
            if pw:
                train_passwords.append(pw)
                if max_train and len(train_passwords) >= max_train:
                    break
    logger.info("Training corpus: %d passwords", len(train_passwords))

    logger.info("Training algorithms...")

    cogpie = CogPIEEngine(alpha=0.4, beta=0.2, markov_order=3)
    train_path = out / "_train_corpus.txt"
    with open(train_path, "w", encoding="utf-8") as f:
        for pw in train_passwords:
            f.write(pw + "\n")
    cogpie.train(str(train_path), max_lines=max_train if max_train else 0)

    markov = MarkovBaseline(order=3)
    markov.train(train_passwords[:500_000])

    freq = FrequencyBaseline()
    freq.train(train_passwords)

    lev = LevenshteinBaseline()
    lev.train(train_passwords[:200_000])

    cupp = CUPPBaseline()
    rand_bl = RandomBaseline()
    rand_bl.train(train_passwords)

    algorithms = [
        ("CogPIE", lambda p, b: [c for c, _ in cogpie.generate(profile=p, policy=None, max_candidates=b)]),
        ("Markov-3", markov.generate),
        ("Frequency", freq.generate),
        ("Levenshtein", lev.generate),
        ("CUPP-style", cupp.generate),
        ("Random", rand_bl.generate),
    ]

    all_results = []
    for name, gen_fn in algorithms:
        logger.info("Evaluating %s on %d targets...", name, len(pairs))
        result = evaluate_algorithm(name, gen_fn, pairs, budgets)
        all_results.append(result)
        logger.info(
            "  %s: coverage=%.1f%%, MRR=%.4f, hit@1k=%.1f%%, hit@100k=%.1f%%",
            name, result["coverage_pct"], result["mrr"],
            result["hit_rates"].get("hit@1000", 0),
            result["hit_rates"].get("hit@100000", 0),
        )

    summary = {
        "pairs_file": pairs_path,
        "train_corpus": train_corpus_path,
        "num_targets": len(pairs),
        "train_size": len(train_passwords),
        "budget_tiers": budgets,
        "algorithms": all_results,
    }

    results_path = out / "scale_benchmark_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    table_path = out / "scale_benchmark_table.md"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write("# CogPIE Scale Benchmark Results\n\n")
        f.write(f"Targets: {len(pairs):,} | Train: {len(train_passwords):,}\n\n")

        headers = ["Algorithm", "Coverage", "MRR"] + [f"hit@{k}" for k in budgets] + ["ms/target"]
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"] * len(headers)) + "|\n")

        for r in all_results:
            row = [
                r["algorithm"],
                f"{r['coverage_pct']:.1f}%",
                f"{r['mrr']:.4f}",
            ]
            for k in budgets:
                row.append(f"{r['hit_rates'][f'hit@{k}']:.2f}%")
            row.append(f"{r['avg_time_per_target_ms']:.1f}")
            f.write("| " + " | ".join(row) + " |\n")

    logger.info("Results: %s", results_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CogPIE Scale Benchmark: evaluate with real PII:password pairs"
    )
    parser.add_argument("--pairs", "-p", required=True, help="JSONL pairs file")
    parser.add_argument("--train-corpus", "-t", required=True, help="Training corpus")
    parser.add_argument("--output", "-o", default="./benchmark/scale", help="Output dir")
    parser.add_argument("--max-targets", type=int, default=1000)
    parser.add_argument("--max-train", type=int, default=0)
    parser.add_argument("--budgets", nargs="+", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    summary = run_scale_benchmark(
        pairs_path=args.pairs,
        train_corpus_path=args.train_corpus,
        output_dir=args.output,
        max_targets=args.max_targets,
        max_train=args.max_train,
        budgets=args.budgets,
        seed=args.seed,
    )

    print("\n=== Scale Benchmark Results ===")
    print(f"Targets: {summary['num_targets']:,} | Train: {summary['train_size']:,}\n")
    for r in summary["algorithms"]:
        rates = " | ".join(f"{k}: {v:.1f}%" for k, v in r["hit_rates"].items())
        print(f"  {r['algorithm']:15s} | Cov: {r['coverage_pct']:.1f}% | MRR: {r['mrr']:.4f} | {rates}")


if __name__ == "__main__":
    main()

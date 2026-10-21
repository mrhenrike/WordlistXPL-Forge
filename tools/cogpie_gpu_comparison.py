#!/usr/bin/env python3
"""
cogpie_gpu_comparison.py - GPU-accelerated comparison of all algorithms.

Uses CUDA tensors for fast candidate-to-corpus matching when evaluating
CogPIE and baselines at scale. The GPU acceleration targets the matching
phase (checking if generated candidates exist in the corpus), which
becomes the bottleneck with large corpora.

Usage:
  python tools/cogpie_gpu_comparison.py \
    --corpus ./corpus/rockyou_full/processed_corpus.txt \
    --output ./benchmark/gpu_comparison \
    --max-test 500 --max-train 500000 \
    --budgets 10 100 1000 10000 -v

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wlf_modules.cogpie.engine import CogPIEEngine
from wlf_modules.cogpie.markov_pcfg_hybrid import HybridRanker
from wlf_modules.cogpie.pii_correlator import correlate_password, _detect_name, _detect_date

logger = logging.getLogger("cogpie.gpu_comparison")

BUDGET_TIERS = [10, 100, 1_000, 10_000]


def _extract_profile(password: str) -> dict | None:
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


def load_and_split(corpus_path, max_lines=0, max_test=500, seed=42):
    passwords = []
    with open(corpus_path, "r", encoding="utf-8", errors="ignore") as fh:
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

    test_size = min(max_test, max(int(len(pii_passwords) * 0.1), 50))
    test_set = pii_passwords[:test_size]
    train_set = pii_passwords[test_size:] + non_pii

    logger.info("Split: %d train, %d test (PII-bearing)", len(train_set), len(test_set))
    return train_set, test_set


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
                c = self._gen(base, length)
                if c:
                    candidates.add(c)
                if len(candidates) >= budget:
                    break
            if len(candidates) >= budget:
                break
        scored = [(c, self.ranker.score(c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:budget]]

    def _gen(self, seed, length):
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
    SUFFIXES = ["", "1", "12", "123", "1234", "!", "@", "#", "01", "11", "13",
                "23", "69", "007", "2024", "2025", "2026"]
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
                if len(candidates) >= budget:
                    break
            if len(candidates) >= budget:
                break

        for i, t1 in enumerate(tokens[:3]):
            for t2 in tokens[i + 1:4]:
                for sep in ("", "_", "."):
                    candidates.add(t1 + sep + t2)
                    candidates.add(t2 + sep + t1)

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
        sample = self.vocab[:min(len(self.vocab), budget * 5)]
        scored = [(pw, self._lev(primary, pw.lower())) for pw in sample]
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


def try_import_torch():
    try:
        import torch
        if torch.cuda.is_available():
            device = torch.device("cuda")
            name = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory
            logger.info("GPU: %s (%.1f GB)", name, mem / 1e9)
            return torch, device
        else:
            logger.warning("CUDA not available, using CPU")
            return torch, torch.device("cpu")
    except ImportError:
        return None, None


def evaluate_with_gpu(name, gen_fn, test_set, budgets, corpus_set, torch_mod=None, device=None):
    max_budget = max(budgets)
    hits_at = {k: 0 for k in budgets}
    ranks = []
    total_time = 0.0
    evaluated = 0

    for idx, target_pw in enumerate(test_set):
        profile = _extract_profile(target_pw)
        if profile is None:
            continue

        t0 = time.monotonic()
        try:
            candidates = gen_fn(profile, max_budget)
        except Exception:
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

        if (idx + 1) % 100 == 0:
            logger.info(
                "  [%s] %d/%d (hit@%d: %.1f%%)",
                name, idx + 1, len(test_set), max_budget,
                hits_at[max_budget] / max(evaluated, 1) * 100,
            )

    hit_rates = {}
    for k in budgets:
        hit_rates[f"hit@{k}"] = round(hits_at[k] / max(evaluated, 1) * 100, 2)

    mrr = sum(1.0 / r for r in ranks) / max(evaluated, 1) if ranks else 0.0

    return {
        "algorithm": name,
        "evaluated": evaluated,
        "total_hits": len(ranks),
        "coverage_pct": round(len(ranks) / max(evaluated, 1) * 100, 2),
        "mrr": round(mrr, 6),
        "median_rank": int(statistics.median(ranks)) if ranks else None,
        "total_time_seconds": round(total_time, 2),
        "avg_time_per_target_ms": round(total_time / max(evaluated, 1) * 1000, 2),
        "hit_rates": hit_rates,
        "hits_raw": {f"hit@{k}": hits_at[k] for k in budgets},
    }


def run_gpu_comparison(
    corpus_path: str,
    output_dir: str,
    max_lines: int = 0,
    max_test: int = 500,
    max_train: int = 500000,
    budgets: list[int] | None = None,
    seed: int = 42,
) -> dict:
    if budgets is None:
        budgets = list(BUDGET_TIERS)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    torch_mod, device = try_import_torch()

    train_set, test_set = load_and_split(
        corpus_path, max_lines=max_lines, max_test=max_test, seed=seed,
    )

    if max_train and len(train_set) > max_train:
        train_set = train_set[:max_train]

    corpus_set = set(train_set)

    train_path = out / "_train_split.txt"
    with open(train_path, "w", encoding="utf-8") as f:
        for pw in train_set:
            f.write(pw + "\n")

    logger.info("Training CogPIE on %d passwords...", len(train_set))
    cogpie = CogPIEEngine(alpha=0.4, beta=0.2, markov_order=3)
    cogpie.train(str(train_path), max_lines=0)

    logger.info("Training Markov baseline...")
    markov = MarkovBaseline(order=3)
    markov.train(train_set[:min(len(train_set), 500000)])

    logger.info("Training Frequency baseline...")
    freq = FrequencyBaseline()
    freq.train(train_set)

    logger.info("Training Levenshtein baseline...")
    lev = LevenshteinBaseline()
    lev.train(train_set[:min(len(train_set), 200000)])

    cupp = CUPPBaseline()
    rand_bl = RandomBaseline()
    rand_bl.train(train_set)

    algorithms = [
        ("CogPIE", lambda p, b: [c for c, _ in cogpie.generate(profile=p, policy=None, max_candidates=b)]),
        ("Markov-3", markov.generate),
        ("Frequency", freq.generate),
        ("Levenshtein", lev.generate),
        ("CUPP-style", cupp.generate),
        ("Random", rand_bl.generate),
    ]

    all_results = []
    for alg_name, gen_fn in algorithms:
        logger.info("Evaluating %s on %d targets...", alg_name, len(test_set))
        result = evaluate_with_gpu(alg_name, gen_fn, test_set, budgets, corpus_set, torch_mod, device)
        all_results.append(result)
        logger.info(
            "  %s: coverage=%.1f%%, MRR=%.4f, hit@%d=%.1f%%",
            alg_name, result["coverage_pct"], result["mrr"],
            max(budgets), result["hit_rates"][f"hit@{max(budgets)}"],
        )

    summary = {
        "corpus": corpus_path,
        "train_size": len(train_set),
        "test_size": len(test_set),
        "budget_tiers": budgets,
        "gpu": str(device) if device else "cpu",
        "algorithms": all_results,
    }

    results_path = out / "gpu_comparison_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    table_path = out / "gpu_comparison_table.md"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write("# CogPIE GPU Comparison Benchmark\n\n")
        f.write(f"Corpus: {corpus_path}\n")
        f.write(f"Train: {len(train_set):,} | Test: {len(test_set):,} | GPU: {device}\n\n")

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
    logger.info("Table: %s", table_path)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CogPIE GPU Comparison: all algorithms with CUDA acceleration"
    )
    parser.add_argument("--corpus", "-c", required=True, help="Corpus file")
    parser.add_argument("--output", "-o", default="./benchmark/gpu_comparison", help="Output dir")
    parser.add_argument("--max-lines", type=int, default=0)
    parser.add_argument("--max-test", type=int, default=500)
    parser.add_argument("--max-train", type=int, default=500000)
    parser.add_argument("--budgets", nargs="+", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    summary = run_gpu_comparison(
        corpus_path=args.corpus,
        output_dir=args.output,
        max_lines=args.max_lines,
        max_test=args.max_test,
        max_train=args.max_train,
        budgets=args.budgets,
        seed=args.seed,
    )

    print(f"\n=== GPU Comparison Results ({summary['gpu']}) ===")
    print(f"Train: {summary['train_size']:,} | Test: {summary['test_size']:,}\n")
    for r in summary["algorithms"]:
        rates = " | ".join(f"{k}: {v:.1f}%" for k, v in r["hit_rates"].items())
        print(f"  {r['algorithm']:15s} | Cov: {r['coverage_pct']:.1f}% | MRR: {r['mrr']:.4f} | {rates}")


if __name__ == "__main__":
    main()

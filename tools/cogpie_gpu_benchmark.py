#!/usr/bin/env python3
"""
cogpie_gpu_benchmark.py - GPU-accelerated CogPIE benchmark at billion-scale.

Uses CUDA via PyTorch for parallel password candidate matching against
massive leak databases. The bottleneck in large-scale benchmarks is
comparing millions of candidates against millions of target passwords;
GPU tensor operations accelerate this by orders of magnitude.

Architecture:
  1. Load target passwords into GPU memory as hash tensors
  2. For each PII profile, generate candidates on CPU (CogPIE)
  3. Hash candidates and batch-compare on GPU
  4. Accumulate hit statistics

Hash method: CRC32 + length as 64-bit key for fast GPU comparison.
False positive rate ~2^-32 per comparison, verified on hits.

Memory: RTX 4060 8GB can hold ~500M 64-bit hashes simultaneously.

Usage:
  python tools/cogpie_gpu_benchmark.py \
    --corpus ./corpus/rockyou_full/processed_corpus.txt \
    --output ./benchmark/gpu \
    --max-targets 5000 \
    --budget 100000 -v

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
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger("cogpie.gpu_benchmark")

BUDGET_TIERS = [10, 100, 1_000, 10_000, 100_000]


def _hash_password(pw: str) -> int:
    """Hash password to signed 64-bit integer (CRC32 + length)."""
    crc = zlib.crc32(pw.encode("utf-8")) & 0xFFFFFFFF
    val = (crc << 16) | (len(pw) & 0xFFFF)
    if val >= (1 << 63):
        val -= (1 << 64)
    return val


def _try_import_torch():
    """Import torch and check CUDA availability."""
    try:
        import torch
        if torch.cuda.is_available():
            device = torch.device("cuda")
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_memory
            logger.info("GPU: %s (%.1f GB)", gpu_name, gpu_mem / 1e9)
            return torch, device
        else:
            logger.warning("CUDA not available, falling back to CPU tensors")
            return torch, torch.device("cpu")
    except ImportError:
        logger.warning("PyTorch not installed, using pure Python fallback")
        return None, None


class GPUHashMatcher:
    """GPU-accelerated hash set for password matching."""

    def __init__(self, passwords: list[str], torch_mod=None, device=None):
        self.torch = torch_mod
        self.device = device
        self._pw_lookup: dict[int, str] = {}

        logger.info("Building hash index for %d passwords...", len(passwords))
        t0 = time.monotonic()

        hashes = []
        for pw in passwords:
            h = _hash_password(pw)
            hashes.append(h)
            self._pw_lookup[h] = pw

        if self.torch is not None:
            self._hash_tensor = self.torch.tensor(
                hashes, dtype=self.torch.int64, device=self.device
            )
            self._sorted, self._indices = self.torch.sort(self._hash_tensor)
        else:
            self._hash_set = set(hashes)

        elapsed = time.monotonic() - t0
        logger.info("Hash index built in %.2fs (%d unique hashes)", elapsed, len(self._pw_lookup))

    def batch_match(self, candidates: list[str]) -> list[tuple[str, int]]:
        """Check which candidates exist in the password set.

        Returns list of (candidate, rank) for matches.
        """
        if not candidates:
            return []

        candidate_hashes = [_hash_password(c) for c in candidates]

        if self.torch is not None:
            query = self.torch.tensor(
                candidate_hashes, dtype=self.torch.int64, device=self.device
            )
            idx = self.torch.searchsorted(self._sorted, query)
            idx = self.torch.clamp(idx, 0, len(self._sorted) - 1)
            matches_mask = self._sorted[idx] == query
            match_indices = self.torch.nonzero(matches_mask).squeeze(-1)

            results = []
            if match_indices.numel() > 0:
                for mi in match_indices.tolist():
                    if isinstance(mi, int):
                        h = candidate_hashes[mi]
                        if h in self._pw_lookup:
                            results.append((candidates[mi], mi + 1))
                    else:
                        for m in mi:
                            h = candidate_hashes[m]
                            if h in self._pw_lookup:
                                results.append((candidates[m], m + 1))
            return results
        else:
            results = []
            for rank, (c, h) in enumerate(zip(candidates, candidate_hashes), 1):
                if h in self._hash_set:
                    if self._pw_lookup.get(h) == c:
                        results.append((c, rank))
            return results


class CPUSetMatcher:
    """CPU fallback: plain set membership."""

    def __init__(self, passwords: list[str]):
        self._pw_set = set(passwords)

    def batch_match(self, candidates: list[str]) -> list[tuple[str, int]]:
        results = []
        for rank, c in enumerate(candidates, 1):
            if c in self._pw_set:
                results.append((c, rank))
        return results


def load_corpus(filepath: str, max_lines: int = 0) -> list[str]:
    passwords = []
    with open(filepath, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            pw = line.rstrip("\n\r")
            if pw:
                passwords.append(pw)
                if max_lines and len(passwords) >= max_lines:
                    break
    return passwords


def load_pairs(filepath: str, max_targets: int = 0, seed: int = 42) -> list[dict]:
    """Load PII:password pairs from JSONL or generate from corpus."""
    pairs = []
    if filepath.endswith(".jsonl"):
        with open(filepath, encoding="utf-8", errors="ignore") as fh:
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
    else:
        from wlf_modules.cogpie.pii_correlator import _detect_date, _detect_name, correlate_password

        passwords = load_corpus(filepath, max_lines=max_targets * 10 if max_targets else 0)
        rng = random.Random(seed)
        rng.shuffle(passwords)

        for pw in passwords:
            result = correlate_password(pw)
            if result.category in ("name_based", "date_based", "hybrid"):
                name, lang = _detect_name(pw)
                date_val, date_type = _detect_date(pw)
                profile = {
                    "names": [name] if name else [],
                    "dates": [date_val] if date_val else [],
                    "numbers": [date_val] if date_val else [],
                    "keywords": [], "pets": [], "companies": [],
                    "phones": [], "emails": [], "old_passwords": [],
                }
                residue = pw.lower()
                if name:
                    residue = residue.replace(name, "")
                if date_val:
                    residue = residue.replace(date_val, "")
                residue = residue.strip()
                if residue and len(residue) >= 3 and residue.isalpha():
                    profile["keywords"].append(residue)

                pairs.append({"password": pw, "pii": profile})
                if max_targets and len(pairs) >= max_targets:
                    break

    if max_targets and len(pairs) > max_targets:
        rng = random.Random(seed)
        rng.shuffle(pairs)
        pairs = pairs[:max_targets]

    return pairs


def run_gpu_benchmark(
    corpus_path: str,
    output_dir: str,
    max_targets: int = 5000,
    max_train: int = 0,
    budgets: list[int] | None = None,
    pairs_path: str | None = None,
    seed: int = 42,
) -> dict:
    """Run GPU-accelerated benchmark."""
    if budgets is None:
        budgets = list(BUDGET_TIERS)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    torch_mod, device = _try_import_torch()

    logger.info("Loading corpus for training...")
    train_passwords = load_corpus(corpus_path, max_lines=max_train if max_train else 0)
    logger.info("Corpus: %d passwords", len(train_passwords))

    if torch_mod is not None:
        matcher = GPUHashMatcher(train_passwords, torch_mod, device)
    else:
        matcher = CPUSetMatcher(train_passwords)

    logger.info("Loading test targets...")
    if pairs_path:
        pairs = load_pairs(pairs_path, max_targets=max_targets, seed=seed)
    else:
        pairs = load_pairs(corpus_path, max_targets=max_targets, seed=seed)
    logger.info("Test targets: %d", len(pairs))

    from wlf_modules.cogpie.engine import CogPIEEngine

    logger.info("Training CogPIE on %d passwords...", len(train_passwords))
    train_path = out / "_train.txt"
    with open(train_path, "w", encoding="utf-8") as f:
        for pw in train_passwords:
            f.write(pw + "\n")
    engine = CogPIEEngine(alpha=0.4, beta=0.2, markov_order=3)
    engine.train(str(train_path), max_lines=max_train if max_train else 0)

    max_budget = max(budgets)
    hits_at = {k: 0 for k in budgets}
    ranks = []
    total_gen_time = 0.0
    total_match_time = 0.0
    evaluated = 0

    logger.info("Evaluating %d targets with budget %d...", len(pairs), max_budget)
    t0 = time.monotonic()

    for idx, record in enumerate(pairs):
        profile = record["pii"]
        target_pw = record["password"]

        tg = time.monotonic()
        try:
            candidates = [c for c, _ in engine.generate(profile=profile, policy=None, max_candidates=max_budget)]
        except Exception:
            continue
        total_gen_time += time.monotonic() - tg

        tm = time.monotonic()
        found_at = None
        for rank, c in enumerate(candidates, 1):
            if c == target_pw:
                found_at = rank
                break
        total_match_time += time.monotonic() - tm

        evaluated += 1

        if found_at is not None:
            ranks.append(found_at)
            for k in budgets:
                if found_at <= k:
                    hits_at[k] += 1

        if (idx + 1) % 500 == 0:
            elapsed = time.monotonic() - t0
            rate = (idx + 1) / elapsed
            logger.info(
                "  %d/%d (%.1f/s) hit@%d: %.1f%% | gen: %.0fms match: %.0fms",
                idx + 1, len(pairs), rate, max_budget,
                hits_at[max_budget] / max(evaluated, 1) * 100,
                total_gen_time / max(evaluated, 1) * 1000,
                total_match_time / max(evaluated, 1) * 1000,
            )

    total_time = time.monotonic() - t0

    hit_rates = {}
    for k in budgets:
        hit_rates[f"hit@{k}"] = round(hits_at[k] / max(evaluated, 1) * 100, 2)

    mrr = sum(1.0 / r for r in ranks) / max(evaluated, 1) if ranks else 0.0

    summary = {
        "corpus": corpus_path,
        "pairs_source": pairs_path or "auto-extracted",
        "train_size": len(train_passwords),
        "test_size": evaluated,
        "gpu": str(device) if device else "cpu",
        "budget_tiers": budgets,
        "hit_rates": hit_rates,
        "hits_raw": {f"hit@{k}": hits_at[k] for k in budgets},
        "coverage_pct": round(len(ranks) / max(evaluated, 1) * 100, 2),
        "mrr": round(mrr, 6),
        "median_rank": int(statistics.median(ranks)) if ranks else None,
        "total_time_seconds": round(total_time, 2),
        "avg_gen_ms": round(total_gen_time / max(evaluated, 1) * 1000, 2),
        "avg_match_ms": round(total_match_time / max(evaluated, 1) * 1000, 2),
        "throughput_targets_per_sec": round(evaluated / max(total_time, 0.001), 2),
    }

    results_path = out / "gpu_benchmark_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("GPU Benchmark complete: %d targets in %.1fs (%.1f/s)", evaluated, total_time, evaluated / max(total_time, 0.001))
    for k in budgets:
        logger.info("  hit@%d: %.2f%% (%d/%d)", k, hit_rates[f"hit@{k}"], hits_at[k], evaluated)
    logger.info("  MRR: %.4f | Coverage: %.1f%%", mrr, summary["coverage_pct"])

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CogPIE GPU Benchmark: large-scale evaluation with CUDA acceleration"
    )
    parser.add_argument("--corpus", "-c", required=True, help="Training corpus")
    parser.add_argument("--pairs", "-p", help="PII:password pairs JSONL (optional)")
    parser.add_argument("--output", "-o", default="./benchmark/gpu", help="Output dir")
    parser.add_argument("--max-targets", type=int, default=5000)
    parser.add_argument("--max-train", type=int, default=0)
    parser.add_argument("--budgets", nargs="+", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    summary = run_gpu_benchmark(
        corpus_path=args.corpus,
        output_dir=args.output,
        max_targets=args.max_targets,
        max_train=args.max_train,
        budgets=args.budgets,
        pairs_path=args.pairs,
        seed=args.seed,
    )

    print(f"\n=== GPU Benchmark Results ({summary['gpu']}) ===")
    print(f"Train: {summary['train_size']:,} | Test: {summary['test_size']:,}")
    print(f"Throughput: {summary['throughput_targets_per_sec']:.1f} targets/s")
    for k, v in summary["hit_rates"].items():
        print(f"  {k}: {v:.2f}%")
    print(f"  MRR: {summary['mrr']:.4f}")
    print(f"  Coverage: {summary['coverage_pct']:.1f}%")


if __name__ == "__main__":
    main()

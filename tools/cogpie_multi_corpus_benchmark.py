#!/usr/bin/env python3
"""
cogpie_multi_corpus_benchmark.py - Multi-corpus CogPIE evaluation at scale.

Builds processed corpora from multiple sources and evaluates CogPIE at
various training scales (1M, 10M, 100M, 1B+). Supports streaming training
for corpora too large to fit in memory as a dedup set.

Sources:
  - /usr/share/crackstation/crackstation.txt (1.2B)
  - /usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt (14.3M)
  - /usr/share/wordlistxpl-forge/passwords/wlist_brasil.lst (8.8M)
  - /usr/share/wordlistxpl-forge/passwords/melissa_andrade.lst (4.3M)
  - /usr/share/seclists/Passwords/Common-Credentials/Pwdb_top-10000000.txt (10M)
  - /usr/share/seclists/Passwords/openwall.net-all.txt (3.7M)
  - SecLists Leaked-Databases (md5decryptor, gmail, 000webhost, etc.)

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import random
import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger("cogpie.multi_corpus")

SOURCES = {
    "crackstation": "/usr/share/crackstation/crackstation.txt",
    "rockyou": "/usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt",
    "wlist_brasil": "/usr/share/wordlistxpl-forge/passwords/wlist_brasil.lst",
    "melissa_andrade": "/usr/share/wordlistxpl-forge/passwords/melissa_andrade.lst",
    "pwdb_10m": "/usr/share/seclists/Passwords/Common-Credentials/Pwdb_top-10000000.txt",
    "xato_10m": "/usr/share/seclists/Passwords/Common-Credentials/xato-net-10-million-passwords.txt",
    "openwall": "/usr/share/seclists/Passwords/openwall.net-all.txt",
    "darkc0de": "/usr/share/seclists/Passwords/darkc0de.txt",
    "md5decryptor": "/usr/share/seclists/Passwords/Leaked-Databases/md5decryptor-uk.txt",
    "gmail": "/usr/share/seclists/Passwords/Leaked-Databases/alleged-gmail-passwords.txt",
    "000webhost": "/usr/share/seclists/Passwords/Leaked-Databases/000webhost.txt",
    "bt4": "/usr/share/seclists/Passwords/Software/bt4-password.txt",
    "wikipedia_pt": "/usr/share/seclists/Passwords/Wikipedia/wikipedia_pt_vowels_no_compounds_top-1000000.txt",
}

CORPUS_PRESETS = {
    "brazilian": ["wlist_brasil", "melissa_andrade"],
    "medium": ["rockyou", "wlist_brasil", "melissa_andrade", "pwdb_10m", "openwall"],
    "large": [
        "rockyou", "wlist_brasil", "melissa_andrade", "pwdb_10m",
        "xato_10m", "openwall", "darkc0de", "md5decryptor", "gmail",
        "000webhost", "bt4",
    ],
    "billion": ["crackstation"],
}

PII_PATTERN = re.compile(
    r"(?:^|(?<=[^a-zA-Z]))"
    r"([a-zA-Z]{3,15})"
    r"(?:"
    r"[._@#!]?"
    r"(\d{2,8})"
    r")"
    r"[!@#$%^&*]*$"
)

BR_NAMES = set()
_BR_NAMES_PATH = "/usr/share/wordlistxpl-forge/br/nomes.txt"
if os.path.isfile(_BR_NAMES_PATH):
    with open(_BR_NAMES_PATH, encoding="utf-8", errors="ignore") as _f:
        for _line in _f:
            n = _line.strip().lower()
            if len(n) >= 3:
                BR_NAMES.add(n)


def _is_pii_bearing(password: str) -> bool:
    if len(password) < 6 or len(password) > 40:
        return False
    m = PII_PATTERN.match(password)
    if not m:
        return False
    name_part = m.group(1).lower()
    if len(name_part) < 3:
        return False
    if name_part in BR_NAMES:
        return True
    if name_part.isalpha() and not name_part.isdigit():
        return True
    return False


def _extract_profile(password: str) -> dict | None:
    m = PII_PATTERN.match(password)
    if not m:
        return None
    name = m.group(1).lower()
    date_part = m.group(2) if m.group(2) else ""
    profile = {
        "names": [name],
        "dates": [date_part] if date_part else [],
        "keywords": [],
        "pets": [],
        "companies": [],
        "phones": [],
        "emails": [],
        "old_passwords": [],
        "numbers": [date_part] if date_part else [],
    }
    if len(name) >= 4:
        profile["keywords"].append(name[:4])
    return profile


def stream_train(engine, sources: list[str], max_lines: int = 0) -> int:
    """Train engine by streaming through source files without full dedup."""
    count = 0
    t0 = time.monotonic()
    for src_name in sources:
        path = SOURCES.get(src_name, src_name)
        if not os.path.isfile(path):
            logger.warning("Source not found: %s (%s)", src_name, path)
            continue
        logger.info("Training from %s: %s", src_name, path)
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                pw = line.rstrip("\n\r")
                if not pw or len(pw) < 4 or len(pw) > 64:
                    continue
                if any(ord(c) < 32 for c in pw):
                    continue
                engine.ranker.train(pw)
                count += 1
                if count % 5_000_000 == 0:
                    elapsed = time.monotonic() - t0
                    rate = count / max(elapsed, 0.001)
                    logger.info(
                        "  Training: %dM passwords (%.0f pw/s, %.1f min)",
                        count // 1_000_000, rate, elapsed / 60,
                    )
                if max_lines and count >= max_lines:
                    break
        if max_lines and count >= max_lines:
            break
    elapsed = time.monotonic() - t0
    logger.info(
        "Training complete: %d passwords in %.1f min (%.0f pw/s)",
        count, elapsed / 60, count / max(elapsed, 0.001),
    )
    return count


def extract_test_set(
    sources: list[str],
    n_targets: int = 2000,
    skip_lines: int = 0,
    seed: int = 42,
) -> list[str]:
    """Extract PII-bearing passwords as test targets from sources."""
    rng = random.Random(seed)
    reservoir: list[str] = []
    seen: set[str] = set()
    total_scanned = 0

    for src_name in sources:
        path = SOURCES.get(src_name, src_name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                total_scanned += 1
                if total_scanned <= skip_lines:
                    continue
                pw = line.rstrip("\n\r")
                if not pw or pw in seen:
                    continue
                if not _is_pii_bearing(pw):
                    continue
                seen.add(pw)
                if len(reservoir) < n_targets:
                    reservoir.append(pw)
                else:
                    j = rng.randint(0, total_scanned - skip_lines - 1)
                    if j < n_targets:
                        reservoir[j] = pw

                if total_scanned % 5_000_000 == 0:
                    logger.info(
                        "  Test extraction: scanned %dM, found %d PII targets",
                        total_scanned // 1_000_000, len(reservoir),
                    )
    logger.info(
        "Test set: %d PII-bearing targets from %dM scanned lines",
        len(reservoir), total_scanned // 1_000_000,
    )
    return reservoir


def evaluate_cogpie(
    engine,
    test_set: list[str],
    budgets: list[int] | None = None,
    max_candidates: int = 10000,
    progress_every: int = 100,
) -> dict:
    """Evaluate CogPIE against test set with hit@k metrics."""
    if budgets is None:
        budgets = [10, 100, 1000, 10000]
    max_budget = max(budgets)

    hits_at = {k: 0 for k in budgets}
    ranks: list[int] = []
    total_time = 0.0
    evaluated = 0
    skipped = 0

    for idx, target_pw in enumerate(test_set):
        profile = _extract_profile(target_pw)
        if profile is None:
            skipped += 1
            continue

        t0 = time.monotonic()
        try:
            results = engine.generate(profile, max_candidates=max_candidates)
        except Exception as e:
            logger.warning("Generation failed for target %d: %s", idx, e)
            skipped += 1
            continue
        gen_time = time.monotonic() - t0
        total_time += gen_time
        evaluated += 1

        candidates = [c for c, _ in results]
        found_rank = None
        for rank, c in enumerate(candidates[:max_budget], 1):
            if c == target_pw:
                found_rank = rank
                break

        if found_rank is not None:
            ranks.append(found_rank)
            for k in budgets:
                if found_rank <= k:
                    hits_at[k] += 1

        if progress_every and (idx + 1) % progress_every == 0:
            cov = len(ranks) / max(evaluated, 1) * 100
            avg_ms = total_time / max(evaluated, 1) * 1000
            logger.info(
                "  [CogPIE] %d/%d evaluated, coverage=%.1f%%, avg=%.0fms/target",
                evaluated, len(test_set), cov, avg_ms,
            )

    hit_rates = {}
    for k in budgets:
        hit_rates[f"hit@{k}"] = round(hits_at[k] / max(evaluated, 1) * 100, 2)

    mrr = sum(1.0 / r for r in ranks) / max(evaluated, 1) if ranks else 0.0

    return {
        "evaluated": evaluated,
        "skipped": skipped,
        "total_hits": len(ranks),
        "coverage_pct": round(len(ranks) / max(evaluated, 1) * 100, 2),
        "mrr": round(mrr, 6),
        "median_rank": int(statistics.median(ranks)) if ranks else None,
        "avg_ms_per_target": round(total_time / max(evaluated, 1) * 1000, 2),
        "total_time_seconds": round(total_time, 2),
        "hit_rates": hit_rates,
        "hits_raw": {f"hit@{k}": hits_at[k] for k in budgets},
    }


def run_benchmark(
    preset: str,
    train_limit: int = 0,
    n_targets: int = 2000,
    use_gpu: bool = True,
    output_dir: str = "benchmark/multi_corpus",
) -> dict:
    """Run a complete benchmark with a given preset and training limit."""
    from wlf_modules.cogpie.engine import CogPIEEngine

    sources = CORPUS_PRESETS.get(preset, [preset])
    available = [s for s in sources if os.path.isfile(SOURCES.get(s, s))]

    if not available:
        logger.error("No sources available for preset: %s", preset)
        return {}

    label = f"{preset}_{train_limit // 1_000_000}M" if train_limit else f"{preset}_full"
    logger.info("=== Benchmark: %s ===", label)
    logger.info("Sources: %s", available)
    logger.info("Train limit: %s", f"{train_limit:,}" if train_limit else "unlimited")

    test_sources = available
    if preset == "billion":
        test_sources = ["rockyou", "wlist_brasil"]
    test_set = extract_test_set(test_sources, n_targets=n_targets, skip_lines=100_000)

    if len(test_set) < 50:
        logger.error("Too few test targets (%d). Aborting.", len(test_set))
        return {}

    engine = CogPIEEngine(use_gpu=use_gpu)
    t0 = time.monotonic()
    trained = stream_train(engine, available, max_lines=train_limit)
    train_time = time.monotonic() - t0

    logger.info("Trained on %d passwords in %.1f min", trained, train_time / 60)

    results = evaluate_cogpie(engine, test_set, progress_every=200)

    output = {
        "label": label,
        "preset": preset,
        "sources": available,
        "train_limit": train_limit,
        "trained_count": trained,
        "train_time_seconds": round(train_time, 2),
        "test_targets": len(test_set),
        "device": "cuda" if use_gpu else "cpu",
        "results": results,
    }

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    result_file = out_path / f"{label}_results.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info("Results saved: %s", result_file)
    logger.info(
        "Coverage: %.2f%%, MRR: %.6f, Median rank: %s",
        results["coverage_pct"],
        results["mrr"],
        results["median_rank"],
    )
    for k, v in results["hit_rates"].items():
        logger.info("  %s: %.2f%%", k, v)

    del engine
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass

    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CogPIE Multi-Corpus Benchmark"
    )
    parser.add_argument(
        "--preset", "-p",
        choices=list(CORPUS_PRESETS.keys()) + ["all"],
        default="brazilian",
        help="Corpus preset to use",
    )
    parser.add_argument(
        "--train-limit", "-t",
        type=int,
        default=0,
        help="Max training passwords (0 = unlimited)",
    )
    parser.add_argument(
        "--targets", "-n",
        type=int,
        default=2000,
        help="Number of test targets",
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Force CPU mode",
    )
    parser.add_argument(
        "--output", "-o",
        default="benchmark/multi_corpus",
        help="Output directory",
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

    if args.preset == "all":
        presets_and_limits = [
            ("brazilian", 0),
            ("medium", 10_000_000),
            ("medium", 0),
            ("large", 10_000_000),
            ("large", 100_000_000),
            ("large", 0),
        ]
        for preset, limit in presets_and_limits:
            run_benchmark(
                preset=preset,
                train_limit=limit,
                n_targets=args.targets,
                use_gpu=not args.cpu,
                output_dir=args.output,
            )
    else:
        run_benchmark(
            preset=args.preset,
            train_limit=args.train_limit,
            n_targets=args.targets,
            use_gpu=not args.cpu,
            output_dir=args.output,
        )


if __name__ == "__main__":
    main()

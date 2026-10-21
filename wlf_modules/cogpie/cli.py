"""
cli.py - CogPIE command-line interface.

Usage:
    python -m wlf_modules.cogpie.cli --profile target.json [--corpus rockyou.txt]
        [--policy-min 8] [--policy-classes 3] [--max 100000] [-o output.txt]

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from wlf_modules.cogpie.engine import CogPIEEngine
from wlf_modules.cogpie.policy_filter import PasswordPolicy


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="cogpie",
        description="CogPIE: Cognitive Pattern Inference Engine for targeted password generation.",
    )
    p.add_argument(
        "--profile", "-p",
        required=True,
        help="Path to target profile JSON file.",
    )
    p.add_argument(
        "--corpus", "-c",
        default=None,
        help="Path to training corpus (password list). Improves ranking quality.",
    )
    p.add_argument(
        "--corpus-limit",
        type=int,
        default=500_000,
        help="Max lines to read from corpus (default: 500000).",
    )
    p.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path. Default: stdout.",
    )
    p.add_argument(
        "--max",
        type=int,
        default=100_000,
        help="Maximum candidates to generate (default: 100000).",
    )
    p.add_argument(
        "--policy-min",
        type=int,
        default=6,
        help="Minimum password length (default: 6).",
    )
    p.add_argument(
        "--policy-max",
        type=int,
        default=64,
        help="Maximum password length (default: 64).",
    )
    p.add_argument(
        "--policy-classes",
        type=int,
        default=1,
        help="Minimum character classes required (default: 1).",
    )
    p.add_argument(
        "--alpha",
        type=float,
        default=0.4,
        help="Markov weight in hybrid scoring (default: 0.4).",
    )
    p.add_argument(
        "--beta",
        type=float,
        default=0.2,
        help="Frequency prior weight (default: 0.2).",
    )
    p.add_argument(
        "--json-meta",
        action="store_true",
        help="Output JSON lines with metadata instead of plain passwords.",
    )
    p.add_argument(
        "--stats",
        action="store_true",
        help="Print pipeline statistics to stderr.",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    profile_path = Path(args.profile)
    if not profile_path.is_file():
        print(f"Error: profile not found: {profile_path}", file=sys.stderr)
        return 1

    with profile_path.open("r", encoding="utf-8") as fh:
        profile = json.load(fh)

    engine = CogPIEEngine(alpha=args.alpha, beta=args.beta)

    if args.corpus:
        corpus_path = Path(args.corpus)
        if corpus_path.is_file():
            count = engine.train(str(corpus_path), max_lines=args.corpus_limit)
            print(f"Trained on {count} passwords", file=sys.stderr)
        else:
            print(f"Warning: corpus not found: {corpus_path}", file=sys.stderr)

    policy = PasswordPolicy(
        min_length=args.policy_min,
        max_length=args.policy_max,
        min_char_classes=args.policy_classes,
    )

    results = engine.generate(profile, policy=policy, max_candidates=args.max)

    out = sys.stdout
    if args.output:
        out = open(args.output, "w", encoding="utf-8")

    try:
        for candidate, meta in results:
            if args.json_meta:
                out.write(json.dumps(meta, ensure_ascii=False) + "\n")
            else:
                out.write(candidate + "\n")
    finally:
        if out is not sys.stdout:
            out.close()

    if args.stats:
        stats = engine.stats
        print("\n--- CogPIE Pipeline Statistics ---", file=sys.stderr)
        for k, v in stats.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.4f}", file=sys.stderr)
            else:
                print(f"  {k}: {v}", file=sys.stderr)

    total = len(results)
    print(f"Generated {total} candidates", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

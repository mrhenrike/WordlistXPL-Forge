#!/usr/bin/env python3
"""
cogpie_corpus_builder.py - Build processed corpora for CogPIE Layer 3 training.

Reads raw password leak files (e.g. SecLists rockyou.txt, darkc0de.txt,
NCSC top-100k), extracts statistics, identifies PII-password patterns,
and generates processed corpus files ready for HybridRanker training.

Output artefacts:
  - corpus_stats.json: aggregate PII correlation statistics
  - processed_corpus.txt: cleaned, deduplicated passwords for training
  - pii_patterns.json: extracted PII-password correlation pairs

Usage:
  python tools/cogpie_corpus_builder.py --input /path/to/rockyou.txt --output ./corpus/
  python tools/cogpie_corpus_builder.py --seclists --output ./corpus/
  python tools/cogpie_corpus_builder.py --seclists --max-lines 1000000 --output ./corpus/

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wlf_modules.cogpie.pii_correlator import correlate_corpus, correlate_password

logger = logging.getLogger("cogpie.corpus_builder")

SECLISTS_BASE = "/usr/share/seclists/Passwords"
DEFAULT_SOURCES = [
    ("rockyou", f"{SECLISTS_BASE}/Leaked-Databases/rockyou.txt"),
    ("darkc0de", f"{SECLISTS_BASE}/darkc0de.txt"),
    ("ncsc_100k", f"{SECLISTS_BASE}/100k-most-used-passwords-NCSC.txt"),
]


def _resolve_sources(
    input_files: list[str] | None,
    use_seclists: bool,
) -> list[tuple[str, str]]:
    """Return list of (label, path) for available sources."""
    sources: list[tuple[str, str]] = []
    if use_seclists:
        for label, path in DEFAULT_SOURCES:
            if os.path.isfile(path):
                sources.append((label, path))
            else:
                logger.warning("SecLists source not found: %s", path)
    if input_files:
        for fp in input_files:
            if os.path.isfile(fp):
                label = Path(fp).stem
                sources.append((label, fp))
            else:
                logger.warning("Input file not found: %s", fp)
    return sources


def build_processed_corpus(
    sources: list[tuple[str, str]],
    output_dir: str,
    max_lines: int = 0,
    min_length: int = 4,
    max_length: int = 64,
) -> dict:
    """Process sources into a deduplicated training corpus.

    Returns summary statistics dict.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    total_raw = 0
    total_kept = 0
    total_skipped_len = 0
    total_skipped_dup = 0
    total_skipped_binary = 0
    source_counts: dict[str, dict[str, int]] = {}

    corpus_path = out / "processed_corpus.txt"
    pii_pairs: list[dict] = []
    pii_sample_limit = 50_000

    t0 = time.monotonic()

    with open(corpus_path, "w", encoding="utf-8") as out_fh:
        for label, path in sources:
            src_raw = 0
            src_kept = 0
            logger.info("Processing %s: %s", label, path)

            with open(path, encoding="utf-8", errors="ignore") as in_fh:
                for line in in_fh:
                    pw = line.rstrip("\n\r")
                    total_raw += 1
                    src_raw += 1

                    if max_lines and total_raw > max_lines:
                        break

                    if not pw or len(pw) < min_length or len(pw) > max_length:
                        total_skipped_len += 1
                        continue

                    try:
                        pw.encode("ascii")
                    except UnicodeEncodeError:
                        pass

                    if any(ord(c) < 32 for c in pw):
                        total_skipped_binary += 1
                        continue

                    if pw in seen:
                        total_skipped_dup += 1
                        continue

                    seen.add(pw)
                    out_fh.write(pw + "\n")
                    total_kept += 1
                    src_kept += 1

                    if len(pii_pairs) < pii_sample_limit:
                        result = correlate_password(pw)
                        if result.category in ("name_based", "date_based", "hybrid"):
                            pii_pairs.append({
                                "password": pw,
                                "category": result.category,
                                "name": result.name_found,
                                "name_lang": result.name_lang,
                                "date": result.date_found,
                                "date_type": result.date_type,
                                "confidence": result.confidence,
                            })

                    if total_raw % 1_000_000 == 0:
                        logger.info(
                            "  ... %dM lines read, %dk kept",
                            total_raw // 1_000_000,
                            total_kept // 1_000,
                        )

            source_counts[label] = {"raw": src_raw, "kept": src_kept}
            logger.info("  %s: %d raw -> %d kept", label, src_raw, src_kept)

    elapsed = time.monotonic() - t0

    pii_path = out / "pii_patterns.json"
    with open(pii_path, "w", encoding="utf-8") as f:
        json.dump(pii_pairs, f, indent=2, ensure_ascii=False)

    logger.info("Running PII correlation on processed corpus...")
    t1 = time.monotonic()
    stats = correlate_corpus(filepath=str(corpus_path), max_lines=0)
    pii_elapsed = time.monotonic() - t1
    stats_dict = stats.as_dict()

    summary = {
        "build_time_seconds": round(elapsed, 2),
        "pii_analysis_time_seconds": round(pii_elapsed, 2),
        "sources": source_counts,
        "total_raw_lines": total_raw,
        "total_kept": total_kept,
        "skipped_length": total_skipped_len,
        "skipped_duplicate": total_skipped_dup,
        "skipped_binary": total_skipped_binary,
        "pii_patterns_sampled": len(pii_pairs),
        "corpus_stats": stats_dict,
    }

    stats_path = out / "corpus_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(
        "Corpus built: %d passwords from %d raw lines (%.1fs)",
        total_kept, total_raw, elapsed,
    )
    logger.info("PII detectable: %.1f%%", stats_dict.get("pii_detectable_pct", 0))
    logger.info("Output: %s", out)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CogPIE Corpus Builder: process raw password leaks for training"
    )
    parser.add_argument(
        "--input", "-i",
        nargs="*",
        help="Input password file(s)",
    )
    parser.add_argument(
        "--seclists",
        action="store_true",
        help="Use default SecLists password files",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output directory",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=0,
        help="Max total lines to read (0 = unlimited)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=4,
        help="Min password length to keep",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=64,
        help="Max password length to keep",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    sources = _resolve_sources(args.input, args.seclists)
    if not sources:
        logger.error("No valid input sources found. Use --input or --seclists.")
        sys.exit(1)

    logger.info("Sources: %s", [s[0] for s in sources])
    summary = build_processed_corpus(
        sources=sources,
        output_dir=args.output,
        max_lines=args.max_lines,
        min_length=args.min_length,
        max_length=args.max_length,
    )

    print(f"\nCorpus built: {summary['total_kept']:,} passwords")
    print(f"PII detectable: {summary['corpus_stats'].get('pii_detectable_pct', 0):.1f}%")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()

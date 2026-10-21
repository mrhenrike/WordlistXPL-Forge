#!/usr/bin/env python3
"""
cogpie_leak_extractor.py - Extract PII-password pairs from breach data.

Processes email:password (or user:password) leak files to extract
structured PII profiles paired with their actual passwords. This
creates the ground truth dataset for CogPIE evaluation at scale.

PII extraction from email addresses:
  - Names: john.smith@... -> ["john", "smith"]
  - Year patterns: john1985@... -> dates=["1985"]
  - Username tokens: j_smith_dev@... -> ["smith", "dev"]
  - Domain context: @company.com -> companies=["company"]

Supports formats:
  - email:password (most common)
  - email;password
  - email\tpassword
  - user:password (no @)

Output: JSONL file with {email, password, pii_profile} per line,
plus summary statistics.

Usage:
  python tools/cogpie_leak_extractor.py --input dump.txt --output ./extracted/ -v
  python tools/cogpie_leak_extractor.py --input-dir ./leaks/ --output ./extracted/ --max-lines 100000000 -v

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

logger = logging.getLogger("cogpie.leak_extractor")

GENERIC_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "mail.com", "protonmail.com", "icloud.com", "live.com", "msn.com",
    "yandex.com", "zoho.com", "gmx.com", "fastmail.com", "tutanota.com",
    "qq.com", "163.com", "126.com", "sina.com", "mail.ru",
    "uol.com.br", "bol.com.br", "terra.com.br", "ig.com.br",
    "globo.com", "zipmail.com.br", "yahoo.com.br", "hotmail.com.br",
}

YEAR_PATTERN = re.compile(r"(?:19[5-9]\d|20[0-2]\d)")
DATE_PATTERNS = [
    re.compile(r"(\d{2})[/\-.](\d{2})[/\-.](\d{4})"),
    re.compile(r"(\d{4})[/\-.](\d{2})[/\-.](\d{2})"),
    re.compile(r"(\d{2})(\d{2})(\d{4})"),
]

NAME_MIN_LEN = 2
NAME_MAX_LEN = 20


def _split_email_local(local: str) -> list[str]:
    """Split email local part into tokens."""
    local = local.lower()
    parts = re.split(r"[._\-+]", local)
    tokens = []
    for part in parts:
        if not part:
            continue
        sub = re.findall(r"[a-z]+|[0-9]+", part)
        tokens.extend(sub)
    return tokens


def _is_name_like(token: str) -> bool:
    """Check if a token looks like a name (alpha, reasonable length)."""
    return (
        token.isalpha()
        and NAME_MIN_LEN <= len(token) <= NAME_MAX_LEN
        and not token.isdigit()
    )


def extract_pii_from_email(email: str) -> dict:
    """Extract PII profile from an email address."""
    profile: dict = {
        "names": [],
        "dates": [],
        "numbers": [],
        "keywords": [],
        "companies": [],
        "pets": [],
        "phones": [],
        "emails": [email],
        "old_passwords": [],
    }

    if "@" in email:
        local, domain = email.rsplit("@", 1)
        domain_lower = domain.lower()

        if domain_lower not in GENERIC_DOMAINS:
            company = domain_lower.split(".")[0]
            if len(company) >= 3 and company.isalpha():
                profile["companies"].append(company)
    else:
        local = email
        domain = ""

    tokens = _split_email_local(local)

    for token in tokens:
        if _is_name_like(token):
            profile["names"].append(token)
        elif token.isdigit():
            profile["numbers"].append(token)
            years = YEAR_PATTERN.findall(token)
            for y in years:
                if y not in profile["dates"]:
                    profile["dates"].append(y)
        else:
            if len(token) >= 3:
                profile["keywords"].append(token)

    for token in tokens:
        if not token.isdigit():
            continue
        if len(token) == 4:
            years = YEAR_PATTERN.findall(token)
            if years:
                for y in years:
                    if y not in profile["dates"]:
                        profile["dates"].append(y)
        elif len(token) in (6, 8):
            for pat in DATE_PATTERNS:
                m = pat.match(token)
                if m:
                    profile["dates"].append(token)
                    break

    return profile


def _parse_line(line: str) -> tuple[str, str] | None:
    """Parse a line into (email/user, password) pair."""
    line = line.rstrip("\n\r")
    if not line:
        return None

    for sep in (":", ";", "\t"):
        idx = line.find(sep)
        if idx > 0:
            left = line[:idx].strip()
            right = line[idx + 1:].strip()
            if left and right and len(right) >= 4 and len(right) <= 128:
                return (left, right)
            break

    return None


def process_file(
    filepath: str,
    output_fh,
    max_lines: int = 0,
    min_pii_tokens: int = 1,
    stats: dict | None = None,
) -> int:
    """Process a single leak file, writing JSONL to output_fh.

    Returns number of valid PII pairs extracted.
    """
    if stats is None:
        stats = {}

    extracted = 0
    total_lines = 0
    parse_errors = 0
    no_pii = 0

    with open(filepath, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            total_lines += 1
            if max_lines and total_lines > max_lines:
                break

            parsed = _parse_line(line)
            if parsed is None:
                parse_errors += 1
                continue

            email, password = parsed
            pii = extract_pii_from_email(email)

            pii_count = len(pii["names"]) + len(pii["dates"]) + len(pii["numbers"])
            if pii_count < min_pii_tokens:
                no_pii += 1
                continue

            record = {
                "email": email,
                "password": password,
                "pii": pii,
            }
            output_fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            extracted += 1

            if total_lines % 5_000_000 == 0:
                logger.info(
                    "  ... %dM lines, %dk pairs extracted",
                    total_lines // 1_000_000,
                    extracted // 1_000,
                )

    stats["total_lines"] = stats.get("total_lines", 0) + total_lines
    stats["extracted"] = stats.get("extracted", 0) + extracted
    stats["parse_errors"] = stats.get("parse_errors", 0) + parse_errors
    stats["no_pii"] = stats.get("no_pii", 0) + no_pii

    return extracted


def process_all(
    input_files: list[str],
    output_dir: str,
    max_lines: int = 0,
    min_pii_tokens: int = 1,
) -> dict:
    """Process all input files and generate extracted dataset."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pairs_path = out / "pii_password_pairs.jsonl"
    stats: dict = {"files": {}}

    t0 = time.monotonic()

    with open(pairs_path, "w", encoding="utf-8") as out_fh:
        remaining = max_lines
        for filepath in input_files:
            logger.info("Processing: %s", filepath)
            file_stats: dict = {}
            file_max = remaining if remaining else 0

            count = process_file(
                filepath, out_fh,
                max_lines=file_max,
                min_pii_tokens=min_pii_tokens,
                stats=file_stats,
            )
            stats["files"][filepath] = file_stats
            logger.info("  -> %d pairs extracted", count)

            if remaining:
                remaining -= file_stats.get("total_lines", 0)
                if remaining <= 0:
                    break

    elapsed = time.monotonic() - t0

    total_extracted = sum(fs.get("extracted", 0) for fs in stats["files"].values())
    total_lines = sum(fs.get("total_lines", 0) for fs in stats["files"].values())

    summary = {
        "total_files": len(input_files),
        "total_lines_processed": total_lines,
        "total_pairs_extracted": total_extracted,
        "extraction_rate_pct": round(total_extracted / max(total_lines, 1) * 100, 2),
        "elapsed_seconds": round(elapsed, 2),
        "throughput_lines_per_sec": round(total_lines / max(elapsed, 0.001)),
        "output_file": str(pairs_path),
        "files": {
            k: v for k, v in stats["files"].items()
        },
    }

    stats_path = out / "extraction_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(
        "Extraction complete: %d pairs from %d lines (%.1f%%) in %.1fs",
        total_extracted, total_lines,
        total_extracted / max(total_lines, 1) * 100,
        elapsed,
    )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CogPIE Leak Extractor: extract PII-password pairs from breach data"
    )
    parser.add_argument("--input", "-i", nargs="*", help="Input leak file(s)")
    parser.add_argument("--input-dir", help="Directory with leak files (*.txt)")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--max-lines", type=int, default=0, help="Max total lines (0=all)")
    parser.add_argument("--min-pii", type=int, default=1, help="Min PII tokens per pair")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    files = []
    if args.input:
        files.extend(args.input)
    if args.input_dir:
        for f in sorted(Path(args.input_dir).glob("*.txt")):
            files.append(str(f))

    if not files:
        logger.error("No input files. Use --input or --input-dir.")
        sys.exit(1)

    logger.info("Processing %d file(s)", len(files))
    summary = process_all(
        input_files=files,
        output_dir=args.output,
        max_lines=args.max_lines,
        min_pii_tokens=args.min_pii,
    )

    print(f"\nExtracted: {summary['total_pairs_extracted']:,} PII:password pairs")
    print(f"From: {summary['total_lines_processed']:,} lines ({summary['extraction_rate_pct']}%)")
    print(f"Time: {summary['elapsed_seconds']:.1f}s")
    print(f"Output: {summary['output_file']}")


if __name__ == "__main__":
    main()

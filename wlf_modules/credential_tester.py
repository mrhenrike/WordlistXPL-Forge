"""Credential testing pipeline — generate wordlist + hashcat cracking."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CrackResult:
    total_hashes: int = 0
    cracked: int = 0
    rate: float = 0.0
    top_passwords: list[dict[str, str]] = field(default_factory=list)
    hash_mode: int = 0
    duration_seconds: float = 0.0
    wordlist_size: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_hashes == 0:
            return 0.0
        return (self.cracked / self.total_hashes) * 100

    def to_finding(self) -> dict[str, Any]:
        return {
            "schema": "xpl.finding.v1",
            "id": f"wlf-credtest-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "title": f"Credential Testing: {self.cracked}/{self.total_hashes} cracked ({self.success_rate:.1f}%)",
            "severity": _severity_from_rate(self.success_rate),
            "target": "hash-file",
            "evidence": {
                "total_hashes": self.total_hashes,
                "cracked": self.cracked,
                "success_rate": self.success_rate,
                "hash_mode": self.hash_mode,
                "wordlist_size": self.wordlist_size,
                "duration_seconds": self.duration_seconds,
                "top_10": self.top_passwords[:10],
            },
            "remediation": (
                "Enforce password policy: min 12 chars, complexity, no dictionary words. "
                "Consider passphrase-based policy."
            ),
            "provenance": {
                "tool": "WordlistXPL-Forge/credential_tester",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }


def _severity_from_rate(rate: float) -> str:
    if rate >= 50:
        return "CRITICAL"
    if rate >= 25:
        return "HIGH"
    if rate >= 10:
        return "MEDIUM"
    if rate > 0:
        return "LOW"
    return "INFO"


HASH_MODES = {
    "md5": 0,
    "sha1": 100,
    "sha256": 1400,
    "sha512": 1700,
    "ntlm": 1000,
    "bcrypt": 3200,
    "sha512crypt": 1800,
    "md5crypt": 500,
    "descrypt": 1500,
    "netlm": 5500,
    "netntlmv2": 5600,
    "kerberos_tgs": 13100,
    "kerberos_asrep": 18200,
    "wpa": 22000,
}


def detect_hash_mode(hash_file: str) -> int:
    with open(hash_file) as fh:
        first_line = fh.readline().strip()

    if first_line.startswith("$2"):
        return 3200
    if first_line.startswith("$6$"):
        return 1800
    if first_line.startswith("$1$"):
        return 500
    if first_line.startswith("$krb5tgs$"):
        return 13100
    if first_line.startswith("$krb5asrep$"):
        return 18200
    if "::" in first_line and first_line.count(":") >= 4:
        return 5600

    hash_part = first_line.split(":")[-1] if ":" in first_line else first_line
    length = len(hash_part)

    if length == 32 and all(c in "0123456789abcdef" for c in hash_part.lower()):
        return 1000 if ":" in first_line else 0
    if length == 40:
        return 100
    if length == 64:
        return 1400
    if length == 128:
        return 1700

    return 0


def generate_wordlist(
    model: str = "M2",
    target_info: dict[str, Any] | None = None,
    output_path: str | None = None,
    max_words: int = 100000,
) -> str:
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".txt", prefix="wlf_credtest_")

    words: list[str] = []

    from wlf_modules.default_creds import get_default_passwords
    words.extend(get_default_passwords())

    if target_info and target_info.get("vendor"):
        from wlf_modules.default_creds import get_vendor_passwords
        vendor_passwords = get_vendor_passwords(target_info["vendor"])
        words.extend(vendor_passwords)

    try:
        from wlf_modules.markov_engine import MarkovEngine
        engine = MarkovEngine()
        markov_words = engine.generate(count=min(max_words // 2, 50000))
        words.extend(markov_words)
    except (ImportError, Exception):
        pass

    try:
        from wlf_modules.rule_engine import RuleEngine
        re_engine = RuleEngine()
        base_words = words[:1000]
        mutated = re_engine.apply_rules(base_words)
        words.extend(mutated[:max_words // 4])
    except (ImportError, Exception):
        pass

    seen: set[str] = set()
    unique = []
    for w in words:
        if w not in seen and len(w) >= 1:
            seen.add(w)
            unique.append(w)
            if len(unique) >= max_words:
                break

    with open(output_path, "w") as fh:
        fh.write("\n".join(unique))

    return output_path


def run_hashcat(
    hash_file: str,
    wordlist: str,
    hash_mode: int | None = None,
    timeout: int = 300,
) -> CrackResult:
    hashcat_bin = shutil.which("hashcat")
    if not hashcat_bin:
        raise FileNotFoundError("hashcat not found in PATH")

    if hash_mode is None:
        hash_mode = detect_hash_mode(hash_file)

    with open(hash_file) as fh:
        total_hashes = sum(1 for line in fh if line.strip())

    with open(wordlist) as fh:
        wordlist_size = sum(1 for line in fh if line.strip())

    potfile = tempfile.mktemp(suffix=".pot", prefix="wlf_")

    import time
    start = time.monotonic()

    try:
        subprocess.run(
            [
                hashcat_bin,
                "-m", str(hash_mode),
                "-a", "0",
                "--potfile-path", potfile,
                "--force",
                "--quiet",
                hash_file,
                wordlist,
            ],
            timeout=timeout,
            capture_output=True,
        )
    except subprocess.TimeoutExpired:
        pass

    duration = time.monotonic() - start

    result = CrackResult(
        total_hashes=total_hashes,
        hash_mode=hash_mode,
        duration_seconds=round(duration, 2),
        wordlist_size=wordlist_size,
    )

    if os.path.exists(potfile):
        with open(potfile) as fh:
            for line in fh:
                line = line.strip()
                if ":" in line:
                    parts = line.rsplit(":", 1)
                    result.top_passwords.append({
                        "hash": parts[0][:16] + "...",
                        "password": parts[1],
                    })
                    result.cracked += 1
        os.unlink(potfile)

    result.rate = result.success_rate
    return result


def run_test(
    hash_file: str,
    model: str = "M2",
    hash_mode: int | None = None,
    output_dir: str = ".",
    timeout: int = 300,
    max_words: int = 100000,
) -> dict[str, Any]:
    print(f"[*] WordlistXPL Credential Testing Pipeline")
    print(f"    Hash file: {hash_file}")
    print(f"    Model: {model}")

    print("[*] Generating wordlist...")
    wordlist = generate_wordlist(model=model, max_words=max_words)
    print(f"[+] Wordlist: {wordlist}")

    print("[*] Running hashcat...")
    try:
        result = run_hashcat(hash_file, wordlist, hash_mode=hash_mode, timeout=timeout)
    finally:
        if os.path.exists(wordlist) and wordlist.startswith(tempfile.gettempdir()):
            os.unlink(wordlist)

    finding = result.to_finding()

    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"credtest_{ts}.json")
    with open(out_path, "w") as fh:
        json.dump(finding, fh, indent=2)

    print(f"\n[+] Results:")
    print(f"    Cracked: {result.cracked}/{result.total_hashes} ({result.success_rate:.1f}%)")
    print(f"    Duration: {result.duration_seconds}s")
    if result.top_passwords:
        print(f"    Top passwords:")
        for entry in result.top_passwords[:10]:
            print(f"      {entry['password']}")
    print(f"[+] Report: {out_path}")

    return finding

"""hibp_checker.py - Have I Been Pwned breach checking.

Checks passwords against the HIBP Pwned Passwords API using the
k-Anonymity model (only the first 5 characters of the SHA-1 hash
are sent).  Includes rate limiting, offline hash-file support, and
statistical summaries.

API: https://api.pwnedpasswords.com/range/{prefix}
No API key required. Rate limit: ~1 request per 1.5 seconds.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_HIBP_API = "https://api.pwnedpasswords.com/range/"
_REQUEST_DELAY = 1.5
_TIMEOUT = 10
_DEFAULT_KEY_FILE = ".hibp-key"


def _load_api_key(key_file: str | None = None) -> str | None:
    """Load HIBP API key from file or default location.

    Searches in order:
      1. Explicit path via --api-key-file
      2. .hibp-key in current directory
      3. ~/.hibp-key in home directory
    File format: plain text, first non-empty line = key.
    """
    candidates: list[str] = []
    if key_file:
        candidates.append(key_file)
    candidates.append(_DEFAULT_KEY_FILE)
    candidates.append(str(Path.home() / _DEFAULT_KEY_FILE))

    for path in candidates:
        p = Path(path)
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    logger.info("Loaded HIBP API key from %s", path)
                    return line
    return None


# ── SHA-1 helpers ─────────────────────────────────────────────────────────────

def _sha1_hash(password: str) -> str:
    """Return uppercase SHA-1 hex digest."""
    return hashlib.sha1(password.encode("utf-8")).hexdigest().upper()


def _split_hash(sha1: str) -> tuple[str, str]:
    """Split SHA-1 into 5-char prefix and suffix."""
    return sha1[:5], sha1[5:]


# ── Online check (HIBP API) ──────────────────────────────────────────────────

def _fetch_range(prefix: str, api_key: str | None = None) -> dict[str, int]:
    """Fetch HIBP range for a hash prefix. Returns {suffix: count}."""
    import urllib.error
    import urllib.request

    url = f"{_HIBP_API}{prefix}"
    headers: dict[str, str] = {
        "User-Agent": "WordlistXPL-Forge/2.0 (breach-checker)",
        "Add-Padding": "true",
    }
    if api_key:
        headers["hibp-api-key"] = api_key
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        logger.warning("HIBP request failed for prefix %s: %s", prefix, e)
        return {}

    results: dict[str, int] = {}
    for line in body.splitlines():
        line = line.strip()
        if ":" in line:
            suffix, count_str = line.split(":", 1)
            try:
                results[suffix.strip()] = int(count_str.strip())
            except ValueError:
                pass
    return results


def check_password_online(password: str) -> int:
    """Check one password against HIBP. Returns breach count (0 = not found)."""
    sha1 = _sha1_hash(password)
    prefix, suffix = _split_hash(sha1)
    results = _fetch_range(prefix)
    return results.get(suffix, 0)


# ── Offline check (local hash file) ──────────────────────────────────────────

class _OfflineHashDB:
    """Simple offline HIBP hash lookup using sorted file or set."""

    def __init__(self, hash_file: str) -> None:
        self.hashes: set[str] = set()
        logger.info("Loading offline hash database: %s", hash_file)
        for line in Path(hash_file).read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines():
            line = line.strip().upper()
            if ":" in line:
                h = line.split(":")[0]
                self.hashes.add(h)
            elif len(line) == 40:
                self.hashes.add(line)
        logger.info("Loaded %d hashes from offline DB", len(self.hashes))

    def check(self, password: str) -> int:
        """Check password against offline DB. Returns 1 if found, 0 if not."""
        sha1 = _sha1_hash(password)
        return 1 if sha1 in self.hashes else 0


# ── Batch checker ─────────────────────────────────────────────────────────────

class HIBPCheckResult:
    """Result of checking a batch of passwords."""

    def __init__(self) -> None:
        self.results: list[tuple[str, int]] = []
        self.total = 0
        self.breached = 0
        self.clean = 0

    def add(self, password: str, count: int) -> None:
        self.results.append((password, count))
        self.total += 1
        if count > 0:
            self.breached += 1
        else:
            self.clean += 1

    @property
    def breach_percentage(self) -> float:
        return (self.breached / self.total * 100.0) if self.total > 0 else 0.0

    def top_breached(self, n: int = 10) -> list[tuple[str, int]]:
        return sorted(
            [(pw, c) for pw, c in self.results if c > 0],
            key=lambda x: x[1],
            reverse=True,
        )[:n]

    def format_text(self) -> str:
        sep = "─" * 60
        lines = [
            sep,
            "  HIBP Breach Check Report",
            sep,
            f"  Total checked:   {self.total:>10,}",
            f"  Breached:        {self.breached:>10,}  ({self.breach_percentage:.1f}%)",
            f"  Clean:           {self.clean:>10,}",
            sep,
        ]
        top = self.top_breached(10)
        if top:
            lines.append("  Top breached passwords:")
            for pw, count in top:
                lines.append(f"    {count:>10,}x  {pw}")
            lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "breached": self.breached,
            "clean": self.clean,
            "breach_percentage": round(self.breach_percentage, 2),
            "top_breached": [
                {"password": pw, "count": c}
                for pw, c in self.top_breached(10)
            ],
        }


class HIBPChecker:
    """Batch HIBP checker with rate limiting and offline support."""

    def __init__(
        self,
        offline_file: str | None = None,
        api_key_file: str | None = None,
        delay: float = _REQUEST_DELAY,
    ) -> None:
        self.delay = delay
        self._offline: _OfflineHashDB | None = None
        if offline_file:
            self._offline = _OfflineHashDB(offline_file)
        self._api_key = _load_api_key(api_key_file)
        if not self._offline and not self._api_key:
            logger.warning(
                "No HIBP API key found. The range endpoint works without "
                "a key but is rate-limited. For higher limits, save your "
                "key to .hibp-key or pass --api-key-file."
            )
        self._last_request = 0.0
        self._cache: dict[str, dict[str, int]] = {}

    def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        if self._offline:
            return
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.time()

    def check_one(self, password: str) -> int:
        """Check a single password. Returns breach count."""
        if self._offline:
            return self._offline.check(password)

        sha1 = _sha1_hash(password)
        prefix, suffix = _split_hash(sha1)

        if prefix not in self._cache:
            self._rate_limit()
            self._cache[prefix] = _fetch_range(prefix, api_key=self._api_key)

        return self._cache[prefix].get(suffix, 0)

    def check_batch(
        self,
        passwords: list[str],
        min_count: int = 0,
    ) -> HIBPCheckResult:
        """Check a batch of passwords."""
        result = HIBPCheckResult()
        for i, pw in enumerate(passwords):
            count = self.check_one(pw)
            if count >= min_count:
                result.add(pw, count)
            if (i + 1) % 100 == 0:
                logger.info(
                    "Checked %d/%d (breached so far: %d)",
                    i + 1, len(passwords), result.breached,
                )
        return result

    def iter_breached(
        self,
        passwords: list[str],
        min_count: int = 1,
    ) -> Generator[tuple[str, int], None, None]:
        """Yield (password, count) for breached passwords."""
        for pw in passwords:
            count = self.check_one(pw)
            if count >= min_count:
                yield pw, count

    def iter_clean(
        self,
        passwords: list[str],
    ) -> Generator[str, None, None]:
        """Yield passwords NOT found in breaches."""
        for pw in passwords:
            count = self.check_one(pw)
            if count == 0:
                yield pw


# ── CLI handler ───────────────────────────────────────────────────────────────

def _load_passwords(path: str, max_load: int = 100_000) -> list[str]:
    """Load passwords from file."""
    passwords: list[str] = []
    for line in Path(path).read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        pw = line.strip()
        if pw:
            passwords.append(pw)
            if len(passwords) >= max_load:
                break
    return passwords


def handle_hibp(
    args: Any, ctx: dict[str, Any]
) -> Generator[str, None, None] | None:
    """CLI handler for HIBP breach checking."""
    wordlist = getattr(args, "wordlist", None)
    fmt = getattr(args, "format", "text")
    min_count = getattr(args, "min_count", 0) or 0
    offline = getattr(args, "offline", None)
    output_breached = getattr(args, "output_breached", None)
    output_clean = getattr(args, "output_clean", None)

    api_key_file = getattr(args, "api_key_file", None)

    if not wordlist:
        logger.warning("No wordlist provided. Use positional arg.")
        return None

    passwords = _load_passwords(wordlist)
    if not passwords:
        logger.warning("Wordlist is empty.")
        return None

    checker = HIBPChecker(offline_file=offline, api_key_file=api_key_file)

    if output_breached:
        count = 0
        with open(output_breached, "w", encoding="utf-8") as fh:
            for pw, c in checker.iter_breached(passwords, min_count=max(1, min_count)):
                fh.write(f"{pw}:{c}\n")
                count += 1
        logger.info("Wrote %d breached entries to %s", count, output_breached)

    if output_clean:
        count = 0
        with open(output_clean, "w", encoding="utf-8") as fh:
            for pw in checker.iter_clean(passwords):
                fh.write(pw + "\n")
                count += 1
        logger.info("Wrote %d clean entries to %s", count, output_clean)

    result = checker.check_batch(passwords, min_count=min_count)

    if fmt == "json":
        def _gen_json() -> Generator[str, None, None]:
            yield json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        return _gen_json()

    if fmt == "csv":
        def _gen_csv() -> Generator[str, None, None]:
            yield "password,breach_count"
            for pw, c in result.results:
                yield f"{pw},{c}"
        return _gen_csv()

    def _gen_text() -> Generator[str, None, None]:
        yield result.format_text()
    return _gen_text()

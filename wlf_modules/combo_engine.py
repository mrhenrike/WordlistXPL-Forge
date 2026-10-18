"""combo_engine.py - Credential combo (user:pass) generation engine.

Generates user:password combinations for credential testing from
username and password lists using multiple pairing strategies.

Strategies:
  - cartesian: every user × every password
  - user_as_pass: username used as its own password (+ variants)
  - email_prefix: email local-part as username, with password variants
  - smart: frequency-weighted pairing (common passwords first)
  - reverse: password as username, common passwords

Output formats: colon-separated, tab-separated, JSON.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)

STRATEGIES = ("cartesian", "user_as_pass", "email_prefix", "smart", "reverse")
OUTPUT_FORMATS = ("colon", "tab", "json")


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load_lines(path: str, max_lines: int = 500_000) -> list[str]:
    """Load non-empty lines from a file."""
    lines: list[str] = []
    for raw in Path(path).read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        line = raw.strip()
        if line:
            lines.append(line)
            if len(lines) >= max_lines:
                break
    return lines


def _user_as_pass_variants(user: str) -> list[str]:
    """Generate password variants derived from the username itself."""
    variants: list[str] = [user]
    if user != user.lower():
        variants.append(user.lower())
    if user != user.capitalize():
        variants.append(user.capitalize())
    variants.append(user + "123")
    variants.append(user + "!")
    variants.append(user + "1")
    variants.append(user.capitalize() + "123")
    variants.append(user + "@123")
    return list(dict.fromkeys(variants))


def _email_to_username(email: str) -> str:
    """Extract username from email address."""
    if "@" in email:
        return email.split("@")[0]
    return email


def _format_combo(user: str, password: str, fmt: str) -> str:
    """Format a single combo in the specified output format."""
    if fmt == "json":
        return json.dumps({"user": user, "password": password}, ensure_ascii=False)
    if fmt == "tab":
        return f"{user}\t{password}"
    return f"{user}:{password}"


# ── Pairing strategies ──────────────────────────────────────────────────────

def _cartesian(
    users: list[str], passwords: list[str], limit: int
) -> Generator[tuple[str, str], None, None]:
    """Cartesian product: every user × every password."""
    count = 0
    for user in users:
        for pw in passwords:
            yield user, pw
            count += 1
            if 0 < limit <= count:
                return


def _user_as_pass(
    users: list[str], _passwords: list[str], limit: int
) -> Generator[tuple[str, str], None, None]:
    """Each username paired with itself and its variants as password."""
    count = 0
    for user in users:
        for variant in _user_as_pass_variants(user):
            yield user, variant
            count += 1
            if 0 < limit <= count:
                return


def _email_prefix(
    users: list[str], passwords: list[str], limit: int
) -> Generator[tuple[str, str], None, None]:
    """Email local-part as username, paired with passwords + self-variants."""
    count = 0
    for email in users:
        uname = _email_to_username(email)
        for variant in _user_as_pass_variants(uname):
            yield uname, variant
            count += 1
            if 0 < limit <= count:
                return
        for pw in passwords[:50]:
            yield uname, pw
            count += 1
            if 0 < limit <= count:
                return


def _smart(
    users: list[str], passwords: list[str], limit: int
) -> Generator[tuple[str, str], None, None]:
    """Smart pairing: common passwords first, then user-specific variants."""
    count = 0
    top_passwords = passwords[:20] if passwords else []
    for user in users:
        for pw in top_passwords:
            yield user, pw
            count += 1
            if 0 < limit <= count:
                return
        for variant in _user_as_pass_variants(user)[:3]:
            yield user, variant
            count += 1
            if 0 < limit <= count:
                return


def _reverse_strategy(
    users: list[str], passwords: list[str], limit: int
) -> Generator[tuple[str, str], None, None]:
    """Reverse: each password treated as a potential username too."""
    count = 0
    common = passwords[:100] if passwords else []
    for pw in common:
        for pw2 in common[:10]:
            yield pw, pw2
            count += 1
            if 0 < limit <= count:
                return


_STRATEGY_MAP: dict[
    str,
    Any,
] = {
    "cartesian": _cartesian,
    "user_as_pass": _user_as_pass,
    "email_prefix": _email_prefix,
    "smart": _smart,
    "reverse": _reverse_strategy,
}


# ── Engine ──────────────────────────────────────────────────────────────────

class ComboEngine:
    """Credential combo generation engine."""

    def __init__(
        self,
        users: list[str],
        passwords: list[str],
        strategy: str = "smart",
        fmt: str = "colon",
        dedup: bool = True,
    ) -> None:
        if strategy not in _STRATEGY_MAP:
            raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {STRATEGIES}")
        if fmt not in OUTPUT_FORMATS:
            raise ValueError(f"Unknown format '{fmt}'. Choose from: {OUTPUT_FORMATS}")
        self.users = users
        self.passwords = passwords
        self.strategy = strategy
        self.fmt = fmt
        self.dedup = dedup

    def generate(self, limit: int = 0) -> Generator[str, None, None]:
        """Yield formatted credential combos."""
        fn = _STRATEGY_MAP[self.strategy]
        seen: set[str] = set()
        for user, password in fn(self.users, self.passwords, limit):
            combo = _format_combo(user, password, self.fmt)
            if self.dedup:
                if combo in seen:
                    continue
                seen.add(combo)
            yield combo


# ── CLI handler ─────────────────────────────────────────────────────────────

def handle_combo(
    args: Any, ctx: dict[str, Any]
) -> Optional[Generator[str, None, None]]:
    """CLI handler for credential combo generation."""
    userlist = getattr(args, "userlist", None)
    passlist = getattr(args, "passlist", None)
    strategy = getattr(args, "strategy", "smart")
    fmt = getattr(args, "format", "colon")
    limit = getattr(args, "limit", 0) or 0
    no_dedup = getattr(args, "no_dedup", False)

    if not userlist:
        logger.warning("No user list provided. Use --userlist.")
        return None

    users = _load_lines(userlist)
    passwords = _load_lines(passlist) if passlist else []

    if not users:
        logger.warning("User list is empty.")
        return None

    engine = ComboEngine(
        users=users,
        passwords=passwords,
        strategy=strategy,
        fmt=fmt,
        dedup=not no_dedup,
    )

    return engine.generate(limit=limit)

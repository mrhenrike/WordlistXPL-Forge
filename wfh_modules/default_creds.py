"""
default_creds.py - Default credentials database for IoT, network, and embedded devices.

Loads a consolidated JSON database of factory-default user:password pairs,
SNMP community strings, and SNMPv3 credentials. Supports filtering by vendor,
protocol, category, and output format.

Database lives outside this repo (suite EmbedXPL resources). Pass ``--db``
or set ``WLF_DEFAULT_CREDS_DB``.

Author: Andre Henrique (LinkedIn/X: @mrhenrike)
Version: 1.2.0
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)

_MODULE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _MODULE_DIR.parent
_DB: Optional[dict] = None
_DB_PATH: Optional[Path] = None


def _resolve_db_path(explicit: Optional[str | Path] = None) -> Path:
    """Resolve default-creds JSON: --db, env, then EmbedXPL suite path."""
    if explicit:
        return Path(explicit)
    env = os.environ.get("WLF_DEFAULT_CREDS_DB", "").strip()
    if env:
        return Path(env)
    candidates = [
        _REPO_ROOT.parent
        / "EmbedXPL-Forge"
        / "embedxpl"
        / "resources"
        / "creds"
        / "default-creds.json",
        _REPO_ROOT / "generated" / "default-creds.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _load_db(explicit: Optional[str | Path] = None) -> dict:
    """Load and cache the credentials database."""
    global _DB, _DB_PATH
    db_path = _resolve_db_path(explicit)
    if _DB is not None and _DB_PATH == db_path:
        return _DB
    if not db_path.exists():
        logger.error(
            "Default credentials database not found: %s\n"
            "  Pass --db PATH or set WLF_DEFAULT_CREDS_DB "
            "(suite: EmbedXPL-Forge/embedxpl/resources/creds/).",
            db_path,
        )
        _DB = {"credentials": [], "snmp_communities": [], "snmpv3_defaults": []}
        _DB_PATH = db_path
        return _DB
    with open(db_path, "r", encoding="utf-8") as f:
        _DB = json.load(f)
    _DB_PATH = db_path
    logger.info(
        "Loaded %d credentials, %d SNMP communities, %d SNMPv3 from %s",
        len(_DB.get("credentials", [])),
        len(_DB.get("snmp_communities", [])),
        len(_DB.get("snmpv3_defaults", [])),
        db_path,
    )
    return _DB


def list_vendors() -> list[str]:
    """Return sorted list of all vendors in the database."""
    db = _load_db()
    vendors = sorted({c["vendor"] for c in db.get("credentials", [])})
    return vendors


def list_protocols() -> list[str]:
    """Return sorted list of all protocols in the database."""
    db = _load_db()
    protocols = sorted({c["protocol"] for c in db.get("credentials", [])})
    return protocols


def list_categories() -> list[str]:
    """Return sorted list of all categories in the database."""
    db = _load_db()
    categories = sorted({c["category"] for c in db.get("credentials", [])})
    return categories


def generate_credentials(
    vendor: Optional[str] = None,
    protocol: Optional[str] = None,
    category: Optional[str] = None,
    fmt: str = "combo",
) -> Generator[str, None, None]:
    """Generate credential entries filtered by vendor/protocol/category.

    Args:
        vendor: Filter by vendor name (case-insensitive, partial match).
        protocol: Filter by protocol (api, ssh, telnet, http, etc.).
        category: Filter by category (router, printer, ics, etc.).
        fmt: Output format - 'combo' (user:pass), 'user', 'pass', 'json'.

    Yields:
        Formatted credential strings.
    """
    db = _load_db()
    seen = set()

    for entry in db.get("credentials", []):
        if vendor and vendor.lower() not in entry["vendor"].lower():
            continue
        if protocol and protocol.lower() != entry["protocol"].lower():
            continue
        if category and category.lower() not in entry["category"].lower():
            continue

        if fmt == "combo":
            line = f"{entry['user']}:{entry['pass']}"
        elif fmt == "user":
            line = entry["user"]
        elif fmt == "pass":
            line = entry["pass"]
        elif fmt == "json":
            line = json.dumps(entry, ensure_ascii=False)
        else:
            line = f"{entry['user']}:{entry['pass']}"

        if line not in seen:
            seen.add(line)
            yield line


def generate_snmp(version: str = "v2") -> Generator[str, None, None]:
    """Generate SNMP community strings or SNMPv3 credentials.

    Args:
        version: 'v2' for community strings, 'v3' for SNMPv3 defaults.

    Yields:
        SNMP community strings or pipe-delimited SNMPv3 entries.
    """
    db = _load_db()
    if version == "v3":
        for entry in db.get("snmpv3_defaults", []):
            yield (
                f"{entry['user']}|{entry['auth_proto']}|{entry['auth_pass']}"
                f"|{entry['priv_proto']}|{entry['priv_pass']}|{entry['level']}"
            )
    else:
        for community in db.get("snmp_communities", []):
            yield community


def handle_default_creds(args: object, _ctx: dict) -> None:
    """CLI handler for the default-creds subcommand."""
    import sys

    db_override = getattr(args, "db", None)
    # Prime cache from generated/ (or --db) before any query
    db = _load_db(db_override)
    db_path = _resolve_db_path(db_override)
    if not db_path.exists() and not any(
        (
            db.get("credentials"),
            db.get("snmp_communities"),
            db.get("snmpv3_defaults"),
        )
    ):
        print(
            f"[!] Local default-creds corpus missing: {db_path}\n"
            "    Not shipped in the public tree. Build with:\n"
            "      python3 update_wordlists.py\n"
            "    Or pass --db /path/to/default-creds.json",
            file=sys.stderr,
        )
        return

    if getattr(args, "list_vendors", False):
        vendors = list_vendors()
        print(f"[+] {len(vendors)} vendors in database:")
        for v in vendors:
            print(f"  {v}")
        return

    if getattr(args, "list_protocols", False):
        protocols = list_protocols()
        print(f"[+] {len(protocols)} protocols in database:")
        for p in protocols:
            print(f"  {p}")
        return

    if getattr(args, "snmp", False):
        version = getattr(args, "snmp_version", "v2")
        out = getattr(args, "output", None)
        fh = open(out, "w", encoding="utf-8", newline="\n") if out else sys.stdout
        count = 0
        try:
            for line in generate_snmp(version):
                fh.write(line + "\n")
                count += 1
        finally:
            if fh is not sys.stdout:
                fh.close()
        logger.info("Generated %d SNMP %s entries", count, version)
        if out:
            print(f"[+] {count} SNMP {version} entries written to {out}")
        return

    vendor = getattr(args, "vendor", None)
    protocol = getattr(args, "protocol", None)
    category = getattr(args, "category", None)
    fmt = getattr(args, "format", "combo")
    out = getattr(args, "output", None)

    fh = open(out, "w", encoding="utf-8", newline="\n") if out else sys.stdout
    count = 0
    try:
        for line in generate_credentials(vendor, protocol, category, fmt):
            fh.write(line + "\n")
            count += 1
    finally:
        if fh is not sys.stdout:
            fh.close()

    logger.info("Generated %d credential entries (vendor=%s, protocol=%s, fmt=%s)",
                count, vendor, protocol, fmt)
    if out:
        print(f"[+] {count} credentials written to {out}")

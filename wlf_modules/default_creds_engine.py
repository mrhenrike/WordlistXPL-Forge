"""
default_creds_engine.py - Default credential database and generator.

Maintains an embedded database of default credentials for network devices,
IoT, SCADA/ICS, web applications, databases, and cloud services. Generates
credential pairs for targeted testing based on vendor, product, protocol,
or category.

Inspired by Passhunt (Viralmaniar, 1,310 stars, 523 vendors), changeme,
and DefaultCreds-Cheat-Sheet, with structured categorization and export
to multiple formats.

Usage (as library):
    from wlf_modules.default_creds_engine import lookup, generate_pairs
    for cred in lookup(vendor="cisco"):
        print(f"{cred['user']}:{cred['password']}")

Usage (CLI):
    wlf.py default-creds --vendor cisco --protocol ssh
    wlf.py default-creds --category iot --format hydra

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__info__ = {
    "name": "default_creds_engine",
    "version": "1.0.0",
    "author": "Andre Henrique (@mrhenrike)",
    "description": "Default credential database for network/IoT/ICS/web devices",
    "category": "credentials",
    "tags": ["default", "credentials", "iot", "ics", "network"],
}

CATEGORIES = (
    "network", "iot", "ics", "web", "database", "cloud",
    "camera", "printer", "router", "firewall", "switch",
    "scada", "plc", "hmi", "nas", "voip", "wireless",
)

PROTOCOLS = (
    "ssh", "telnet", "http", "https", "ftp", "snmp",
    "rdp", "vnc", "smb", "modbus", "s7comm", "bacnet",
    "mqtt", "rtsp", "sip",
)


def _builtin_db() -> list[dict[str, str]]:
    """Embedded default credential database (representative subset).

    In production this loads from resources/default_creds.json; the
    embedded list provides the core dataset without external files.
    """
    return [
        {"vendor": "cisco", "product": "ios", "category": "router", "protocol": "telnet", "user": "admin", "password": "admin"},
        {"vendor": "cisco", "product": "ios", "category": "router", "protocol": "telnet", "user": "cisco", "password": "cisco"},
        {"vendor": "cisco", "product": "ios", "category": "router", "protocol": "ssh", "user": "admin", "password": ""},
        {"vendor": "cisco", "product": "asa", "category": "firewall", "protocol": "ssh", "user": "admin", "password": "admin"},
        {"vendor": "cisco", "product": "asa", "category": "firewall", "protocol": "https", "user": "cisco", "password": "cisco"},
        {"vendor": "juniper", "product": "junos", "category": "router", "protocol": "ssh", "user": "root", "password": "root123"},
        {"vendor": "juniper", "product": "junos", "category": "switch", "protocol": "ssh", "user": "admin", "password": "abc123"},
        {"vendor": "mikrotik", "product": "routeros", "category": "router", "protocol": "ssh", "user": "admin", "password": ""},
        {"vendor": "mikrotik", "product": "routeros", "category": "router", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "ubiquiti", "product": "unifi", "category": "wireless", "protocol": "ssh", "user": "ubnt", "password": "ubnt"},
        {"vendor": "ubiquiti", "product": "edgemax", "category": "router", "protocol": "ssh", "user": "ubnt", "password": "ubnt"},
        {"vendor": "tp-link", "product": "router", "category": "router", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "dlink", "product": "router", "category": "router", "protocol": "http", "user": "admin", "password": ""},
        {"vendor": "dlink", "product": "camera", "category": "camera", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "netgear", "product": "router", "category": "router", "protocol": "http", "user": "admin", "password": "password"},
        {"vendor": "netgear", "product": "switch", "category": "switch", "protocol": "http", "user": "admin", "password": ""},
        {"vendor": "hikvision", "product": "camera", "category": "camera", "protocol": "http", "user": "admin", "password": "12345"},
        {"vendor": "hikvision", "product": "nvr", "category": "camera", "protocol": "http", "user": "admin", "password": "admin12345"},
        {"vendor": "dahua", "product": "camera", "category": "camera", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "axis", "product": "camera", "category": "camera", "protocol": "http", "user": "root", "password": "pass"},
        {"vendor": "hp", "product": "ilo", "category": "network", "protocol": "https", "user": "Administrator", "password": "admin"},
        {"vendor": "hp", "product": "procurve", "category": "switch", "protocol": "ssh", "user": "admin", "password": ""},
        {"vendor": "dell", "product": "idrac", "category": "network", "protocol": "https", "user": "root", "password": "calvin"},
        {"vendor": "supermicro", "product": "ipmi", "category": "network", "protocol": "https", "user": "ADMIN", "password": "ADMIN"},
        {"vendor": "siemens", "product": "s7-300", "category": "plc", "protocol": "s7comm", "user": "", "password": ""},
        {"vendor": "siemens", "product": "s7-1200", "category": "plc", "protocol": "s7comm", "user": "admin", "password": "admin"},
        {"vendor": "siemens", "product": "wincc", "category": "hmi", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "schneider", "product": "m340", "category": "plc", "protocol": "modbus", "user": "USER", "password": "USER"},
        {"vendor": "schneider", "product": "quantum", "category": "plc", "protocol": "ftp", "user": "USER", "password": "USER"},
        {"vendor": "allen-bradley", "product": "controllogix", "category": "plc", "protocol": "http", "user": "admin", "password": "1234"},
        {"vendor": "honeywell", "product": "experion", "category": "scada", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "abb", "product": "800xa", "category": "scada", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "mysql", "product": "mysql", "category": "database", "protocol": "mysql", "user": "root", "password": ""},
        {"vendor": "mysql", "product": "mysql", "category": "database", "protocol": "mysql", "user": "root", "password": "root"},
        {"vendor": "postgresql", "product": "postgresql", "category": "database", "protocol": "postgresql", "user": "postgres", "password": "postgres"},
        {"vendor": "mongodb", "product": "mongodb", "category": "database", "protocol": "mongodb", "user": "admin", "password": "admin"},
        {"vendor": "redis", "product": "redis", "category": "database", "protocol": "redis", "user": "", "password": ""},
        {"vendor": "oracle", "product": "database", "category": "database", "protocol": "oracle", "user": "system", "password": "manager"},
        {"vendor": "oracle", "product": "database", "category": "database", "protocol": "oracle", "user": "sys", "password": "change_on_install"},
        {"vendor": "mssql", "product": "sqlserver", "category": "database", "protocol": "mssql", "user": "sa", "password": ""},
        {"vendor": "mssql", "product": "sqlserver", "category": "database", "protocol": "mssql", "user": "sa", "password": "sa"},
        {"vendor": "tomcat", "product": "tomcat", "category": "web", "protocol": "http", "user": "tomcat", "password": "tomcat"},
        {"vendor": "tomcat", "product": "tomcat", "category": "web", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "jenkins", "product": "jenkins", "category": "web", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "grafana", "product": "grafana", "category": "web", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "zabbix", "product": "zabbix", "category": "web", "protocol": "http", "user": "Admin", "password": "zabbix"},
        {"vendor": "nagios", "product": "nagios", "category": "web", "protocol": "http", "user": "nagiosadmin", "password": "nagios"},
        {"vendor": "pfsense", "product": "pfsense", "category": "firewall", "protocol": "https", "user": "admin", "password": "pfsense"},
        {"vendor": "fortinet", "product": "fortigate", "category": "firewall", "protocol": "https", "user": "admin", "password": ""},
        {"vendor": "sophos", "product": "utm", "category": "firewall", "protocol": "https", "user": "admin", "password": "admin"},
        {"vendor": "paloalto", "product": "panos", "category": "firewall", "protocol": "https", "user": "admin", "password": "admin"},
        {"vendor": "sonicwall", "product": "firewall", "category": "firewall", "protocol": "https", "user": "admin", "password": "password"},
        {"vendor": "qnap", "product": "nas", "category": "nas", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "synology", "product": "dsm", "category": "nas", "protocol": "https", "user": "admin", "password": ""},
        {"vendor": "raspberry", "product": "raspbian", "category": "iot", "protocol": "ssh", "user": "pi", "password": "raspberry"},
        {"vendor": "aws", "product": "ec2", "category": "cloud", "protocol": "ssh", "user": "ec2-user", "password": ""},
        {"vendor": "aws", "product": "ec2", "category": "cloud", "protocol": "ssh", "user": "ubuntu", "password": ""},
        {"vendor": "azure", "product": "vm", "category": "cloud", "protocol": "ssh", "user": "azureuser", "password": ""},
        {"vendor": "asterisk", "product": "freepbx", "category": "voip", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "grandstream", "product": "phone", "category": "voip", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "polycom", "product": "phone", "category": "voip", "protocol": "http", "user": "Polycom", "password": "456"},
        {"vendor": "avaya", "product": "phone", "category": "voip", "protocol": "http", "user": "admin", "password": "admin"},
        {"vendor": "hp", "product": "laserjet", "category": "printer", "protocol": "http", "user": "admin", "password": ""},
        {"vendor": "xerox", "product": "printer", "category": "printer", "protocol": "http", "user": "admin", "password": "1111"},
        {"vendor": "brother", "product": "printer", "category": "printer", "protocol": "http", "user": "admin", "password": "access"},
        {"vendor": "epson", "product": "printer", "category": "printer", "protocol": "http", "user": "epson", "password": "epson"},
    ]


_DB_CACHE: list[dict[str, str]] | None = None


def _get_db() -> list[dict[str, str]]:
    global _DB_CACHE
    if _DB_CACHE is not None:
        return _DB_CACHE

    ext_path = Path(__file__).parent / "resources" / "default_creds.json"
    if ext_path.exists():
        try:
            data = json.loads(ext_path.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                _DB_CACHE = data
                logger.info("Loaded %d credentials from %s", len(data), ext_path)
                return _DB_CACHE
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load external DB: %s", exc)

    _DB_CACHE = _builtin_db()
    return _DB_CACHE


def lookup(
    *,
    vendor: str = "",
    product: str = "",
    category: str = "",
    protocol: str = "",
) -> list[dict[str, str]]:
    """Search the default credential database.

    All filters are case-insensitive substring matches. Multiple filters
    are ANDed together.

    Returns:
        List of matching credential records.
    """
    db = _get_db()
    results: list[dict[str, str]] = []
    v = vendor.lower()
    p = product.lower()
    c = category.lower()
    pr = protocol.lower()

    for entry in db:
        if v and v not in entry.get("vendor", "").lower():
            continue
        if p and p not in entry.get("product", "").lower():
            continue
        if c and c not in entry.get("category", "").lower():
            continue
        if pr and pr not in entry.get("protocol", "").lower():
            continue
        results.append(entry)

    return results


def generate_pairs(
    *,
    vendor: str = "",
    product: str = "",
    category: str = "",
    protocol: str = "",
    include_variants: bool = True,
    output_format: str = "colon",
    max_candidates: int = 0,
) -> Generator[str, None, None]:
    """Generate credential pairs from the database with optional variants.

    Args:
        vendor: Filter by vendor name.
        product: Filter by product name.
        category: Filter by device category.
        protocol: Filter by protocol.
        include_variants: Add common mutations of found credentials.
        output_format: "colon" (user:pass), "tab", "hydra" (-l user -p pass).
        max_candidates: Limit output (0 = unlimited).

    Yields:
        Formatted credential strings.
    """
    matches = lookup(
        vendor=vendor, product=product,
        category=category, protocol=protocol,
    )

    seen: set[str] = set()
    emitted = 0

    def _fmt(user: str, pwd: str) -> str:
        if output_format == "tab":
            return f"{user}\t{pwd}"
        if output_format == "hydra":
            return f"-l {user} -p {pwd}"
        return f"{user}:{pwd}"

    def _emit(formatted: str) -> bool:
        nonlocal emitted
        if formatted in seen:
            return False
        seen.add(formatted)
        emitted += 1
        return True

    for entry in matches:
        user = entry.get("user", "")
        pwd = entry.get("password", "")
        line = _fmt(user, pwd)
        if _emit(line):
            yield line
            if max_candidates and emitted >= max_candidates:
                return

        if include_variants:
            variants_u = {user}
            variants_p = {pwd}
            if user:
                variants_u.add(user.lower())
                variants_u.add(user.upper())
            if pwd:
                variants_p.add(pwd + "1")
                variants_p.add(pwd + "123")
                variants_p.add(pwd + "!")
                variants_p.add(pwd.capitalize())

            for u in variants_u:
                for p in variants_p:
                    line = _fmt(u, p)
                    if _emit(line):
                        yield line
                        if max_candidates and emitted >= max_candidates:
                            return


def list_vendors() -> list[str]:
    """Return sorted unique vendor names in the database."""
    db = _get_db()
    return sorted({e.get("vendor", "") for e in db if e.get("vendor")})


def list_categories() -> list[str]:
    """Return sorted unique categories in the database."""
    db = _get_db()
    return sorted({e.get("category", "") for e in db if e.get("category")})


def stats() -> dict[str, int]:
    """Return summary statistics of the credential database."""
    db = _get_db()
    vendors = {e.get("vendor", "") for e in db if e.get("vendor")}
    categories = {e.get("category", "") for e in db if e.get("category")}
    protocols = {e.get("protocol", "") for e in db if e.get("protocol")}
    return {
        "total_entries": len(db),
        "vendors": len(vendors),
        "categories": len(categories),
        "protocols": len(protocols),
    }


def run(
    vendor: str = "",
    product: str = "",
    category: str = "",
    protocol: str = "",
    include_variants: bool = True,
    output_format: str = "colon",
    max_candidates: int = 0,
) -> list[str]:
    """Generate default credentials and return as list."""
    return list(generate_pairs(
        vendor=vendor, product=product,
        category=category, protocol=protocol,
        include_variants=include_variants,
        output_format=output_format,
        max_candidates=max_candidates,
    ))


def handle_default_creds(
    args: Any, _ctx: dict[str, Any],
) -> Generator[str, None, None] | None:
    """CLI handler for the default-creds subcommand."""
    vendor = getattr(args, "vendor", "") or ""
    product = getattr(args, "product", "") or ""
    category = getattr(args, "category", "") or ""
    protocol = getattr(args, "protocol", "") or ""
    fmt = getattr(args, "format", "colon") or "colon"
    variants = not getattr(args, "no_variants", False)
    limit = getattr(args, "limit", 0) or 0

    if not vendor and not product and not category and not protocol:
        logger.error("Provide at least --vendor, --product, --category, or --protocol.")
        return None

    return generate_pairs(
        vendor=vendor, product=product,
        category=category, protocol=protocol,
        include_variants=variants, output_format=fmt,
        max_candidates=limit,
    )

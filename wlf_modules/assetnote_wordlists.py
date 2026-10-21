"""
assetnote_wordlists.py: Manager for Assetnote Commonspeak2 wordlists.

Provides download, indexing, and management of the Assetnote wordlist
collection (assetnote/wordlists) which is generated monthly via
Commonspeak2 using BigQuery analysis of HTTP archives, DNS datasets,
and other real-world sources.

Categories include: subdomains, parameters, paths, technologies,
HTTP headers, and API routes.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

MANIFEST: dict[str, Any] = {
    "name": "assetnote_wordlists",
    "version": __version__,
    "category": "collection",
    "description": "Assetnote Commonspeak2 wordlist manager with download and indexing",
    "source_url": "https://github.com/assetnote/wordlists",
}

_REPO_URL = "https://github.com/assetnote/wordlists.git"
_RAW_BASE = "https://raw.githubusercontent.com/assetnote/wordlists/main/"
_RELEASE_API = "https://api.github.com/repos/assetnote/wordlists/releases"

_WORDLISTS_SITE = "https://wordlists.assetnote.io/"


@dataclass
class WordlistEntry:
    """Metadata for a single Assetnote wordlist file."""

    name: str
    category: str
    description: str
    url: str
    filename: str
    size_bytes: int = 0
    line_count: int = 0
    sha256: str = ""
    local_path: str = ""


CATALOG: dict[str, list[dict[str, str]]] = {
    "subdomains": [
        {
            "name": "best-dns-wordlist",
            "description": "Top subdomains from DNS datasets, high-quality curated list",
            "filename": "best-dns-wordlist.txt",
        },
        {
            "name": "httparchive_subdomains",
            "description": "Subdomains extracted from HTTP Archive crawls",
            "filename": "httparchive_subdomains_2024_12_28.txt",
        },
    ],
    "parameters": [
        {
            "name": "httparchive_parameters",
            "description": "GET/POST parameters found in HTTP Archive data",
            "filename": "httparchive_parameters_2024_12_28.txt",
        },
        {
            "name": "burp_parameter_names",
            "description": "Parameter names collected from Burp Suite community scans",
            "filename": "burp_parameter_names.txt",
        },
    ],
    "paths": [
        {
            "name": "httparchive_directories",
            "description": "Directory paths from HTTP Archive crawls",
            "filename": "httparchive_directories_1m_2024_12_28.txt",
        },
        {
            "name": "httparchive_jsp_filenames",
            "description": "JSP filenames from HTTP Archive",
            "filename": "httparchive_jsp_filenames_2024_12_28.txt",
        },
        {
            "name": "httparchive_php_filenames",
            "description": "PHP filenames from HTTP Archive",
            "filename": "httparchive_php_filenames_2024_12_28.txt",
        },
        {
            "name": "httparchive_aspx_filenames",
            "description": "ASPX filenames from HTTP Archive",
            "filename": "httparchive_aspx_asp_filenames_2024_12_28.txt",
        },
    ],
    "technologies": [
        {
            "name": "httparchive_xml_filenames",
            "description": "XML filenames from HTTP Archive",
            "filename": "httparchive_xml_filenames_2024_12_28.txt",
        },
        {
            "name": "httparchive_cgi_filenames",
            "description": "CGI filenames from HTTP Archive",
            "filename": "httparchive_cgi_filenames_2024_12_28.txt",
        },
    ],
    "api": [
        {
            "name": "httparchive_apiroutes",
            "description": "API route patterns from HTTP Archive",
            "filename": "httparchive_apiroutes_2024_12_28.txt",
        },
    ],
}


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        path: File path.

    Returns:
        Hex digest string.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _count_lines(path: Path) -> int:
    """Count non-empty lines in a text file.

    Args:
        path: File path.

    Returns:
        Number of non-empty lines.
    """
    count = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


class AssetnoteWordlists:
    """Manager for Assetnote wordlist collection."""

    def __init__(
        self,
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize the Assetnote wordlists manager.

        Args:
            data_dir: Directory for storing downloaded wordlists.
                      Defaults to ~/.local/share/wlf/assetnote.
        """
        if data_dir is None:
            self._data_dir = Path.home() / ".local" / "share" / "wlf" / "assetnote"
        else:
            self._data_dir = Path(data_dir)
        self._index_file = self._data_dir / "index.json"
        self._index: dict[str, Any] = {}

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def _ensure_dir(self) -> None:
        """Create the data directory if it does not exist."""
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> dict[str, Any]:
        """Load the local index of downloaded wordlists."""
        if self._index:
            return self._index
        if self._index_file.exists():
            try:
                self._index = json.loads(self._index_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._index = {}
        return self._index

    def _save_index(self) -> None:
        """Persist the index to disk."""
        self._ensure_dir()
        self._index_file.write_text(
            json.dumps(self._index, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def list_categories(self) -> list[str]:
        """Return all available wordlist categories.

        Returns:
            List of category names.
        """
        return list(CATALOG.keys())

    def list_wordlists(self, category: str | None = None) -> list[dict[str, str]]:
        """List available wordlists, optionally filtered by category.

        Args:
            category: Filter by this category. None returns all.

        Returns:
            List of wordlist metadata dicts.
        """
        results: list[dict[str, str]] = []
        cats = [category] if category and category in CATALOG else list(CATALOG.keys())
        for cat in cats:
            for entry in CATALOG.get(cat, []):
                item = dict(entry)
                item["category"] = cat
                local_path = self._data_dir / cat / entry["filename"]
                item["downloaded"] = str(local_path.exists())
                if local_path.exists():
                    item["local_path"] = str(local_path)
                results.append(item)
        return results

    def download(
        self,
        name: str,
        category: str | None = None,
        force: bool = False,
        timeout: int = 300,
    ) -> WordlistEntry:
        """Download a specific wordlist by name.

        Tries the Assetnote wordlists site first, then falls back
        to raw GitHub content.

        Args:
            name: Wordlist name (matches catalog entry name).
            category: Category hint to narrow search.
            force: Re-download even if already present.
            timeout: Download timeout in seconds.

        Returns:
            WordlistEntry with local path and metadata.

        Raises:
            ValueError: If wordlist name not found in catalog.
            RuntimeError: If download fails.
        """
        entry_data: dict[str, str] | None = None
        entry_cat = ""

        cats = [category] if category and category in CATALOG else list(CATALOG.keys())
        for cat in cats:
            for item in CATALOG.get(cat, []):
                if item["name"] == name:
                    entry_data = item
                    entry_cat = cat
                    break
            if entry_data:
                break

        if not entry_data:
            raise ValueError(
                f"Wordlist '{name}' not found in catalog. "
                f"Available: {[e['name'] for c in CATALOG.values() for e in c]}"
            )

        self._ensure_dir()
        cat_dir = self._data_dir / entry_cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        local_path = cat_dir / entry_data["filename"]

        if local_path.exists() and not force:
            logger.info("Wordlist already downloaded: %s", local_path)
            return self._build_entry(entry_data, entry_cat, local_path)

        download_url = f"{_WORDLISTS_SITE}data/{entry_cat}/{entry_data['filename']}"
        fallback_url = f"{_RAW_BASE}{entry_cat}/{entry_data['filename']}"

        downloaded = False
        for url in [download_url, fallback_url]:
            try:
                logger.info("Downloading %s from %s", name, url)
                result = subprocess.run(
                    ["curl", "-fSL", "--max-time", str(timeout),
                     "-o", str(local_path), url],
                    capture_output=True,
                    text=True,
                    timeout=timeout + 30,
                )
                if result.returncode == 0 and local_path.exists() and local_path.stat().st_size > 0:
                    downloaded = True
                    break
            except (subprocess.TimeoutExpired, OSError) as exc:
                logger.warning("Download attempt failed for %s: %s", url, exc)

        if not downloaded:
            if local_path.exists():
                local_path.unlink()
            raise RuntimeError(f"Failed to download wordlist '{name}'")

        entry = self._build_entry(entry_data, entry_cat, local_path)

        self._load_index()
        self._index[name] = {
            "category": entry_cat,
            "filename": entry_data["filename"],
            "local_path": str(local_path),
            "sha256": entry.sha256,
            "size_bytes": entry.size_bytes,
            "line_count": entry.line_count,
        }
        self._save_index()

        return entry

    def download_category(
        self,
        category: str,
        force: bool = False,
        timeout: int = 300,
    ) -> list[WordlistEntry]:
        """Download all wordlists in a category.

        Args:
            category: Category name.
            force: Re-download existing files.
            timeout: Per-file timeout.

        Returns:
            List of downloaded WordlistEntry objects.

        Raises:
            ValueError: If category not found.
        """
        if category not in CATALOG:
            raise ValueError(
                f"Category '{category}' not found. Available: {list(CATALOG.keys())}"
            )

        results: list[WordlistEntry] = []
        for item in CATALOG[category]:
            try:
                entry = self.download(item["name"], category, force=force, timeout=timeout)
                results.append(entry)
            except RuntimeError as exc:
                logger.error("Failed to download %s: %s", item["name"], exc)
        return results

    def download_all(
        self,
        force: bool = False,
        timeout: int = 300,
    ) -> list[WordlistEntry]:
        """Download all wordlists from all categories.

        Args:
            force: Re-download existing files.
            timeout: Per-file timeout.

        Returns:
            List of all downloaded entries.
        """
        results: list[WordlistEntry] = []
        for cat in CATALOG:
            results.extend(self.download_category(cat, force=force, timeout=timeout))
        return results

    def get_local_path(self, name: str) -> Path | None:
        """Get the local path for a previously downloaded wordlist.

        Args:
            name: Wordlist name.

        Returns:
            Path if downloaded, None otherwise.
        """
        self._load_index()
        info = self._index.get(name)
        if info:
            p = Path(info["local_path"])
            if p.exists():
                return p
        for cat, items in CATALOG.items():
            for item in items:
                if item["name"] == name:
                    candidate = self._data_dir / cat / item["filename"]
                    if candidate.exists():
                        return candidate
        return None

    def search(self, query: str) -> list[dict[str, str]]:
        """Search wordlists by name or description substring.

        Args:
            query: Search string (case-insensitive).

        Returns:
            Matching wordlist entries.
        """
        q = query.lower()
        results: list[dict[str, str]] = []
        for cat, items in CATALOG.items():
            for item in items:
                if q in item["name"].lower() or q in item.get("description", "").lower():
                    entry = dict(item)
                    entry["category"] = cat
                    results.append(entry)
        return results

    def stats(self) -> dict[str, Any]:
        """Return statistics about downloaded wordlists.

        Returns:
            Dict with total_files, total_size_bytes, categories, etc.
        """
        self._load_index()
        total_files = 0
        total_size = 0
        total_lines = 0
        cat_counts: dict[str, int] = {}

        for name, info in self._index.items():
            p = Path(info.get("local_path", ""))
            if p.exists():
                total_files += 1
                total_size += info.get("size_bytes", 0)
                total_lines += info.get("line_count", 0)
                cat = info.get("category", "unknown")
                cat_counts[cat] = cat_counts.get(cat, 0) + 1

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_lines": total_lines,
            "categories": cat_counts,
            "catalog_total": sum(len(v) for v in CATALOG.values()),
        }

    def cleanup(self, category: str | None = None) -> int:
        """Remove downloaded wordlists.

        Args:
            category: Remove only this category. None removes all.

        Returns:
            Number of files removed.
        """
        removed = 0
        if category:
            cat_dir = self._data_dir / category
            if cat_dir.exists():
                for f in cat_dir.iterdir():
                    if f.is_file() and f.suffix == ".txt":
                        f.unlink()
                        removed += 1
        else:
            for cat in CATALOG:
                cat_dir = self._data_dir / cat
                if cat_dir.exists():
                    for f in cat_dir.iterdir():
                        if f.is_file() and f.suffix == ".txt":
                            f.unlink()
                            removed += 1
            self._index = {}
            self._save_index()

        logger.info("Removed %d wordlist files", removed)
        return removed

    def _build_entry(
        self,
        item: dict[str, str],
        category: str,
        local_path: Path,
    ) -> WordlistEntry:
        """Build a WordlistEntry from catalog item and local file.

        Args:
            item: Catalog item dict.
            category: Category name.
            local_path: Path to local file.

        Returns:
            Populated WordlistEntry.
        """
        size = local_path.stat().st_size if local_path.exists() else 0
        lines = _count_lines(local_path) if local_path.exists() else 0
        sha = _sha256_file(local_path) if local_path.exists() else ""

        return WordlistEntry(
            name=item["name"],
            category=category,
            description=item.get("description", ""),
            url=f"{_WORDLISTS_SITE}data/{category}/{item['filename']}",
            filename=item["filename"],
            size_bytes=size,
            line_count=lines,
            sha256=sha,
            local_path=str(local_path),
        )

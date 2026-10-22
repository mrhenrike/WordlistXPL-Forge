"""
trickest_wordlists.py: Manager for Trickest real-world crawled wordlists.

Fetches, indexes, and manages the Trickest wordlist collection
(trickest/wordlists), which contains large-scale wordlists compiled
from real-world data gathered during bug bounty and security research.

Categories: technologies, robots, inventory, servers, extensions.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

MANIFEST: dict[str, Any] = {
    "name": "trickest_wordlists",
    "version": __version__,
    "category": "collection",
    "description": "Trickest real-world crawled wordlist manager with download and indexing",
    "source_url": "https://github.com/trickest/wordlists",
}

_REPO_URL = "https://github.com/trickest/wordlists.git"
_RAW_BASE = "https://raw.githubusercontent.com/trickest/wordlists/main/"


@dataclass
class TrickestEntry:
    """Metadata for a single Trickest wordlist file."""

    name: str
    category: str
    description: str
    filename: str
    remote_path: str
    size_bytes: int = 0
    line_count: int = 0
    sha256: str = ""
    local_path: str = ""


CATALOG: dict[str, list[dict[str, str]]] = {
    "technologies": [
        {
            "name": "nginx-wordlist",
            "description": "Paths and files specific to nginx servers",
            "filename": "nginx.txt",
            "remote_path": "technologies/nginx.txt",
        },
        {
            "name": "apache-wordlist",
            "description": "Paths and files specific to Apache HTTP servers",
            "filename": "apache.txt",
            "remote_path": "technologies/apache.txt",
        },
        {
            "name": "tomcat-wordlist",
            "description": "Paths and files specific to Apache Tomcat",
            "filename": "tomcat.txt",
            "remote_path": "technologies/tomcat.txt",
        },
        {
            "name": "iis-wordlist",
            "description": "Paths and files specific to Microsoft IIS",
            "filename": "iis.txt",
            "remote_path": "technologies/iis.txt",
        },
        {
            "name": "php-wordlist",
            "description": "PHP-related paths and filenames",
            "filename": "PHP.txt",
            "remote_path": "technologies/PHP.txt",
        },
        {
            "name": "wordpress-wordlist",
            "description": "WordPress-specific paths, plugins, themes",
            "filename": "wordpress.txt",
            "remote_path": "technologies/wordpress.txt",
        },
        {
            "name": "joomla-wordlist",
            "description": "Joomla CMS specific paths",
            "filename": "joomla.txt",
            "remote_path": "technologies/joomla.txt",
        },
        {
            "name": "drupal-wordlist",
            "description": "Drupal CMS specific paths",
            "filename": "drupal.txt",
            "remote_path": "technologies/drupal.txt",
        },
    ],
    "robots": [
        {
            "name": "robots-disallowed",
            "description": "Disallowed paths from robots.txt files across the internet",
            "filename": "robots-disallowed.txt",
            "remote_path": "robots/robots-disallowed.txt",
        },
    ],
    "inventory": [
        {
            "name": "subdomains-top100k",
            "description": "Top 100K subdomains from real-world DNS data",
            "filename": "subdomains-100.txt",
            "remote_path": "inventory/subdomains-100.txt",
        },
        {
            "name": "subdomains-top1m",
            "description": "Top 1M subdomains from real-world DNS data",
            "filename": "subdomains-1000.txt",
            "remote_path": "inventory/subdomains-1000.txt",
        },
    ],
    "servers": [
        {
            "name": "directory-listing",
            "description": "Common directory listing paths across servers",
            "filename": "directory-listing.txt",
            "remote_path": "servers/directory-listing.txt",
        },
    ],
    "extensions": [
        {
            "name": "common-extensions",
            "description": "Common web file extensions",
            "filename": "common-extensions.txt",
            "remote_path": "extensions/common-extensions.txt",
        },
    ],
}


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _count_lines(path: Path) -> int:
    """Count non-empty lines in a file."""
    count = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


class TrickestWordlists:
    """Manager for the Trickest wordlist collection."""

    def __init__(
        self,
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize the Trickest wordlists manager.

        Args:
            data_dir: Directory for storing downloaded wordlists.
                      Defaults to ~/.local/share/wlf/trickest.
        """
        if data_dir is None:
            self._data_dir = Path.home() / ".local" / "share" / "wlf" / "trickest"
        else:
            self._data_dir = Path(data_dir)
        self._index_file = self._data_dir / "index.json"
        self._index: dict[str, Any] = {}
        self._repo_dir = self._data_dir / "_repo"

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def _ensure_dir(self) -> None:
        """Create data directory structure."""
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> dict[str, Any]:
        """Load the local download index."""
        if self._index:
            return self._index
        if self._index_file.exists():
            try:
                self._index = json.loads(self._index_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._index = {}
        return self._index

    def _save_index(self) -> None:
        """Persist the download index."""
        self._ensure_dir()
        self._index_file.write_text(
            json.dumps(self._index, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def clone_repo(self, force: bool = False, sparse: bool = True) -> Path:
        """Clone the Trickest wordlists repository.

        Uses sparse checkout by default to avoid downloading
        multi-gigabyte files unnecessarily.

        Args:
            force: Re-clone even if already present.
            sparse: Use sparse checkout (recommended for large repo).

        Returns:
            Path to cloned repo.

        Raises:
            RuntimeError: If clone fails.
        """
        if self._repo_dir.exists():
            if not force:
                logger.info("Trickest repo already cloned at %s", self._repo_dir)
                return self._repo_dir
            shutil.rmtree(self._repo_dir)

        self._ensure_dir()
        logger.info("Cloning Trickest wordlists repo (sparse=%s)", sparse)

        if sparse:
            self._repo_dir.mkdir(parents=True, exist_ok=True)
            cmds = [
                ["git", "init", str(self._repo_dir)],
                ["git", "-C", str(self._repo_dir), "remote", "add", "origin", _REPO_URL],
                ["git", "-C", str(self._repo_dir), "config", "core.sparseCheckout", "true"],
            ]
            for cmd in cmds:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    raise RuntimeError(f"Git setup failed: {result.stderr.strip()}")

            sparse_file = self._repo_dir / ".git" / "info" / "sparse-checkout"
            sparse_file.parent.mkdir(parents=True, exist_ok=True)
            sparse_file.write_text("README.md\n", encoding="utf-8")

            result = subprocess.run(
                ["git", "-C", str(self._repo_dir), "pull", "--depth", "1", "origin", "main"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Sparse pull failed: {result.stderr.strip()}")
        else:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", _REPO_URL, str(self._repo_dir)],
                capture_output=True, text=True, timeout=600,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Clone failed: {result.stderr.strip()}")

        return self._repo_dir

    def list_categories(self) -> list[str]:
        """Return available wordlist categories."""
        return list(CATALOG.keys())

    def list_wordlists(self, category: str | None = None) -> list[dict[str, str]]:
        """List available wordlists with download status.

        Args:
            category: Optional category filter.

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
        timeout: int = 600,
    ) -> TrickestEntry:
        """Download a specific wordlist by name.

        Downloads from raw GitHub content URL.

        Args:
            name: Wordlist name from catalog.
            category: Category hint.
            force: Re-download if already present.
            timeout: Download timeout.

        Returns:
            TrickestEntry with local path and metadata.

        Raises:
            ValueError: If name not found in catalog.
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
            all_names = [e["name"] for c in CATALOG.values() for e in c]
            raise ValueError(
                f"Wordlist '{name}' not found. Available: {all_names}"
            )

        self._ensure_dir()
        cat_dir = self._data_dir / entry_cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        local_path = cat_dir / entry_data["filename"]

        if local_path.exists() and not force:
            logger.info("Already downloaded: %s", local_path)
            return self._build_entry(entry_data, entry_cat, local_path)

        url = f"{_RAW_BASE}{entry_data['remote_path']}"
        logger.info("Downloading %s from %s", name, url)

        result = subprocess.run(
            ["curl", "-fSL", "--max-time", str(timeout),
             "-o", str(local_path), url],
            capture_output=True,
            text=True,
            timeout=timeout + 30,
        )
        if result.returncode != 0 or not local_path.exists() or local_path.stat().st_size == 0:
            if local_path.exists():
                local_path.unlink()
            raise RuntimeError(f"Failed to download '{name}': {result.stderr.strip()}")

        entry = self._build_entry(entry_data, entry_cat, local_path)

        self._load_index()
        self._index[name] = {
            "category": entry_cat,
            "filename": entry_data["filename"],
            "remote_path": entry_data["remote_path"],
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
        timeout: int = 600,
    ) -> list[TrickestEntry]:
        """Download all wordlists in a category.

        Args:
            category: Category name.
            force: Re-download existing.
            timeout: Per-file timeout.

        Returns:
            List of downloaded entries.
        """
        if category not in CATALOG:
            raise ValueError(f"Category '{category}' not found. Available: {list(CATALOG.keys())}")

        results: list[TrickestEntry] = []
        for item in CATALOG[category]:
            try:
                entry = self.download(item["name"], category, force=force, timeout=timeout)
                results.append(entry)
            except RuntimeError as exc:
                logger.error("Failed to download %s: %s", item["name"], exc)
        return results

    def search(self, query: str) -> list[dict[str, str]]:
        """Search wordlists by name or description.

        Args:
            query: Case-insensitive search string.

        Returns:
            Matching entries.
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

    def merge_wordlists(
        self,
        names: list[str],
        output_file: str | Path,
        deduplicate: bool = True,
        sort: bool = True,
    ) -> Path:
        """Merge multiple downloaded wordlists into a single file.

        Args:
            names: Wordlist names to merge.
            output_file: Output file path.
            deduplicate: Remove duplicate lines.
            sort: Sort the output.

        Returns:
            Path to merged wordlist.

        Raises:
            FileNotFoundError: If any wordlist is not downloaded.
        """
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        lines: set[str] = set() if deduplicate else None
        ordered: list[str] = [] if not deduplicate else []

        for name in names:
            local = self.get_local_path(name)
            if not local:
                raise FileNotFoundError(
                    f"Wordlist '{name}' not downloaded. Call download() first."
                )
            with open(local, encoding="utf-8", errors="replace") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        if deduplicate:
                            if stripped not in lines:
                                lines.add(stripped)
                                ordered.append(stripped)
                        else:
                            ordered.append(stripped)

        if sort:
            ordered.sort()

        out_path.write_text("\n".join(ordered) + "\n", encoding="utf-8")
        logger.info("Merged %d unique lines into %s", len(ordered), out_path)
        return out_path

    def get_local_path(self, name: str) -> Path | None:
        """Get local path for a downloaded wordlist.

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

    def stats(self) -> dict[str, Any]:
        """Return download statistics.

        Returns:
            Dict with total_files, total_size, categories, etc.
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
        cats = [category] if category else list(CATALOG.keys())
        for cat in cats:
            cat_dir = self._data_dir / cat
            if cat_dir.exists():
                for f in cat_dir.iterdir():
                    if f.is_file() and f.suffix == ".txt":
                        f.unlink()
                        removed += 1
        if not category:
            self._index = {}
            self._save_index()
        logger.info("Removed %d wordlist files", removed)
        return removed

    def _build_entry(
        self,
        item: dict[str, str],
        category: str,
        local_path: Path,
    ) -> TrickestEntry:
        """Build a TrickestEntry from catalog item and local file."""
        size = local_path.stat().st_size if local_path.exists() else 0
        lines = _count_lines(local_path) if local_path.exists() else 0
        sha = _sha256_file(local_path) if local_path.exists() else ""

        return TrickestEntry(
            name=item["name"],
            category=category,
            description=item.get("description", ""),
            filename=item["filename"],
            remote_path=item.get("remote_path", ""),
            size_bytes=size,
            line_count=lines,
            sha256=sha,
            local_path=str(local_path),
        )

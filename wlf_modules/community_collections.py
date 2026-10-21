"""
community_collections.py: Registry and manager for curated wordlist collections.

Provides unified access to multiple community-maintained wordlist
repositories and collections:

  - kkrypt0nn/wordlists: Multi-purpose curated wordlists for various uses
  - g0tmi1k/debian-default: Default credentials database
  - danielmiessler/SecLists: Large security assessment wordlist collection
  - awesome-password-cracking: Curated resource list for password cracking
  - WordList-Compendium: Aggregated wordlist compilation
  - bruteforce-database: Collection of common credential files

Each collection can be cloned, updated, indexed, and its wordlists
accessed individually or merged for targeted operations.

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

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

MANIFEST: dict[str, Any] = {
    "name": "community_collections",
    "version": __version__,
    "category": "collection",
    "description": "Registry and manager for curated community wordlist collections",
    "source_url": "https://github.com/kkrypt0nn/wordlists",
}


@dataclass
class CollectionMeta:
    """Metadata describing a community wordlist collection."""

    name: str
    description: str
    repo_url: str
    default_branch: str = "main"
    categories: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=lambda: ["*.txt"])
    sparse_paths: list[str] = field(default_factory=list)
    license: str = ""
    notes: str = ""


REGISTRY: dict[str, CollectionMeta] = {
    "kkrypt0nn-wordlists": CollectionMeta(
        name="kkrypt0nn/wordlists",
        description="Multi-purpose wordlists for content discovery, credentials, subdomains, fuzzing",
        repo_url="https://github.com/kkrypt0nn/wordlists.git",
        default_branch="main",
        categories=["passwords", "usernames", "subdomains", "directories", "fuzzing"],
        file_patterns=["*.txt"],
        license="MIT",
    ),
    "awesome-password-cracking": CollectionMeta(
        name="awesome-password-cracking",
        description="Curated list of password cracking tools, rules, wordlists, and research",
        repo_url="https://github.com/n0kovo/awesome-password-cracking.git",
        default_branch="main",
        categories=["meta", "resources", "tools"],
        file_patterns=["*.md", "*.txt"],
        license="CC0",
        notes="Primarily a resource index; contains links to tools and wordlists rather than raw data",
    ),
    "wordlist-compendium": CollectionMeta(
        name="WordList-Compendium",
        description="Aggregated compilation of wordlists from multiple sources for penetration testing",
        repo_url="https://github.com/Dormidera/WordList-Compendium.git",
        default_branch="master",
        categories=["passwords", "usernames", "web", "network"],
        file_patterns=["*.txt", "*.lst"],
    ),
    "bruteforce-database": CollectionMeta(
        name="bruteforce-database",
        description="Collection of common usernames and passwords for bruteforce attacks",
        repo_url="https://github.com/duyet/bruteforce-database.git",
        default_branch="master",
        categories=["passwords", "usernames", "credentials"],
        file_patterns=["*.txt"],
    ),
}


@dataclass
class WordlistFile:
    """Represents a single wordlist file within a collection."""

    collection: str
    relative_path: str
    absolute_path: str
    category: str
    size_bytes: int = 0
    line_count: int = 0
    sha256: str = ""


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _count_lines(path: Path) -> int:
    """Count non-empty lines in a file."""
    count = 0
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    count += 1
    except OSError:
        pass
    return count


def _guess_category(relative_path: str) -> str:
    """Guess the category of a wordlist from its path.

    Args:
        relative_path: Path relative to collection root.

    Returns:
        Category string.
    """
    lower = relative_path.lower()
    category_hints: dict[str, list[str]] = {
        "passwords": ["pass", "cred", "leak", "common", "rockyou", "default"],
        "usernames": ["user", "name", "login", "account"],
        "subdomains": ["subdomain", "dns", "domain"],
        "directories": ["dir", "path", "route", "endpoint", "web"],
        "fuzzing": ["fuzz", "inject", "payload", "xss", "sqli", "traversal"],
        "credentials": ["credential", "combo", "pair"],
    }
    for cat, hints in category_hints.items():
        for hint in hints:
            if hint in lower:
                return cat
    return "general"


class CommunityCollections:
    """Manager for community-maintained wordlist collections."""

    def __init__(
        self,
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize the community collections manager.

        Args:
            data_dir: Base directory for storing cloned collections.
                      Defaults to ~/.local/share/wlf/community.
        """
        if data_dir is None:
            self._data_dir = Path.home() / ".local" / "share" / "wlf" / "community"
        else:
            self._data_dir = Path(data_dir)
        self._index_file = self._data_dir / "collections_index.json"
        self._index: dict[str, Any] = {}

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def _ensure_dir(self) -> None:
        """Create base directory."""
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> dict[str, Any]:
        """Load the local index."""
        if self._index:
            return self._index
        if self._index_file.exists():
            try:
                self._index = json.loads(self._index_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._index = {}
        return self._index

    def _save_index(self) -> None:
        """Persist the index."""
        self._ensure_dir()
        self._index_file.write_text(
            json.dumps(self._index, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def list_collections(self) -> list[dict[str, Any]]:
        """List all registered collections with status.

        Returns:
            List of collection metadata with clone status.
        """
        results: list[dict[str, Any]] = []
        for key, meta in REGISTRY.items():
            clone_dir = self._data_dir / key
            results.append({
                "key": key,
                "name": meta.name,
                "description": meta.description,
                "repo_url": meta.repo_url,
                "categories": meta.categories,
                "cloned": clone_dir.exists(),
                "license": meta.license,
                "notes": meta.notes,
            })
        return results

    def get_collection_meta(self, key: str) -> CollectionMeta | None:
        """Get metadata for a specific collection.

        Args:
            key: Collection registry key.

        Returns:
            CollectionMeta or None if not found.
        """
        return REGISTRY.get(key)

    def clone_collection(
        self,
        key: str,
        force: bool = False,
        depth: int = 1,
        timeout: int = 300,
    ) -> Path:
        """Clone a collection repository.

        Args:
            key: Collection registry key.
            force: Re-clone even if present.
            depth: Git clone depth (1 for shallow).
            timeout: Clone timeout in seconds.

        Returns:
            Path to cloned directory.

        Raises:
            ValueError: If key not in registry.
            RuntimeError: If clone fails.
        """
        meta = REGISTRY.get(key)
        if not meta:
            raise ValueError(
                f"Collection '{key}' not in registry. "
                f"Available: {list(REGISTRY.keys())}"
            )

        clone_dir = self._data_dir / key

        if clone_dir.exists():
            if not force:
                logger.info("Collection '%s' already cloned at %s", key, clone_dir)
                return clone_dir
            shutil.rmtree(clone_dir)

        self._ensure_dir()
        logger.info("Cloning collection '%s' from %s", key, meta.repo_url)

        args = ["git", "clone"]
        if depth > 0:
            args.extend(["--depth", str(depth)])
        args.extend(["-b", meta.default_branch, meta.repo_url, str(clone_dir)])

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to clone '{key}': {result.stderr.strip()}"
            )

        self._load_index()
        self._index[key] = {
            "cloned": True,
            "path": str(clone_dir),
            "branch": meta.default_branch,
        }
        self._save_index()

        return clone_dir

    def clone_all(
        self,
        force: bool = False,
        depth: int = 1,
        timeout: int = 300,
    ) -> dict[str, Path | str]:
        """Clone all registered collections.

        Args:
            force: Re-clone all.
            depth: Clone depth.
            timeout: Per-collection timeout.

        Returns:
            Dict mapping collection key to path or error string.
        """
        results: dict[str, Path | str] = {}
        for key in REGISTRY:
            try:
                path = self.clone_collection(key, force=force, depth=depth, timeout=timeout)
                results[key] = path
            except RuntimeError as exc:
                logger.error("Failed to clone '%s': %s", key, exc)
                results[key] = f"ERROR: {exc}"
        return results

    def update_collection(self, key: str, timeout: int = 120) -> bool:
        """Pull latest changes for a cloned collection.

        Args:
            key: Collection registry key.
            timeout: Pull timeout.

        Returns:
            True if update succeeded.
        """
        clone_dir = self._data_dir / key
        if not clone_dir.exists():
            logger.warning("Collection '%s' not cloned", key)
            return False

        result = subprocess.run(
            ["git", "-C", str(clone_dir), "pull", "--ff-only"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            logger.error("Failed to update '%s': %s", key, result.stderr.strip())
            return False

        logger.info("Updated collection '%s'", key)
        return True

    def index_collection(
        self,
        key: str,
        max_files: int = 10_000,
    ) -> list[WordlistFile]:
        """Index all wordlist files in a collection.

        Scans the cloned repository for wordlist files matching
        the collection's file patterns.

        Args:
            key: Collection registry key.
            max_files: Safety limit on number of files to index.

        Returns:
            List of WordlistFile entries.

        Raises:
            ValueError: If collection not cloned.
        """
        meta = REGISTRY.get(key)
        if not meta:
            raise ValueError(f"Collection '{key}' not in registry")

        clone_dir = self._data_dir / key
        if not clone_dir.exists():
            raise ValueError(f"Collection '{key}' not cloned. Call clone_collection() first.")

        results: list[WordlistFile] = []
        count = 0

        for pattern in meta.file_patterns:
            for match in sorted(clone_dir.rglob(pattern)):
                if count >= max_files:
                    break
                if not match.is_file():
                    continue
                if ".git" in match.parts:
                    continue

                rel = str(match.relative_to(clone_dir))
                category = _guess_category(rel)

                wf = WordlistFile(
                    collection=key,
                    relative_path=rel,
                    absolute_path=str(match),
                    category=category,
                    size_bytes=match.stat().st_size,
                )
                results.append(wf)
                count += 1

        logger.info("Indexed %d files in collection '%s'", len(results), key)
        return results

    def search_files(
        self,
        query: str,
        collection: str | None = None,
        category: str | None = None,
    ) -> list[WordlistFile]:
        """Search for wordlist files across collections.

        Args:
            query: Case-insensitive search in file paths.
            collection: Limit search to this collection.
            category: Filter by guessed category.

        Returns:
            Matching WordlistFile entries.
        """
        q = query.lower()
        results: list[WordlistFile] = []
        keys = [collection] if collection and collection in REGISTRY else list(REGISTRY.keys())

        for key in keys:
            clone_dir = self._data_dir / key
            if not clone_dir.exists():
                continue
            meta = REGISTRY[key]
            for pattern in meta.file_patterns:
                for match in clone_dir.rglob(pattern):
                    if not match.is_file() or ".git" in match.parts:
                        continue
                    rel = str(match.relative_to(clone_dir))
                    if q not in rel.lower():
                        continue
                    cat = _guess_category(rel)
                    if category and cat != category:
                        continue
                    results.append(WordlistFile(
                        collection=key,
                        relative_path=rel,
                        absolute_path=str(match),
                        category=cat,
                        size_bytes=match.stat().st_size,
                    ))

        return results

    def get_wordlist(
        self,
        collection: str,
        relative_path: str,
        compute_hash: bool = False,
        count_lines: bool = False,
    ) -> WordlistFile | None:
        """Get a specific wordlist file from a collection.

        Args:
            collection: Collection key.
            relative_path: Path relative to collection root.
            compute_hash: Compute SHA-256 hash.
            count_lines: Count lines in the file.

        Returns:
            WordlistFile or None if not found.
        """
        clone_dir = self._data_dir / collection
        target = clone_dir / relative_path
        if not target.exists() or not target.is_file():
            return None

        wf = WordlistFile(
            collection=collection,
            relative_path=relative_path,
            absolute_path=str(target),
            category=_guess_category(relative_path),
            size_bytes=target.stat().st_size,
        )
        if compute_hash:
            wf.sha256 = _sha256_file(target)
        if count_lines:
            wf.line_count = _count_lines(target)
        return wf

    def merge_collection_files(
        self,
        collection: str,
        output_file: str | Path,
        category: str | None = None,
        deduplicate: bool = True,
        max_lines: int = 5_000_000,
    ) -> Path:
        """Merge wordlist files from a collection into one file.

        Args:
            collection: Collection key.
            output_file: Output path.
            category: Only merge files from this category.
            deduplicate: Remove duplicate lines.
            max_lines: Safety cap on total lines.

        Returns:
            Path to merged file.
        """
        files = self.index_collection(collection)
        if category:
            files = [f for f in files if f.category == category]

        out = Path(output_file)
        out.parent.mkdir(parents=True, exist_ok=True)

        seen: set[str] = set() if deduplicate else None  # type: ignore[assignment]
        line_count = 0

        with open(out, "w", encoding="utf-8") as outf:
            for wf in files:
                if line_count >= max_lines:
                    logger.warning("Reached max_lines limit (%d)", max_lines)
                    break
                try:
                    with open(wf.absolute_path, encoding="utf-8", errors="replace") as inf:
                        for line in inf:
                            stripped = line.strip()
                            if not stripped:
                                continue
                            if deduplicate:
                                if stripped in seen:
                                    continue
                                seen.add(stripped)  # type: ignore[union-attr]
                            outf.write(stripped + "\n")
                            line_count += 1
                            if line_count >= max_lines:
                                break
                except OSError as exc:
                    logger.warning("Could not read %s: %s", wf.absolute_path, exc)

        logger.info(
            "Merged %d lines from %d files in '%s' into %s",
            line_count, len(files), collection, out,
        )
        return out

    def stats(self) -> dict[str, Any]:
        """Return statistics about all collections.

        Returns:
            Dict with per-collection and aggregate stats.
        """
        overall: dict[str, Any] = {
            "registered": len(REGISTRY),
            "cloned": 0,
            "total_size_bytes": 0,
            "collections": {},
        }

        for key in REGISTRY:
            clone_dir = self._data_dir / key
            if not clone_dir.exists():
                overall["collections"][key] = {"cloned": False}
                continue

            overall["cloned"] += 1
            total_size = 0
            file_count = 0
            for root, _dirs, filenames in os.walk(clone_dir):
                if ".git" in root:
                    continue
                for fn in filenames:
                    fp = Path(root) / fn
                    if fp.is_file():
                        total_size += fp.stat().st_size
                        file_count += 1

            overall["total_size_bytes"] += total_size
            overall["collections"][key] = {
                "cloned": True,
                "file_count": file_count,
                "size_bytes": total_size,
            }

        return overall

    def remove_collection(self, key: str) -> bool:
        """Remove a cloned collection from disk.

        Args:
            key: Collection registry key.

        Returns:
            True if removed, False if not found.
        """
        clone_dir = self._data_dir / key
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
            self._load_index()
            self._index.pop(key, None)
            self._save_index()
            logger.info("Removed collection '%s'", key)
            return True
        return False

    def add_custom_collection(
        self,
        key: str,
        name: str,
        repo_url: str,
        description: str = "",
        default_branch: str = "main",
        categories: list[str] | None = None,
        file_patterns: list[str] | None = None,
    ) -> CollectionMeta:
        """Register a custom community collection.

        Does not clone; call clone_collection() after registering.

        Args:
            key: Unique registry key.
            name: Display name.
            repo_url: Git clone URL.
            description: Collection description.
            default_branch: Default branch name.
            categories: Content categories.
            file_patterns: Glob patterns for wordlist files.

        Returns:
            The registered CollectionMeta.

        Raises:
            ValueError: If key already exists.
        """
        if key in REGISTRY:
            raise ValueError(f"Collection key '{key}' already registered")

        meta = CollectionMeta(
            name=name,
            description=description,
            repo_url=repo_url,
            default_branch=default_branch,
            categories=categories or [],
            file_patterns=file_patterns or ["*.txt"],
        )
        REGISTRY[key] = meta
        logger.info("Registered custom collection '%s' (%s)", key, repo_url)
        return meta

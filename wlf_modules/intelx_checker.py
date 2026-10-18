"""intelx_checker.py - Intelligence X (IntelX) leak/breach search.

Integrates with the IntelX API to search for leaked credentials,
email addresses, and domains in breach databases, pastes, and
darknet sources.

API key is REQUIRED. Save it to:
  - .intelx-key (current dir)
  - ~/.intelx-key (home dir)
  - or pass via --api-key-file

API: https://2.intelx.io
Docs: https://intelx.io/developers

Results depend on the user's API tier and available credits.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)

_INTELX_API = "https://2.intelx.io"
_DEFAULT_KEY_FILE = ".intelx-key"
_REQUEST_DELAY = 1.0
_TIMEOUT = 30

_SEARCH_TYPES: dict[str, int] = {
    "all": 0,
    "leak": 1,
    "paste": 2,
    "darknet": 3,
    "document": 4,
    "whois": 5,
}

_MEDIA_TYPES: dict[int, str] = {
    0: "all",
    1: "paste",
    2: "paste (document)",
    3: "forum/discussion",
    4: "blog/news",
    5: "leak",
    6: "tweet",
    7: "trash",
    8: "legal",
    9: "email",
    10: "screenname",
    11: "photo",
    12: "code",
    13: "document",
    14: "video",
    15: "audio",
    20: "darknet",
    21: "darknet-forum",
    22: "darknet-market",
    23: "darknet-chat",
    24: "whois",
}


# ── API key loader ────────────────────────────────────────────────────────────

def _load_api_key(key_file: Optional[str] = None) -> Optional[str]:
    """Load IntelX API key from file.

    Searches in order:
      1. Explicit path via --api-key-file
      2. .intelx-key in current directory
      3. ~/.intelx-key in home directory
    File format: plain text, first non-empty non-comment line = key.
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
                    logger.info("Loaded IntelX API key from %s", path)
                    return line
    return None


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _api_post(
    endpoint: str,
    data: dict[str, Any],
    api_key: str,
) -> Optional[dict[str, Any]]:
    """POST to IntelX API."""
    import urllib.request
    import urllib.error

    url = f"{_INTELX_API}{endpoint}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "x-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": "WordlistXPL-Forge/2.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            result: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        logger.error("IntelX API error %d: %s", e.code, body[:200])
        return None
    except urllib.error.URLError as e:
        logger.error("IntelX request failed: %s", e)
        return None


def _api_get(
    endpoint: str,
    api_key: str,
    params: Optional[dict[str, str]] = None,
) -> Optional[dict[str, Any]]:
    """GET from IntelX API."""
    import urllib.request
    import urllib.error
    import urllib.parse

    url = f"{_INTELX_API}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "x-key": api_key,
            "User-Agent": "WordlistXPL-Forge/2.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            result: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        logger.error("IntelX API error %d: %s", e.code, body[:200])
        return None
    except urllib.error.URLError as e:
        logger.error("IntelX request failed: %s", e)
        return None


# ── Search result ─────────────────────────────────────────────────────────────

class IntelXResult:
    """Single IntelX search result entry."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.system_id: str = str(raw.get("systemid", ""))
        self.name: str = str(raw.get("name", ""))
        self.date: str = str(raw.get("date", ""))
        self.media_type: int = int(raw.get("media", 0))
        self.media_label: str = _MEDIA_TYPES.get(self.media_type, "unknown")
        self.bucket: str = str(raw.get("bucket", ""))
        self.storageid: str = str(raw.get("storageid", ""))
        self.size: int = int(raw.get("size", 0))

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_id": self.system_id,
            "name": self.name,
            "date": self.date,
            "media_type": self.media_type,
            "media_label": self.media_label,
            "bucket": self.bucket,
            "size": self.size,
        }


class IntelXSearchResult:
    """Aggregated IntelX search results."""

    def __init__(self, query: str) -> None:
        self.query = query
        self.results: list[IntelXResult] = []
        self.total: int = 0
        self.search_id: str = ""

    def add(self, entry: IntelXResult) -> None:
        self.results.append(entry)
        self.total += 1

    def format_text(self) -> str:
        sep = "─" * 60
        lines = [
            sep,
            "  IntelX Search Report",
            sep,
            f"  Query:     {self.query}",
            f"  Results:   {self.total:,}",
            f"  Search ID: {self.search_id[:16]}...",
            sep,
        ]
        if self.results:
            lines.append("  Top results:")
            for r in self.results[:20]:
                lines.append(
                    f"    [{r.media_label:12s}] {r.date[:10]}  "
                    f"{r.name[:40]}  ({r.size:,} bytes)"
                )
            if self.total > 20:
                lines.append(f"    ... ({self.total - 20} more)")
        else:
            lines.append("  No results found.")
        lines.append(sep)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "total": self.total,
            "search_id": self.search_id,
            "results": [r.to_dict() for r in self.results],
        }


# ── Engine ────────────────────────────────────────────────────────────────────

class IntelXChecker:
    """IntelX API search engine."""

    def __init__(
        self,
        api_key_file: Optional[str] = None,
        delay: float = _REQUEST_DELAY,
    ) -> None:
        self._api_key = _load_api_key(api_key_file)
        self._delay = delay
        self._last_request = 0.0

        if not self._api_key:
            logger.error(
                "IntelX API key not found. Save your key to "
                ".intelx-key or pass --api-key-file."
            )

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
        self._last_request = time.time()

    def search(
        self,
        query: str,
        search_type: str = "all",
        max_results: int = 100,
    ) -> IntelXSearchResult:
        """Execute IntelX search."""
        result = IntelXSearchResult(query)

        if not self._api_key:
            logger.error("No API key available.")
            return result

        type_id = _SEARCH_TYPES.get(search_type, 0)

        self._rate_limit()
        search_resp = _api_post(
            "/intelligent/search",
            {
                "term": query,
                "buckets": [],
                "lookuplevel": 0,
                "maxresults": max_results,
                "timeout": 10,
                "datefrom": "",
                "dateto": "",
                "sort": 2,
                "media": type_id,
                "terminate": [],
            },
            self._api_key,
        )

        if not search_resp:
            logger.error("Search request failed.")
            return result

        search_id = search_resp.get("id", "")
        result.search_id = str(search_id)

        if not search_id:
            logger.error("No search ID returned.")
            return result

        time.sleep(2)

        self._rate_limit()
        results_resp = _api_get(
            f"/intelligent/search/result",
            self._api_key,
            params={"id": str(search_id), "limit": str(max_results), "offset": "0"},
        )

        if not results_resp:
            logger.warning("No results returned for search %s", search_id)
            return result

        records = results_resp.get("records", [])
        if isinstance(records, list):
            for record in records:
                if isinstance(record, dict):
                    result.add(IntelXResult(record))

        result.total = int(results_resp.get("count", len(result.results)))
        return result

    def search_batch(
        self,
        queries: list[str],
        search_type: str = "all",
        max_results: int = 100,
    ) -> list[IntelXSearchResult]:
        """Execute multiple searches."""
        results: list[IntelXSearchResult] = []
        for i, query in enumerate(queries):
            logger.info("Searching %d/%d: %s", i + 1, len(queries), query)
            results.append(self.search(query, search_type, max_results))
        return results


# ── CLI handler ───────────────────────────────────────────────────────────────

def handle_intelx(
    args: Any, ctx: dict[str, Any]
) -> Optional[Generator[str, None, None]]:
    """CLI handler for IntelX search."""
    query = getattr(args, "query", None)
    query_file = getattr(args, "query_file", None)
    api_key_file = getattr(args, "api_key_file", None)
    search_type = getattr(args, "type", "all")
    max_results = getattr(args, "max_results", 100) or 100
    fmt = getattr(args, "format", "text")

    queries: list[str] = []
    if query:
        queries.append(query)
    if query_file:
        for line in Path(query_file).read_text(
            encoding="utf-8", errors="ignore"
        ).splitlines():
            q = line.strip()
            if q and not q.startswith("#"):
                queries.append(q)

    if not queries:
        logger.warning("No query provided. Use --query or --query-file.")
        return None

    checker = IntelXChecker(api_key_file=api_key_file)
    if not checker._api_key:
        def _gen_no_key() -> Generator[str, None, None]:
            yield (
                "ERROR: IntelX API key required.\n"
                "Save your key to .intelx-key (one line, plain text) or\n"
                "pass --api-key-file <path>.\n"
                "Get your key at https://intelx.io/account?tab=developer"
            )
        return _gen_no_key()

    results = checker.search_batch(queries, search_type, max_results)

    if fmt == "json":
        def _gen_json() -> Generator[str, None, None]:
            data = [r.to_dict() for r in results]
            yield json.dumps(data, indent=2, ensure_ascii=False)
        return _gen_json()

    if fmt == "csv":
        def _gen_csv() -> Generator[str, None, None]:
            yield "query,system_id,name,date,media_type,media_label,size"
            for sr in results:
                for r in sr.results:
                    yield (
                        f"{sr.query},{r.system_id},{r.name},"
                        f"{r.date},{r.media_type},{r.media_label},{r.size}"
                    )
        return _gen_csv()

    def _gen_text() -> Generator[str, None, None]:
        for sr in results:
            yield sr.format_text()
    return _gen_text()

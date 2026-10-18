"""cluster_engine.py - Password clustering and classification.

Pure-Python implementation of K-means and DBSCAN clustering for
password analysis.  Extracts structural features (length, entropy,
character-class ratios) and groups passwords by similarity.

Also provides a rule-based classifier that labels passwords by type
(numeric, alpha, alphanumeric, complex, passphrase, leet, date, etc.).

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import json
import logging
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Generator, Optional

logger = logging.getLogger(__name__)


# ── Feature extraction ────────────────────────────────────────────────────────

def _entropy(s: str) -> float:
    """Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def _char_class_flags(s: str) -> tuple[bool, bool, bool, bool]:
    """Return (has_lower, has_upper, has_digit, has_special)."""
    lo = up = di = sp = False
    for ch in s:
        if ch.islower():
            lo = True
        elif ch.isupper():
            up = True
        elif ch.isdigit():
            di = True
        else:
            sp = True
    return lo, up, di, sp


def extract_features(pw: str) -> list[float]:
    """Extract a fixed-length numeric feature vector from a password.

    Features (8 dims):
      0: length (normalized to 0-1 via tanh(len/20))
      1: Shannon entropy (normalized via tanh(ent/4))
      2: lowercase ratio
      3: uppercase ratio
      4: digit ratio
      5: special ratio
      6: unique char ratio
      7: number of char classes (0-4, normalized /4)
    """
    n = len(pw) if pw else 1
    lo = sum(1 for c in pw if c.islower()) / n
    up = sum(1 for c in pw if c.isupper()) / n
    di = sum(1 for c in pw if c.isdigit()) / n
    sp = 1.0 - lo - up - di
    ent = _entropy(pw)
    unique = len(set(pw)) / n if pw else 0.0
    has_lo, has_up, has_di, has_sp = _char_class_flags(pw)
    n_classes = sum([has_lo, has_up, has_di, has_sp])
    return [
        math.tanh(len(pw) / 20.0),
        math.tanh(ent / 4.0),
        lo,
        up,
        di,
        sp,
        unique,
        n_classes / 4.0,
    ]


# ── Classification ────────────────────────────────────────────────────────────

def _is_digit_date(s: str) -> bool:
    return s.isdigit()


def _is_date_10(s: str) -> bool:
    return len(s) == 10 and s[4] in "-/" and s[7] in "-/"


_DATE_PATTERNS: dict[int, Callable[[str], bool]] = {
    4: _is_digit_date,
    6: _is_digit_date,
    8: _is_digit_date,
    10: _is_date_10,
}

_LEET_MAP = {"@", "4", "3", "1", "0", "5", "7", "$", "!"}


def classify_password(pw: str) -> str:
    """Classify a password into a structural type label."""
    if not pw:
        return "empty"

    has_lo, has_up, has_di, has_sp = _char_class_flags(pw)
    is_all_digit = all(c.isdigit() for c in pw)
    is_all_alpha = all(c.isalpha() for c in pw)
    is_alnum = all(c.isalnum() for c in pw)
    has_space = " " in pw
    word_count = len(pw.split())

    if is_all_digit:
        checker = _DATE_PATTERNS.get(len(pw))
        if checker and checker(pw):
            return "date-like"
        return "numeric"

    if is_all_alpha:
        if pw.islower():
            return "lower-alpha"
        if pw.isupper():
            return "upper-alpha"
        if pw[0].isupper() and pw[1:].islower():
            return "capitalized"
        return "mixed-alpha"

    if has_space and word_count >= 3:
        return "passphrase"

    leet_score = sum(1 for c in pw if c in _LEET_MAP)
    if leet_score >= len(pw) * 0.3 and has_di and has_sp:
        return "leet"

    if is_alnum:
        if has_lo and has_up and has_di:
            return "mixed-alnum"
        if has_di and (has_lo or has_up):
            return "alnum"
        return "alnum"

    n_classes = sum([has_lo, has_up, has_di, has_sp])
    if n_classes >= 3:
        return "complex"

    if has_sp and not has_di:
        return "alpha-special"

    return "other"


# ── K-means (pure Python) ────────────────────────────────────────────────────

def _euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def _mean_vec(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    dim = len(vectors[0])
    n = len(vectors)
    return [sum(v[d] for v in vectors) / n for d in range(dim)]


def kmeans(
    data: list[list[float]],
    k: int = 5,
    max_iter: int = 50,
    seed: int = 42,
) -> list[int]:
    """K-means clustering. Returns cluster label per data point."""
    if not data or k <= 0:
        return []
    n = len(data)
    k = min(k, n)

    rng = random.Random(seed)
    indices = rng.sample(range(n), k)
    centroids = [list(data[i]) for i in indices]

    labels = [0] * n
    for _it in range(max_iter):
        changed = False
        for i, point in enumerate(data):
            dists = [_euclidean(point, c) for c in centroids]
            new_label = dists.index(min(dists))
            if new_label != labels[i]:
                labels[i] = new_label
                changed = True
        if not changed:
            break
        for c_idx in range(k):
            members = [data[i] for i in range(n) if labels[i] == c_idx]
            if members:
                centroids[c_idx] = _mean_vec(members)

    return labels


# ── DBSCAN (pure Python) ─────────────────────────────────────────────────────

def dbscan(
    data: list[list[float]],
    eps: float = 0.3,
    min_samples: int = 3,
) -> list[int]:
    """DBSCAN clustering. Returns cluster label per point (-1 = noise)."""
    n = len(data)
    labels = [-1] * n
    visited = [False] * n
    cluster_id = 0

    def _region_query(idx: int) -> list[int]:
        return [j for j in range(n) if _euclidean(data[idx], data[j]) <= eps]

    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        neighbors = _region_query(i)
        if len(neighbors) < min_samples:
            continue
        labels[i] = cluster_id
        seed_set = list(neighbors)
        j = 0
        while j < len(seed_set):
            q = seed_set[j]
            if not visited[q]:
                visited[q] = True
                q_neighbors = _region_query(q)
                if len(q_neighbors) >= min_samples:
                    seed_set.extend(q_neighbors)
            if labels[q] == -1:
                labels[q] = cluster_id
            j += 1
        cluster_id += 1

    return labels


# ── Cluster summary ───────────────────────────────────────────────────────────

class ClusterSummary:
    """Summary of one cluster."""

    def __init__(
        self,
        cluster_id: int,
        passwords: list[str],
        features: list[list[float]],
    ) -> None:
        self.cluster_id = cluster_id
        self.size = len(passwords)
        self.passwords = passwords
        self.centroid = _mean_vec(features) if features else []
        types = Counter(classify_password(pw) for pw in passwords)
        self.dominant_type = types.most_common(1)[0][0] if types else "unknown"
        self.type_distribution = dict(types.most_common())
        avg_len = sum(len(pw) for pw in passwords) / max(len(passwords), 1)
        self.avg_length = round(avg_len, 1)
        self.examples = passwords[:5]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "size": self.size,
            "dominant_type": self.dominant_type,
            "avg_length": self.avg_length,
            "type_distribution": self.type_distribution,
            "examples": self.examples,
        }


# ── Engine ────────────────────────────────────────────────────────────────────

class ClusterEngine:
    """Password clustering and classification engine."""

    def __init__(
        self,
        passwords: list[str],
        algorithm: str = "kmeans",
        n_clusters: int = 5,
        eps: float = 0.3,
        min_samples: int = 3,
        seed: int = 42,
    ) -> None:
        self.passwords = passwords
        self.algorithm = algorithm
        self.n_clusters = n_clusters
        self.eps = eps
        self.min_samples = min_samples
        self.seed = seed
        self._features: Optional[list[list[float]]] = None
        self._labels: Optional[list[int]] = None

    def _extract_all(self) -> list[list[float]]:
        if self._features is None:
            self._features = [extract_features(pw) for pw in self.passwords]
        return self._features

    def cluster(self) -> list[int]:
        """Run clustering and return labels."""
        if self._labels is not None:
            return self._labels
        features = self._extract_all()
        if self.algorithm == "dbscan":
            self._labels = dbscan(features, eps=self.eps, min_samples=self.min_samples)
        else:
            self._labels = kmeans(features, k=self.n_clusters, seed=self.seed)
        return self._labels

    def summaries(self) -> list[ClusterSummary]:
        """Return a summary for each cluster."""
        labels = self.cluster()
        features = self._extract_all()
        cluster_ids = sorted(set(labels))
        results: list[ClusterSummary] = []
        for cid in cluster_ids:
            pw_list = [self.passwords[i] for i in range(len(labels)) if labels[i] == cid]
            ft_list = [features[i] for i in range(len(labels)) if labels[i] == cid]
            results.append(ClusterSummary(cid, pw_list, ft_list))
        return results

    def classify_all(self) -> list[tuple[str, str]]:
        """Classify each password without clustering."""
        return [(pw, classify_password(pw)) for pw in self.passwords]

    def format_text(self) -> str:
        """Format cluster results as text report."""
        sums = self.summaries()
        sep = "─" * 60
        lines = [sep, "  Password Cluster Report", sep]
        lines.append(f"  Total passwords: {len(self.passwords):,}")
        lines.append(f"  Algorithm: {self.algorithm}")
        lines.append(f"  Clusters found: {len(sums)}")
        lines.append(sep)
        for s in sums:
            label = f"Cluster {s.cluster_id}" if s.cluster_id >= 0 else "Noise"
            lines.append(f"  {label} ({s.size:,} entries)")
            lines.append(f"    Dominant type: {s.dominant_type}")
            lines.append(f"    Avg length: {s.avg_length}")
            lines.append(f"    Examples: {', '.join(s.examples)}")
            top_types = ", ".join(
                f"{t}={c}" for t, c in list(s.type_distribution.items())[:4]
            )
            lines.append(f"    Types: {top_types}")
            lines.append("")
        lines.append(sep)
        return "\n".join(lines)

    def format_json(self) -> str:
        """Format cluster results as JSON."""
        sums = self.summaries()
        data = {
            "total": len(self.passwords),
            "algorithm": self.algorithm,
            "clusters": [s.to_dict() for s in sums],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)


# ── CLI handler ───────────────────────────────────────────────────────────────

def _load_passwords(path: str, max_load: int = 200_000) -> list[str]:
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


def handle_cluster(
    args: Any, ctx: dict[str, Any]
) -> Optional[Generator[str, None, None]]:
    """CLI handler for password clustering."""
    wordlist = getattr(args, "wordlist", None)
    algorithm = getattr(args, "algorithm", "kmeans")
    n_clusters = getattr(args, "clusters", 5) or 5
    fmt = getattr(args, "format", "text")
    label_only = getattr(args, "label", False)
    eps = float(getattr(args, "eps", 0.3) or 0.3)
    min_samples = int(getattr(args, "min_samples", 3) or 3)
    seed = int(getattr(args, "seed", 42) or 42)

    if not wordlist:
        logger.warning("No wordlist provided. Use positional arg.")
        return None

    passwords = _load_passwords(wordlist)
    if not passwords:
        logger.warning("Wordlist is empty.")
        return None

    if label_only:
        def _gen_labels() -> Generator[str, None, None]:
            for pw in passwords:
                label = classify_password(pw)
                if fmt == "json":
                    yield json.dumps({"password": pw, "type": label}, ensure_ascii=False)
                elif fmt == "csv":
                    yield f"{pw},{label}"
                else:
                    yield f"{label:20s}  {pw}"
        return _gen_labels()

    engine = ClusterEngine(
        passwords=passwords,
        algorithm=algorithm,
        n_clusters=n_clusters,
        eps=eps,
        min_samples=min_samples,
        seed=seed,
    )

    if fmt == "json":
        def _gen_json() -> Generator[str, None, None]:
            yield engine.format_json()
        return _gen_json()

    def _gen_text() -> Generator[str, None, None]:
        yield engine.format_text()
    return _gen_text()

"""password_graph.py - Password graph analysis and graph-based generation.

Models passwords as a graph where:
  - Nodes = unique substrings (character n-grams, whole tokens, segments)
  - Edges = co-occurrence within the same password (from training corpus)

Graph-based generation:
  - Random walk along high-weight edges → new password fragments
  - Shortest-path between two user-provided tokens → hybrid password
  - Community detection → identify structural clusters for targeted expansion

Uses adjacency dict + PageRank to score expansion paths.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Generator, Optional


# ── Graph data structure ──────────────────────────────────────────────────────

@dataclass
class GraphNode:
    label: str
    freq: int = 0
    pagerank: float = 0.0


class PasswordGraph:
    """Directed weighted graph of password substring co-occurrences."""

    def __init__(self, ngram_sizes: tuple[int, ...] = (2, 3, 4)) -> None:
        self.ngram_sizes = ngram_sizes
        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, Counter] = defaultdict(Counter)   # src → Counter(dst → weight)
        self._n_passwords = 0

    def _extract_tokens(self, pw: str) -> list[str]:
        tokens = []
        # character n-grams
        for n in self.ngram_sizes:
            for i in range(len(pw) - n + 1):
                tokens.append(pw[i:i+n])
        # structural segments (alpha/digit/special)
        for m in re.finditer(r"[A-Za-z]+|[0-9]+|[^A-Za-z0-9]+", pw):
            val = m.group()
            if len(val) >= 2:
                tokens.append(val)
        return tokens

    def _ensure_node(self, label: str) -> GraphNode:
        if label not in self.nodes:
            self.nodes[label] = GraphNode(label)
        return self.nodes[label]

    def add_password(self, pw: str, weight: float = 1.0) -> None:
        tokens = self._extract_tokens(pw)
        self._n_passwords += 1
        for tok in tokens:
            node = self._ensure_node(tok)
            node.freq += 1
        # connect all pairs within the password
        unique_toks = list(set(tokens))
        for i, a in enumerate(unique_toks):
            for b in unique_toks[i+1:]:
                self.edges[a][b] += weight
                self.edges[b][a] += weight

    def train(self, passwords: list[str]) -> None:
        for pw in passwords:
            self.add_password(pw)
        self._compute_pagerank()

    def _compute_pagerank(self, damping: float = 0.85, iterations: int = 20) -> None:
        n = max(len(self.nodes), 1)
        pr = {node: 1.0 / n for node in self.nodes}

        for _ in range(iterations):
            new_pr: dict[str, float] = {}
            for node in self.nodes:
                in_score = 0.0
                for src, dsts in self.edges.items():
                    if node in dsts:
                        total_out = sum(dsts.values()) or 1.0
                        in_score += pr.get(src, 0.0) * (dsts[node] / total_out)
                new_pr[node] = (1.0 - damping) / n + damping * in_score
            pr = new_pr

        for label, score in pr.items():
            if label in self.nodes:
                self.nodes[label].pagerank = score

    def top_nodes(self, k: int = 20) -> list[GraphNode]:
        return sorted(self.nodes.values(), key=lambda n: -n.pagerank)[:k]

    def neighbors(self, label: str, k: int = 10) -> list[tuple[str, float]]:
        cnts = self.edges.get(label, Counter())
        total = sum(cnts.values()) or 1.0
        return [(dst, w / total) for dst, w in cnts.most_common(k)]

    def random_walk(
        self,
        start: Optional[str] = None,
        length: int = 3,
        rng: Optional[random.Random] = None,
    ) -> list[str]:
        if rng is None:
            rng = random.Random()
        if not self.nodes:
            return []
        if start is None or start not in self.nodes:
            start = rng.choice(list(self.nodes.keys()))
        path = [start]
        current = start
        for _ in range(length - 1):
            nbrs = self.neighbors(current, k=20)
            if not nbrs:
                break
            labels, weights = zip(*nbrs)
            nxt = rng.choices(labels, weights=weights)[0]
            path.append(nxt)
            current = nxt
        return path

    def path_between(self, src: str, dst: str) -> list[str]:
        """BFS shortest path between two nodes."""
        if src not in self.nodes or dst not in self.nodes:
            return []
        visited = {src}
        queue = [[src]]
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == dst:
                return path
            for nbr, _ in self.neighbors(node):
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(path + [nbr])
        return []


# ── Graph generator engine ────────────────────────────────────────────────────

class PasswordGraphEngine:
    """Generate passwords via random-walk over a co-occurrence graph."""

    def __init__(
        self,
        ngram_sizes: tuple[int, ...] = (2, 3, 4),
        walk_length: int = 4,
        seed: Optional[int] = None,
    ) -> None:
        self.graph = PasswordGraph(ngram_sizes)
        self.walk_length = walk_length
        self.rng = random.Random(seed)
        self._trained = False

    def train(self, corpus: list[str]) -> None:
        self.graph.train(corpus)
        self._trained = True

    def _walk_to_password(self) -> Optional[str]:
        path = self.graph.random_walk(length=self.walk_length, rng=self.rng)
        if not path:
            return None
        # concatenate path segments
        pw = "".join(path)
        return pw if len(pw) >= 4 else None

    def expand(self, token: str, max_candidates: int = 1000) -> Generator[tuple[str, float], None, None]:
        """Expand from a specific token via graph walk."""
        count = 0
        yielded: set[str] = set()
        while count < max_candidates:
            path = self.graph.random_walk(start=token, length=self.walk_length, rng=self.rng)
            pw = "".join(path)
            if pw and pw not in yielded and len(pw) >= 4:
                yielded.add(pw)
                pr = sum(self.graph.nodes[n].pagerank for n in path if n in self.graph.nodes)
                yield (pw, min(pr * 100, 0.9))
                count += 1

    def generate(
        self,
        seed_corpus: Optional[list[str]] = None,
        max_candidates: int = 100_000,
        min_len: int = 4,
        max_len: int = 32,
    ) -> Generator[tuple[str, float], None, None]:
        if seed_corpus:
            self.train(seed_corpus)
        if not self._trained:
            return

        yielded: set[str] = set()
        count = 0
        attempts = 0

        while count < max_candidates:
            attempts += 1
            if attempts > max_candidates * 5:
                break
            pw = self._walk_to_password()
            if pw is None or len(pw) < min_len or len(pw) > max_len:
                continue
            if pw in yielded:
                continue
            yielded.add(pw)
            # score = mean pagerank of nodes in path
            tokens = self.graph._extract_tokens(pw)
            if tokens:
                pr = sum(self.graph.nodes[t].pagerank for t in tokens if t in self.graph.nodes)
                score = min(pr / max(len(tokens), 1) * 500, 0.95)
            else:
                score = 0.4
            yield (pw, score)
            count += 1

    def describe(self) -> str:
        n_nodes = len(self.graph.nodes)
        n_edges = sum(len(v) for v in self.graph.edges.values())
        return (
            f"PasswordGraph: {n_nodes} nodes, {n_edges} edges\n"
            f"  Top nodes: "
            + ", ".join(n.label for n in self.graph.top_nodes(5))
        )

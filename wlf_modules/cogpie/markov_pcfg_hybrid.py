"""
markov_pcfg_hybrid.py - Layer 3: Probabilistic ranking via Markov + PCFG hybrid.

Combines two complementary probabilistic models:
  - Character-level Markov chain (positional n-grams, a la OMEN)
  - Structural PCFG (grammar-based decomposition, a la Weir et al.)

The hybrid score for a candidate c is:

    H(c) = alpha * log P_markov(c) + (1 - alpha) * log P_pcfg(c) + beta * log P_freq(c)

where:
  - P_markov(c): character-level probability from positional Markov model
  - P_pcfg(c): structural probability from grammar decomposition
  - P_freq(c): frequency prior from breach statistics
  - alpha: Markov weight (default 0.4)
  - beta: frequency prior weight (default 0.2)

The frequency prior P_freq uses a Zipf-like distribution fitted to known
breach statistics, following Wang and Wang (2016) and Bonneau (2012).

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict


class _MiniMarkov:
    """Lightweight positional character-level Markov model."""

    def __init__(self, order: int = 3, smoothing: float = 0.01) -> None:
        self.order = order
        self.smoothing = smoothing
        self._ngrams: dict[int, dict[str, Counter]] = defaultdict(
            lambda: defaultdict(Counter)
        )
        self._total_by_pos: dict[int, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._alphabet: set[str] = set()
        self._trained = 0

    def __getstate__(self) -> dict:
        return {
            "order": self.order,
            "smoothing": self.smoothing,
            "ngrams": {k: {ctx: dict(cnt) for ctx, cnt in v.items()} for k, v in self._ngrams.items()},
            "total_by_pos": {k: dict(v) for k, v in self._total_by_pos.items()},
            "alphabet": self._alphabet,
            "trained": self._trained,
        }

    def __setstate__(self, state: dict) -> None:
        self.order = state["order"]
        self.smoothing = state["smoothing"]
        self._ngrams = defaultdict(lambda: defaultdict(Counter))
        for k, v in state["ngrams"].items():
            for ctx, cnt in v.items():
                self._ngrams[k][ctx] = Counter(cnt)
        self._total_by_pos = defaultdict(lambda: defaultdict(int))
        for k, v in state["total_by_pos"].items():
            self._total_by_pos[k].update(v)
        self._alphabet = state["alphabet"]
        self._trained = state["trained"]

    def train(self, password: str) -> None:
        pw = password.strip()
        if len(pw) < 2:
            return
        padded = "\x02" * self.order + pw + "\x03"
        for i in range(len(padded) - self.order):
            ctx = padded[i:i + self.order]
            nxt = padded[i + self.order]
            pos = min(i, 20)
            self._ngrams[pos][ctx][nxt] += 1
            self._total_by_pos[pos][ctx] += 1
        self._alphabet.update(pw)
        self._trained += 1

    def log_prob(self, password: str) -> float:
        if self._trained == 0:
            return -100.0
        padded = "\x02" * self.order + password + "\x03"
        total_log = 0.0
        alpha_size = max(len(self._alphabet), 1)
        for i in range(len(padded) - self.order):
            ctx = padded[i:i + self.order]
            nxt = padded[i + self.order]
            pos = min(i, 20)
            count = self._ngrams[pos][ctx][nxt]
            total = self._total_by_pos[pos].get(ctx, 0)
            prob = (count + self.smoothing) / (total + self.smoothing * alpha_size)
            total_log += math.log(max(prob, 1e-15))
        return total_log


_STRUCT_RE = re.compile(r"([A-Za-z]+)|(\d+)|([^A-Za-z0-9]+)")


class _MiniPCFG:
    """Lightweight PCFG structural model."""

    def __init__(self) -> None:
        self._structure_counts: Counter = Counter()
        self._terminal_counts: dict[str, Counter] = defaultdict(Counter)
        self._total = 0

    @staticmethod
    def _decompose(password: str) -> list[tuple[str, str]]:
        parts = []
        for m in _STRUCT_RE.finditer(password):
            if m.group(1):
                tag = f"L{len(m.group(1))}"
                parts.append((tag, m.group(1).lower()))
            elif m.group(2):
                tag = f"D{len(m.group(2))}"
                parts.append((tag, m.group(2)))
            else:
                tag = f"S{len(m.group(3))}"
                parts.append((tag, m.group(3)))
        return parts

    def train(self, password: str) -> None:
        pw = password.strip()
        if len(pw) < 2:
            return
        parts = self._decompose(pw)
        if not parts:
            return
        structure = " ".join(tag for tag, _ in parts)
        self._structure_counts[structure] += 1
        for tag, terminal in parts:
            self._terminal_counts[tag][terminal] += 1
        self._total += 1

    def log_prob(self, password: str) -> float:
        if self._total == 0:
            return -100.0
        parts = self._decompose(password)
        if not parts:
            return -100.0

        structure = " ".join(tag for tag, _ in parts)
        struct_prob = (self._structure_counts[structure] + 0.01) / (self._total + 0.01 * max(len(self._structure_counts), 1))
        total_log = math.log(max(struct_prob, 1e-15))

        for tag, terminal in parts:
            count = self._terminal_counts[tag][terminal]
            tag_total = sum(self._terminal_counts[tag].values())
            tag_vocab = max(len(self._terminal_counts[tag]), 1)
            prob = (count + 0.01) / (tag_total + 0.01 * tag_vocab)
            total_log += math.log(max(prob, 1e-15))

        return total_log


class HybridRanker:
    """Layer 3: Markov + PCFG hybrid probabilistic ranker.

    Produces a unified log-probability score for each candidate, enabling
    ordered enumeration from most-likely to least-likely.
    """

    def __init__(
        self,
        alpha: float = 0.4,
        beta: float = 0.2,
        markov_order: int = 3,
    ) -> None:
        self.alpha = alpha
        self.beta = beta
        self._markov = _MiniMarkov(order=markov_order)
        self._pcfg = _MiniPCFG()
        self._freq_counts: Counter = Counter()
        self._freq_total: int = 0

    def train(self, password: str) -> None:
        self._markov.train(password)
        self._pcfg.train(password)
        pw = password.strip()
        if pw:
            self._freq_counts[pw.lower()] += 1
            self._freq_total += 1

    def train_from_file(self, filepath: str, max_lines: int = 0) -> int:
        processed = 0
        with open(filepath, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                pw = line.rstrip("\n\r")
                if pw:
                    self.train(pw)
                    processed += 1
                    if max_lines and processed >= max_lines:
                        break
        return processed

    def score(self, candidate: str) -> float:
        """Compute hybrid log-probability H(c) for a candidate.

        Higher (less negative) = more probable = should be tried first.
        """
        log_markov = self._markov.log_prob(candidate)
        log_pcfg = self._pcfg.log_prob(candidate)

        freq = self._freq_counts.get(candidate.lower(), 0)
        vocab = max(len(self._freq_counts), 1)
        log_freq = math.log((freq + 0.001) / (self._freq_total + 0.001 * vocab))

        return (
            self.alpha * log_markov
            + (1.0 - self.alpha - self.beta) * log_pcfg
            + self.beta * log_freq
        )

    def rank(self, candidates: list[str]) -> list[tuple[str, float]]:
        """Rank candidates by hybrid score (descending probability)."""
        scored = [(c, self.score(c)) for c in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    @property
    def trained_count(self) -> int:
        return self._freq_total

"""async_pipeline.py - Async multi-engine generation pipeline with unified scoring.

Runs multiple generation engines concurrently using threads, merges their output
via a priority queue ordered by normalized score, and deduplicates across engines
using a Bloom filter. The interface is a standard synchronous generator so callers
(including _write_output) need no async changes.

Architecture:
  Engine threads → Queue → PriorityMerger → BloomDedup → scored Generator[str]

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import hashlib
import logging
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Optional, Sequence

from wfh_modules.score_normalizer import MultiEngineNormalizer

logger = logging.getLogger(__name__)

_SENTINEL = object()  # poison pill for queues


# ── Bloom filter (space-efficient dedup) ──────────────────────────────────────

class _BloomFilter:
    """Simple double-hash Bloom filter.  ~9.6 bits/element at 1% FP rate."""

    __slots__ = ("_bits", "_size", "_k")

    def __init__(self, capacity: int = 10_000_000, fp_rate: float = 0.01) -> None:
        import math
        m = int(-capacity * math.log(fp_rate) / (math.log(2) ** 2))
        self._size = max(m, 1)
        self._bits = bytearray((self._size + 7) // 8)
        self._k = max(1, int((self._size / capacity) * math.log(2)))

    def _hashes(self, item: str) -> list[int]:
        h1 = int(hashlib.md5(item.encode(), usedforsecurity=False).hexdigest(), 16)  # noqa: S324
        h2 = int(hashlib.sha1(item.encode(), usedforsecurity=False).hexdigest(), 16)  # noqa: S324
        return [(h1 + i * h2) % self._size for i in range(self._k)]

    def add(self, item: str) -> bool:
        """Add item; return True if it was already present (probable duplicate)."""
        bits = self._bits
        sz = self._size
        already = True
        for h in self._hashes(item):
            byte_i, bit_i = divmod(h, 8)
            mask = 1 << bit_i
            if not (bits[byte_i] & mask):
                already = False
                bits[byte_i] |= mask
        return already


# ── Engine slot ───────────────────────────────────────────────────────────────

@dataclass
class EngineSlot:
    name: str
    factory: Callable[[], Generator[Any, None, None]]
    weight: float = 1.0
    limit: int = 0
    raw_score_field: Optional[str] = None  # if engine yields (cand, score) tuples


# ── Pipeline ──────────────────────────────────────────────────────────────────

class AsyncGeneratorPipeline:
    """Run multiple engines in parallel threads, merge by score, dedup with Bloom.

    Usage::

        pipeline = AsyncGeneratorPipeline(slots, global_limit=500_000)
        for candidate in pipeline.run():
            print(candidate)
    """

    def __init__(
        self,
        slots: Sequence[EngineSlot],
        global_limit: int = 0,
        bloom_capacity: int = 5_000_000,
        bloom_fp: float = 0.01,
        queue_size: int = 50_000,
        emit_scores: bool = False,
    ) -> None:
        self.slots = list(slots)
        self.global_limit = global_limit
        self.bloom = _BloomFilter(bloom_capacity, bloom_fp)
        self.queue_size = queue_size
        self.emit_scores = emit_scores
        self._normalizer = MultiEngineNormalizer()
        self._stop = threading.Event()

    def _worker(
        self,
        slot: EngineSlot,
        out_q: "queue.Queue[tuple[float, str]]",
    ) -> None:
        try:
            gen = slot.factory()
            emitted = 0
            for item in gen:
                if self._stop.is_set():
                    break
                if isinstance(item, (tuple, list)) and len(item) == 2:
                    cand, raw = item
                else:
                    cand, raw = str(item), 0.5
                cand = str(cand)
                norm = self._normalizer.score(slot.name, float(raw))
                weighted = norm * slot.weight
                try:
                    out_q.put((-weighted, cand), timeout=2.0)
                except queue.Full:
                    if self._stop.is_set():
                        break
                emitted += 1
                if slot.limit and emitted >= slot.limit:
                    break
        except Exception as exc:
            logger.debug("Engine %s error: %s", slot.name, exc)
        finally:
            try:
                out_q.put((_SENTINEL, slot.name), block=False)  # type: ignore[arg-type]
            except queue.Full:
                pass

    def run(self) -> Generator[str, None, None]:
        """Synchronous generator yielding deduplicated, score-ordered candidates."""
        if not self.slots:
            return

        merge_q: queue.Queue = queue.Queue(maxsize=self.queue_size)
        threads = []
        for slot in self.slots:
            t = threading.Thread(
                target=self._worker,
                args=(slot, merge_q),
                daemon=True,
                name=f"wlf-engine-{slot.name}",
            )
            t.start()
            threads.append(t)

        done_count = 0
        total = len(self.slots)
        emitted = 0

        try:
            while done_count < total:
                try:
                    item = merge_q.get(timeout=0.1)
                except queue.Empty:
                    if all(not t.is_alive() for t in threads):
                        break
                    continue

                neg_score, cand = item
                if neg_score is _SENTINEL or not isinstance(cand, str):
                    done_count += 1
                    continue

                if self.bloom.add(cand):
                    continue  # duplicate

                emitted += 1
                if self.global_limit and emitted > self.global_limit:
                    break

                if self.emit_scores:
                    yield f"{cand}\t{-neg_score:.6f}"
                else:
                    yield cand

        finally:
            self._stop.set()
            for t in threads:
                t.join(timeout=3.0)

    def stop(self) -> None:
        self._stop.set()


# ── Convenience builder ───────────────────────────────────────────────────────

def build_pipeline(
    engine_map: dict[str, dict],
    global_limit: int = 0,
    emit_scores: bool = False,
) -> AsyncGeneratorPipeline:
    """Build a pipeline from a dict of {engine_name: {factory, weight, limit}}.

    engine_map example::

        {
          "markov": {"factory": lambda: markov.generate(), "weight": 0.4, "limit": 50000},
          "pcfg":   {"factory": lambda: pcfg.generate(),   "weight": 0.6, "limit": 80000},
        }
    """
    slots = []
    for name, cfg in engine_map.items():
        factory = cfg.get("factory")
        if not callable(factory):
            logger.warning("Engine %s has no callable factory, skipping", name)
            continue
        slots.append(EngineSlot(
            name=name,
            factory=factory,
            weight=float(cfg.get("weight", 1.0)),
            limit=int(cfg.get("limit", 0)),
        ))
    return AsyncGeneratorPipeline(slots, global_limit=global_limit, emit_scores=emit_scores)

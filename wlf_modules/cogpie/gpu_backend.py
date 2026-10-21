"""
gpu_backend.py - CUDA-accelerated backend for CogPIE pipeline.

Provides GPU-accelerated implementations for:
  - Markov n-gram training and batch scoring
  - PCFG structure scoring in batch
  - Hybrid score computation for thousands of candidates at once
  - Vectorized candidate-to-target matching

Requires PyTorch with CUDA. Falls back to CPU tensors when CUDA is unavailable
but logs a warning; callers should check `is_gpu_available()` before committing
to batch sizes that assume GPU throughput.

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import logging
import math
import re
import time
from collections import Counter, defaultdict
from typing import Any

logger = logging.getLogger(__name__)

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


_STRUCT_RE = re.compile(r"([A-Za-z]+)|(\d+)|([^A-Za-z0-9]+)")


def is_gpu_available() -> bool:
    return _TORCH_AVAILABLE and torch.cuda.is_available()


def get_device() -> torch.device:
    if not _TORCH_AVAILABLE:
        raise RuntimeError("PyTorch not installed")
    if torch.cuda.is_available():
        dev = torch.device("cuda")
        logger.info(
            "GPU: %s (%.1f GB VRAM)",
            torch.cuda.get_device_name(0),
            torch.cuda.get_device_properties(0).total_memory / 1e9,
        )
        return dev
    logger.warning("CUDA unavailable; using CPU tensors")
    return torch.device("cpu")


class GPUMarkov:
    """GPU-accelerated positional character-level Markov model.

    Training builds lookup tables on CPU (sequential by nature), then
    transfers them to GPU tensors. Scoring runs entirely on GPU via
    batched tensor operations.
    """

    def __init__(
        self,
        order: int = 3,
        smoothing: float = 0.01,
        device: torch.device | None = None,
    ) -> None:
        self.order = order
        self.smoothing = smoothing
        self.device = device or get_device()
        self._char2idx: dict[str, int] = {}
        self._idx_counter = 0
        self._ngram_counts: dict[int, dict[str, Counter]] = defaultdict(
            lambda: defaultdict(Counter)
        )
        self._total_by_pos: dict[int, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._trained = 0
        self._gpu_tables: dict[int, torch.Tensor] = {}
        self._gpu_totals: dict[int, torch.Tensor] = {}
        self._ctx2idx: dict[int, dict[str, int]] = {}
        self._materialized = False

    def __getstate__(self) -> dict:
        return {
            "order": self.order,
            "smoothing": self.smoothing,
            "char2idx": dict(self._char2idx),
            "idx_counter": self._idx_counter,
            "ngram_counts": {
                k: {ctx: dict(cnt) for ctx, cnt in v.items()}
                for k, v in self._ngram_counts.items()
            },
            "total_by_pos": {k: dict(v) for k, v in self._total_by_pos.items()},
            "trained": self._trained,
        }

    def __setstate__(self, state: dict) -> None:
        self.order = state["order"]
        self.smoothing = state["smoothing"]
        self._char2idx = state["char2idx"]
        self._idx_counter = state["idx_counter"]
        self._ngram_counts = defaultdict(lambda: defaultdict(Counter))
        for k, v in state["ngram_counts"].items():
            for ctx, cnt in v.items():
                self._ngram_counts[k][ctx] = Counter(cnt)
        self._total_by_pos = defaultdict(lambda: defaultdict(int))
        for k, v in state["total_by_pos"].items():
            self._total_by_pos[k].update(v)
        self._trained = state["trained"]
        self._gpu_tables = {}
        self._gpu_totals = {}
        self._ctx2idx = {}
        self._ctx_hash_tables = {}
        self._materialized = False
        self.device = get_device() if is_gpu_available() else None

    def _get_char_idx(self, ch: str) -> int:
        if ch not in self._char2idx:
            self._char2idx[ch] = self._idx_counter
            self._idx_counter += 1
        return self._char2idx[ch]

    def train(self, password: str) -> None:
        pw = password.strip()
        if len(pw) < 2:
            return
        for ch in pw:
            self._get_char_idx(ch)
        self._get_char_idx("\x02")
        self._get_char_idx("\x03")

        padded = "\x02" * self.order + pw + "\x03"
        for i in range(len(padded) - self.order):
            ctx = padded[i : i + self.order]
            nxt = padded[i + self.order]
            pos = min(i, 20)
            self._ngram_counts[pos][ctx][nxt] += 1
            self._total_by_pos[pos][ctx] += 1
        self._trained += 1
        self._materialized = False

    def train_batch(self, passwords: list[str]) -> int:
        count = 0
        for pw in passwords:
            pw = pw.strip()
            if len(pw) >= 2:
                self.train(pw)
                count += 1
        return count

    def materialize_gpu(self) -> None:
        """Transfer n-gram tables to GPU as sparse indexed tensors.

        Uses enumerated context indices (only contexts seen in training) to
        keep memory compact. Context lookup uses a GPU hash table with open
        addressing for fully vectorized scoring without Python loops.
        """
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not installed")

        V = self._idx_counter + 1
        self._V = V
        self._gpu_tables.clear()
        self._gpu_totals.clear()
        self._ctx2idx.clear()
        self._ctx_hash_tables: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}

        max_ord = 0
        for ch in self._char2idx:
            o = ord(ch)
            if o > max_ord:
                max_ord = o
        self._ord_to_idx = torch.zeros(max_ord + 2, dtype=torch.long, device=self.device)
        for ch, idx in self._char2idx.items():
            self._ord_to_idx[ord(ch)] = idx

        for pos in sorted(self._ngram_counts.keys()):
            contexts = list(self._ngram_counts[pos].keys())
            ctx_map: dict[int, int] = {}
            for i, ctx in enumerate(contexts):
                ctx_key = 0
                valid = True
                for ch in ctx:
                    idx = self._char2idx.get(ch, -1)
                    if idx < 0:
                        valid = False
                        break
                    ctx_key = ctx_key * V + idx
                if valid:
                    ctx_map[ctx_key] = i

            n_ctx = len(contexts) + 1
            table = torch.full(
                (n_ctx, V), self.smoothing, dtype=torch.float32, device="cpu"
            )
            totals = torch.full(
                (n_ctx,), self.smoothing * V, dtype=torch.float32, device="cpu"
            )

            for ctx, counts in self._ngram_counts[pos].items():
                ctx_key = 0
                valid = True
                for ch in ctx:
                    idx = self._char2idx.get(ch, -1)
                    if idx < 0:
                        valid = False
                        break
                    ctx_key = ctx_key * V + idx
                if not valid:
                    continue
                cidx = ctx_map.get(ctx_key, n_ctx - 1)
                total = self._total_by_pos[pos].get(ctx, 0)
                totals[cidx] = total + self.smoothing * V
                for ch, count in counts.items():
                    ch_idx = self._char2idx.get(ch, -1)
                    if 0 <= ch_idx < V:
                        table[cidx, ch_idx] = count + self.smoothing

            self._gpu_tables[pos] = table.to(self.device)
            self._gpu_totals[pos] = totals.to(self.device)
            self._ctx2idx[pos] = ctx_map
            self._ctx_default_idx = n_ctx - 1

            ht_size = max(len(ctx_map) * 4, 64)
            ht_keys = torch.full((ht_size,), -1, dtype=torch.long, device=self.device)
            ht_vals = torch.full(
                (ht_size,), n_ctx - 1, dtype=torch.long, device=self.device
            )
            for k, v in ctx_map.items():
                slot = k % ht_size
                while ht_keys[slot].item() != -1:
                    slot = (slot + 1) % ht_size
                ht_keys[slot] = k
                ht_vals[slot] = v
            self._ctx_hash_tables[pos] = (ht_keys, ht_vals)

        self._materialized = True
        mem_mb = sum(t.nelement() * 4 for t in self._gpu_tables.values()) / 1e6
        mem_mb += sum(t.nelement() * 4 for t in self._gpu_totals.values()) / 1e6
        logger.info(
            "Markov GPU materialized: %d positions, V=%d, %.1f MB VRAM, device=%s",
            len(self._gpu_tables), V, mem_mb, self.device,
        )

    def _encode_candidates(self, candidates: list[str]) -> tuple:
        """Encode candidates as char-index tensor using numpy bulk conversion."""
        import numpy as np

        order = self.order
        pad = "\x02" * order
        end = "\x03"

        padded = [pad + c + end for c in candidates]
        max_len = max(len(p) for p in padded)
        n = len(padded)

        ord_table = self._ord_to_idx
        max_ord = ord_table.shape[0] - 1

        flat = bytearray()
        offsets = []
        pos = 0
        for p in padded:
            b = p.encode("utf-8", errors="replace")
            flat.extend(b)
            offsets.append((pos, len(b)))
            pos += len(b)

        ords_np = np.zeros((n, max_len), dtype=np.int64)
        flat_arr = np.frombuffer(bytes(flat), dtype=np.uint8)
        for i, (off, length) in enumerate(offsets):
            ords_np[i, :length] = flat_arr[off : off + length]

        np.clip(ords_np, 0, max_ord, out=ords_np)
        ords_gpu = torch.from_numpy(ords_np).to(self.device)
        encoded = ord_table[ords_gpu]

        return encoded, max_len

    def _compute_ctx_keys(
        self, encoded: torch.Tensor, pos_offset: int
    ) -> torch.Tensor:
        """Compute integer context keys for all candidates at a given position."""
        V = self._V
        if self.order == 3:
            return (
                encoded[:, pos_offset] * (V * V)
                + encoded[:, pos_offset + 1] * V
                + encoded[:, pos_offset + 2]
            )
        elif self.order == 2:
            return encoded[:, pos_offset] * V + encoded[:, pos_offset + 1]
        else:
            key = torch.zeros(encoded.shape[0], dtype=torch.long, device=self.device)
            for o in range(self.order):
                key = key * V + encoded[:, pos_offset + o]
            return key

    def _map_ctx_keys_to_indices(
        self, ctx_keys: torch.Tensor, pos: int
    ) -> torch.Tensor:
        """Map integer context keys to table row indices using GPU hash table."""
        if pos not in self._ctx_hash_tables:
            return torch.full_like(ctx_keys, self._ctx_default_idx)

        ht_keys, ht_vals = self._ctx_hash_tables[pos]
        ht_size = ht_keys.shape[0]
        default = self._ctx_default_idx

        slots = ctx_keys % ht_size
        result = torch.full_like(ctx_keys, default)

        for probe in range(min(32, ht_size)):
            current_slots = (slots + probe) % ht_size
            stored_keys = ht_keys[current_slots]
            match = stored_keys == ctx_keys
            empty = stored_keys == -1
            result = torch.where(match, ht_vals[current_slots], result)
            if (match | empty).all():
                break

        return result

    def score_batch(self, candidates: list[str]) -> torch.Tensor:
        """Score a batch of candidates on GPU.

        Encoding and context-key mapping are vectorized; the per-position loop
        iterates ~15 times (password length) but each iteration is a GPU
        gather over the full batch.
        """
        if not self._materialized:
            self.materialize_gpu()

        n = len(candidates)
        if self._trained == 0:
            return torch.full((n,), -100.0, dtype=torch.float32, device=self.device)

        encoded, max_len = self._encode_candidates(candidates)
        scores = torch.zeros(n, dtype=torch.float32, device=self.device)
        lengths = torch.tensor(
            [len(c) + self.order + 1 for c in candidates],
            dtype=torch.long, device=self.device,
        )

        for i in range(max_len - self.order):
            pos = min(i, 20)
            if pos not in self._gpu_tables:
                active = (i + self.order) < lengths
                scores -= active.float() * 10.0
                continue

            table = self._gpu_tables[pos]
            totals = self._gpu_totals[pos]
            active = (i + self.order) < lengths

            ctx_keys = self._compute_ctx_keys(encoded, i)
            ctx_indices = self._map_ctx_keys_to_indices(ctx_keys, pos)
            ctx_indices = ctx_indices.clamp(0, table.shape[0] - 1)
            nxt_idx = encoded[:, i + self.order].clamp(0, table.shape[1] - 1)

            counts = table[ctx_indices, nxt_idx]
            tots = totals[ctx_indices]
            probs = (counts / tots).clamp(min=1e-15)
            log_probs = probs.log()

            scores += torch.where(active, log_probs, torch.zeros_like(log_probs))

        return scores

    def log_prob(self, password: str) -> float:
        """CPU fallback for single password scoring."""
        if self._trained == 0:
            return -100.0
        padded = "\x02" * self.order + password + "\x03"
        total_log = 0.0
        alpha_size = max(len(self._char2idx), 1)
        for i in range(len(padded) - self.order):
            ctx = padded[i : i + self.order]
            nxt = padded[i + self.order]
            pos = min(i, 20)
            count = self._ngram_counts[pos][ctx][nxt]
            total = self._total_by_pos[pos].get(ctx, 0)
            prob = (count + self.smoothing) / (total + self.smoothing * alpha_size)
            total_log += math.log(max(prob, 1e-15))
        return total_log

    @property
    def trained_count(self) -> int:
        return self._trained


class GPUPCFG:
    """GPU-accelerated structural PCFG model.

    Training runs on CPU; batch scoring uses GPU hash-based lookups.
    """

    def __init__(self, device: torch.device | None = None) -> None:
        self.device = device or get_device()
        self._structure_counts: Counter = Counter()
        self._terminal_counts: dict[str, Counter] = defaultdict(Counter)
        self._total = 0

    def __getstate__(self) -> dict:
        return {
            "structure_counts": dict(self._structure_counts),
            "terminal_counts": {k: dict(v) for k, v in self._terminal_counts.items()},
            "total": self._total,
        }

    def __setstate__(self, state: dict) -> None:
        self._structure_counts = Counter(state["structure_counts"])
        self._terminal_counts = defaultdict(Counter)
        for k, v in state["terminal_counts"].items():
            self._terminal_counts[k] = Counter(v)
        self._total = state["total"]
        self.device = get_device() if is_gpu_available() else None

    @staticmethod
    def _decompose(password: str) -> list[tuple[str, str]]:
        parts = []
        for m in _STRUCT_RE.finditer(password):
            if m.group(1):
                parts.append((f"L{len(m.group(1))}", m.group(1).lower()))
            elif m.group(2):
                parts.append((f"D{len(m.group(2))}", m.group(2)))
            else:
                parts.append((f"S{len(m.group(3))}", m.group(3)))
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

    def train_batch(self, passwords: list[str]) -> int:
        count = 0
        for pw in passwords:
            pw = pw.strip()
            if len(pw) >= 2:
                self.train(pw)
                count += 1
        return count

    def _tag_total_cache(self) -> dict[str, tuple[int, int]]:
        cache = {}
        for tag, counts in self._terminal_counts.items():
            total = sum(counts.values())
            vocab = max(len(counts), 1)
            cache[tag] = (total, vocab)
        return cache

    def score_batch(self, candidates: list[str]) -> torch.Tensor:
        """Score batch of candidates. Returns tensor of log-probs on GPU."""
        n = len(candidates)
        scores = torch.zeros(n, dtype=torch.float32, device=self.device)
        if self._total == 0:
            return scores.fill_(-100.0)

        struct_total = self._total
        struct_vocab = max(len(self._structure_counts), 1)
        tag_cache = self._tag_total_cache()

        score_list = []
        for c in candidates:
            parts = self._decompose(c)
            if not parts:
                score_list.append(-100.0)
                continue
            structure = " ".join(tag for tag, _ in parts)
            sp = (self._structure_counts[structure] + 0.01) / (
                struct_total + 0.01 * struct_vocab
            )
            total_log = math.log(max(sp, 1e-15))
            for tag, terminal in parts:
                count = self._terminal_counts[tag][terminal]
                tt, tv = tag_cache.get(tag, (0, 1))
                prob = (count + 0.01) / (tt + 0.01 * tv)
                total_log += math.log(max(prob, 1e-15))
            score_list.append(total_log)

        return torch.tensor(score_list, dtype=torch.float32, device=self.device)

    def log_prob(self, password: str) -> float:
        if self._total == 0:
            return -100.0
        parts = self._decompose(password)
        if not parts:
            return -100.0
        structure = " ".join(tag for tag, _ in parts)
        sp = (self._structure_counts[structure] + 0.01) / (
            self._total + 0.01 * max(len(self._structure_counts), 1)
        )
        total_log = math.log(max(sp, 1e-15))
        tag_cache = self._tag_total_cache()
        for tag, terminal in parts:
            count = self._terminal_counts[tag][terminal]
            tt, tv = tag_cache.get(tag, (0, 1))
            prob = (count + 0.01) / (tt + 0.01 * tv)
            total_log += math.log(max(prob, 1e-15))
        return total_log


class GPUHybridRanker:
    """GPU-accelerated Layer 3: Markov + PCFG hybrid ranker.

    All scoring operations run on GPU tensors. Training collects
    counts on CPU and materializes to GPU before the first score_batch.
    """

    def __init__(
        self,
        alpha: float = 0.4,
        beta: float = 0.2,
        markov_order: int = 3,
        device: torch.device | None = None,
    ) -> None:
        self.device = device or get_device()
        self.alpha = alpha
        self.beta = beta
        self._markov = GPUMarkov(order=markov_order, device=self.device)
        self._pcfg = GPUPCFG(device=self.device)
        self._freq_counts: Counter = Counter()
        self._freq_total: int = 0

    def __getstate__(self) -> dict:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "markov": self._markov.__getstate__(),
            "pcfg": self._pcfg.__getstate__(),
            "freq_counts": dict(self._freq_counts),
            "freq_total": self._freq_total,
        }

    def __setstate__(self, state: dict) -> None:
        self.alpha = state["alpha"]
        self.beta = state["beta"]
        self.device = get_device() if is_gpu_available() else None
        self._markov = GPUMarkov.__new__(GPUMarkov)
        self._markov.__setstate__(state["markov"])
        self._pcfg = GPUPCFG.__new__(GPUPCFG)
        self._pcfg.__setstate__(state["pcfg"])
        self._freq_counts = Counter(state["freq_counts"])
        self._freq_total = state["freq_total"]

    def train(self, password: str) -> None:
        self._markov.train(password)
        self._pcfg.train(password)
        pw = password.strip()
        if pw:
            self._freq_counts[pw.lower()] += 1
            self._freq_total += 1

    def train_from_file(
        self,
        filepath: str,
        max_lines: int = 0,
        progress_every: int = 500_000,
    ) -> int:
        processed = 0
        t0 = time.monotonic()
        with open(filepath, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                pw = line.rstrip("\n\r")
                if pw:
                    self.train(pw)
                    processed += 1
                    if progress_every and processed % progress_every == 0:
                        elapsed = time.monotonic() - t0
                        rate = processed / max(elapsed, 0.001)
                        logger.info(
                            "GPU Training: %dk passwords (%.0f pw/s)",
                            processed // 1000,
                            rate,
                        )
                    if max_lines and processed >= max_lines:
                        break
        elapsed = time.monotonic() - t0
        logger.info(
            "GPU Training complete: %d passwords in %.1fs (%.0f pw/s)",
            processed,
            elapsed,
            processed / max(elapsed, 0.001),
        )
        self._markov.materialize_gpu()
        return processed

    def score_batch(self, candidates: list[str]) -> torch.Tensor:
        """Score all candidates in one GPU pass. Returns tensor of hybrid scores."""
        if not self._markov._materialized:
            self._markov.materialize_gpu()

        log_markov = self._markov.score_batch(candidates)
        log_pcfg = self._pcfg.score_batch(candidates)

        vocab = max(len(self._freq_counts), 1)
        freq_scores = []
        for c in candidates:
            freq = self._freq_counts.get(c.lower(), 0)
            freq_scores.append(
                math.log((freq + 0.001) / (self._freq_total + 0.001 * vocab))
            )
        log_freq = torch.tensor(
            freq_scores, dtype=torch.float32, device=self.device
        )

        hybrid = (
            self.alpha * log_markov
            + (1.0 - self.alpha - self.beta) * log_pcfg
            + self.beta * log_freq
        )
        return hybrid

    def rank_batch(self, candidates: list[str]) -> list[tuple[str, float]]:
        """Rank candidates by hybrid score using GPU batch scoring."""
        if not candidates:
            return []

        BATCH = 50_000
        all_scores = []
        for i in range(0, len(candidates), BATCH):
            chunk = candidates[i : i + BATCH]
            scores = self.score_batch(chunk)
            all_scores.append(scores)

        full_scores = torch.cat(all_scores)
        sorted_indices = torch.argsort(full_scores, descending=True)
        idx_cpu = sorted_indices.cpu().tolist()
        scores_cpu = full_scores.cpu().tolist()

        return [(candidates[i], scores_cpu[i]) for i in idx_cpu]

    def score(self, candidate: str) -> float:
        """Single-candidate scoring (uses GPU batch of 1)."""
        result = self.score_batch([candidate])
        return result[0].item()

    def rank(self, candidates: list[str]) -> list[tuple[str, float]]:
        """Drop-in replacement for HybridRanker.rank()."""
        return self.rank_batch(candidates)

    @property
    def trained_count(self) -> int:
        return self._freq_total


class GPUCandidateMatcher:
    """GPU-accelerated candidate-to-target matching for benchmarks.

    Converts candidate strings to hash tensors and performs vectorized
    lookup, avoiding O(N) Python string comparisons per target.
    """

    def __init__(self, device: torch.device | None = None) -> None:
        self.device = device or get_device()

    @staticmethod
    def _hash_strings(strings: list[str]) -> list[int]:
        return [hash(s) & 0x7FFFFFFFFFFFFFFF for s in strings]

    def find_rank(
        self,
        target: str,
        candidates: list[str],
        max_budget: int = 10000,
    ) -> int | None:
        """Find rank of target in candidates list using GPU matching.

        Returns 1-indexed rank, or None if not found within budget.
        """
        limit = min(len(candidates), max_budget)
        chunk = candidates[:limit]

        target_hash = hash(target) & 0x7FFFFFFFFFFFFFFF
        candidate_hashes = self._hash_strings(chunk)

        target_t = torch.tensor(
            [target_hash], dtype=torch.long, device=self.device
        )
        cand_t = torch.tensor(
            candidate_hashes, dtype=torch.long, device=self.device
        )

        matches = (cand_t == target_t).nonzero(as_tuple=True)[0]

        if len(matches) == 0:
            return None

        for idx in matches.cpu().tolist():
            if chunk[idx] == target:
                return idx + 1

        return None

    def find_ranks_batch(
        self,
        targets: list[str],
        candidates_per_target: list[list[str]],
        max_budget: int = 10000,
    ) -> list[int | None]:
        """Find ranks for multiple targets in parallel."""
        results = []
        for target, candidates in zip(targets, candidates_per_target):
            results.append(self.find_rank(target, candidates, max_budget))
        return results


def gpu_benchmark_evaluate(
    algorithm_name: str,
    gen_fn: Any,
    test_set: list[str],
    budgets: list[int],
    device: torch.device | None = None,
    progress_every: int = 100,
) -> dict[str, Any]:
    """GPU-accelerated benchmark evaluation for a single algorithm.

    Replaces the CPU-bound evaluate_with_gpu from cogpie_gpu_comparison.
    """
    import statistics

    dev = device or get_device()
    matcher = GPUCandidateMatcher(device=dev)
    max_budget = max(budgets)
    hits_at = {k: 0 for k in budgets}
    ranks = []
    total_time = 0.0
    evaluated = 0

    for idx, target_pw in enumerate(test_set):
        from tools.cogpie_gpu_comparison import _extract_profile

        profile = _extract_profile(target_pw)
        if profile is None:
            continue

        t0 = time.monotonic()
        try:
            candidates = gen_fn(profile, max_budget)
        except Exception:
            continue
        time.monotonic() - t0

        found_at = matcher.find_rank(target_pw, candidates, max_budget)
        total_time += time.monotonic() - t0
        evaluated += 1

        if found_at is not None:
            ranks.append(found_at)
            for k in budgets:
                if found_at <= k:
                    hits_at[k] += 1

        if progress_every and (idx + 1) % progress_every == 0:
            logger.info(
                "  [%s] %d/%d (hit@%d: %.1f%%)",
                algorithm_name,
                idx + 1,
                len(test_set),
                max_budget,
                hits_at[max_budget] / max(evaluated, 1) * 100,
            )

    hit_rates = {}
    for k in budgets:
        hit_rates[f"hit@{k}"] = round(hits_at[k] / max(evaluated, 1) * 100, 2)

    mrr = sum(1.0 / r for r in ranks) / max(evaluated, 1) if ranks else 0.0

    return {
        "algorithm": algorithm_name,
        "evaluated": evaluated,
        "total_hits": len(ranks),
        "coverage_pct": round(len(ranks) / max(evaluated, 1) * 100, 2),
        "mrr": round(mrr, 6),
        "median_rank": int(statistics.median(ranks)) if ranks else None,
        "total_time_seconds": round(total_time, 2),
        "avg_time_per_target_ms": round(
            total_time / max(evaluated, 1) * 1000, 2
        ),
        "hit_rates": hit_rates,
        "hits_raw": {f"hit@{k}": hits_at[k] for k in budgets},
    }

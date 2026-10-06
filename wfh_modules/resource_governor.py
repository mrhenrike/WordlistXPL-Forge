"""resource_governor.py - Soft resource budgets to keep generation from freezing the host.

Polls available RAM (and optional VRAM hints), enforces candidate/chunk limits,
and signals graceful stop without killing the process abruptly.

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Exit-ish reason codes for callers
STOP_OK = "ok"
STOP_LIMIT = "limit"
STOP_TIMEOUT = "timeout"
STOP_RAM = "ram"
STOP_VRAM = "vram"
STOP_SHUTDOWN = "shutdown"
STOP_DISK = "disk"


@dataclass
class GovernorConfig:
    ram_budget_pct: float = 50.0       # stop when available RAM < (100-pct)% of total… see below
    min_available_ram_mb: int = 512    # hard floor of free RAM
    vram_budget_mb: int = 4096
    max_candidates: int = 0            # 0 = unlimited (caller may set safe default)
    safe_default_max: int = 5_000_000  # applied when nuclear/unlimited without explicit limit
    chunk_lines: int = 0               # rotate output every N lines (0 = off)
    chunk_bytes: int = 0               # rotate output every N bytes (0 = off)
    poll_every: int = 10_000           # check RAM every N emitted candidates
    timeout_secs: float = 0.0
    enforce_safe_default: bool = False # if True and max_candidates==0 → use safe_default_max


@dataclass
class GovernorState:
    emitted: int = 0
    bytes_written: int = 0
    chunk_index: int = 0
    stop_reason: str = STOP_OK
    started: float = field(default_factory=time.time)
    last_ram_mb: int = 0


class ResourceGovernor:
    """Stateful soft governor for generation loops."""

    def __init__(self, cfg: Optional[GovernorConfig] = None) -> None:
        self.cfg = cfg or GovernorConfig()
        self.state = GovernorState()
        if self.cfg.enforce_safe_default and not self.cfg.max_candidates:
            self.cfg.max_candidates = self.cfg.safe_default_max

    @staticmethod
    def ram_available_mb() -> int:
        try:
            import psutil
            return int(psutil.virtual_memory().available / (1024 * 1024))
        except Exception:
            pass
        try:
            with open("/proc/meminfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("MemAvailable:"):
                        return int(line.split()[1]) // 1024
        except Exception:
            pass
        return 4096  # optimistic fallback

    @staticmethod
    def ram_total_mb() -> int:
        try:
            import psutil
            return int(psutil.virtual_memory().total / (1024 * 1024))
        except Exception:
            pass
        try:
            with open("/proc/meminfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) // 1024
        except Exception:
            pass
        return 8192

    def vram_free_mb(self) -> Optional[int]:
        try:
            import subprocess
            out = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.free",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
                timeout=3,
            )
            vals = [int(x.strip()) for x in out.strip().splitlines() if x.strip().isdigit()]
            return min(vals) if vals else None
        except Exception:
            return None

    def gpu_batch_size(self, default: int = 65536) -> int:
        """Suggest a batch size capped by VRAM budget."""
        free = self.vram_free_mb()
        budget = self.cfg.vram_budget_mb
        if free is not None:
            usable = max(256, min(free, budget))
            # rough: ~64 bytes/candidate on device → scale
            return max(1024, min(default, usable * 256))
        return min(default, 16384)

    def check(self, shutdown_flag: bool = False) -> str:
        """Return STOP_* reason if generation should halt, else STOP_OK."""
        st = self.state
        cfg = self.cfg

        if shutdown_flag:
            st.stop_reason = STOP_SHUTDOWN
            return STOP_SHUTDOWN

        if cfg.max_candidates and st.emitted >= cfg.max_candidates:
            st.stop_reason = STOP_LIMIT
            return STOP_LIMIT

        if cfg.timeout_secs and (time.time() - st.started) > cfg.timeout_secs:
            st.stop_reason = STOP_TIMEOUT
            return STOP_TIMEOUT

        # Poll after progress has started (emitted==0 always matches `% N == 0`
        # and would false-trip on busy hosts before any output).
        poll_every = max(cfg.poll_every, 1)
        if st.emitted > 0 and st.emitted % poll_every == 0:
            avail = self.ram_available_mb()
            st.last_ram_mb = avail
            total = max(self.ram_total_mb(), 1)
            # Stop when available RAM is below max(min_available, total * (100-budget_pct)/100)
            floor = max(
                cfg.min_available_ram_mb,
                int(total * (100.0 - cfg.ram_budget_pct) / 100.0),
            )
            if avail < floor:
                logger.warning(
                    "RAM guard: available=%dMB floor=%dMB — stopping gracefully",
                    avail,
                    floor,
                )
                st.stop_reason = STOP_RAM
                return STOP_RAM

            free_v = self.vram_free_mb()
            if free_v is not None and free_v < max(128, cfg.vram_budget_mb // 16):
                # only warn-level for VRAM during CPU gen; callers using GPU should stop
                pass

        return STOP_OK

    def note_emit(self, n: int = 1, nbytes: int = 0) -> None:
        self.state.emitted += n
        self.state.bytes_written += nbytes

    def need_chunk_rotate(self) -> bool:
        cfg = self.cfg
        if cfg.chunk_lines and self.state.emitted > 0 and self.state.emitted % cfg.chunk_lines == 0:
            return True
        if cfg.chunk_bytes and self.state.bytes_written > 0:
            # rotate when crossing chunk boundaries
            prev = self.state.bytes_written - 1
            if self.state.bytes_written // cfg.chunk_bytes > max(prev, 0) // cfg.chunk_bytes:
                return True
        return False

    def next_chunk_path(self, base: str) -> str:
        self.state.chunk_index += 1
        root, ext = os.path.splitext(base)
        return f"{root}.part{self.state.chunk_index:03d}{ext or '.lst'}"


def governor_from_ctx(ctx: dict) -> ResourceGovernor:
    """Build a ResourceGovernor from wlf _GLOBAL_CTX."""
    cfg = GovernorConfig(
        ram_budget_pct=float(ctx.get("ram_budget_pct", 50) or 50),
        min_available_ram_mb=int(ctx.get("min_available_ram_mb", 512) or 512),
        vram_budget_mb=int(ctx.get("vram_budget_mb", 4096) or 4096),
        max_candidates=int(ctx.get("limit", 0) or 0),
        chunk_lines=int(ctx.get("chunk_lines", 0) or 0),
        chunk_bytes=int(ctx.get("chunk_bytes", 0) or 0),
        poll_every=int(ctx.get("gov_poll_every", 10_000) or 10_000),
        timeout_secs=float(ctx.get("timeout", 0) or 0),
        enforce_safe_default=bool(ctx.get("enforce_safe_default", False)),
        safe_default_max=int(ctx.get("safe_default_max", 5_000_000) or 5_000_000),
    )
    return ResourceGovernor(cfg)

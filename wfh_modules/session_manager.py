"""session_manager.py - Generation session checkpoint and resume.

Serialises the complete state of an in-progress generation run:
  - ResourceGovernor counters (emitted, bytes_written, chunk_index)
  - BanditRouter arm statistics
  - PBMP/strategy weights
  - Engine-specific state checkpoints (e.g. Markov heap position)
  - Pipeline configuration

Sessions are stored as JSON in ~/.wlf/sessions/ by default.
Each session gets a unique ID (timestamp + short hash of config).

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_SESSION_DIR = Path.home() / ".wlf" / "sessions"


@dataclass
class SessionState:
    session_id: str
    created_at: float
    updated_at: float
    label: str = ""
    emitted: int = 0
    bytes_written: int = 0
    chunk_index: int = 0
    engine_states: dict[str, Any] = field(default_factory=dict)
    bandit_stats: dict[str, Any] = field(default_factory=dict)
    pbmp_weights: dict[str, float] = field(default_factory=dict)
    pipeline_config: dict[str, Any] = field(default_factory=dict)
    global_ctx_snapshot: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Save, load, list and delete generation sessions."""

    def __init__(self, session_dir: Optional[Path] = None) -> None:
        self.session_dir = Path(session_dir or _DEFAULT_SESSION_DIR)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    # ── ID helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def new_id(label: str = "") -> str:
        ts = int(time.time())
        h = hashlib.sha1(f"{ts}{label}".encode(), usedforsecurity=False).hexdigest()[:6]  # noqa: S324
        return f"{ts}-{h}"

    def _path(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.json"

    # ── Save ────────────────────────────────────────────────────────────────

    def save(self, state: SessionState) -> Path:
        state.updated_at = time.time()
        p = self._path(state.session_id)
        with p.open("w", encoding="utf-8") as fh:
            json.dump(asdict(state), fh, indent=2, default=str)
        logger.debug("Session saved: %s", p)
        return p

    def save_from_parts(
        self,
        session_id: str,
        label: str = "",
        emitted: int = 0,
        bytes_written: int = 0,
        chunk_index: int = 0,
        engine_states: Optional[dict] = None,
        bandit_stats: Optional[dict] = None,
        pbmp_weights: Optional[dict] = None,
        pipeline_config: Optional[dict] = None,
        global_ctx: Optional[dict] = None,
    ) -> Path:
        existing = self._try_load(session_id)
        now = time.time()
        state = existing or SessionState(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            label=label,
        )
        state.emitted = emitted
        state.bytes_written = bytes_written
        state.chunk_index = chunk_index
        if engine_states is not None:
            state.engine_states = engine_states
        if bandit_stats is not None:
            state.bandit_stats = bandit_stats
        if pbmp_weights is not None:
            state.pbmp_weights = pbmp_weights
        if pipeline_config is not None:
            state.pipeline_config = pipeline_config
        if global_ctx is not None:
            safe = {k: v for k, v in global_ctx.items() if isinstance(v, (str, int, float, bool, type(None)))}
            state.global_ctx_snapshot = safe
        return self.save(state)

    # ── Load ────────────────────────────────────────────────────────────────

    def load(self, session_id: str) -> SessionState:
        p = self._path(session_id)
        if not p.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        with p.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return SessionState(**data)

    def _try_load(self, session_id: str) -> Optional[SessionState]:
        try:
            return self.load(session_id)
        except (FileNotFoundError, TypeError, json.JSONDecodeError):
            return None

    # ── List ────────────────────────────────────────────────────────────────

    def list_sessions(self) -> list[SessionState]:
        sessions = []
        for p in sorted(self.session_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with p.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                sessions.append(SessionState(**data))
            except Exception:
                pass
        return sessions

    def describe_list(self) -> str:
        sessions = self.list_sessions()
        if not sessions:
            return "No sessions found."
        lines = ["Sessions:"]
        for s in sessions:
            age = int(time.time() - s.updated_at)
            lines.append(
                f"  {s.session_id}  emitted={s.emitted:,}  "
                f"label={s.label!r}  age={age}s"
            )
        return "\n".join(lines)

    # ── Delete ──────────────────────────────────────────────────────────────

    def delete(self, session_id: str) -> bool:
        p = self._path(session_id)
        if p.exists():
            p.unlink()
            return True
        return False

    # ── Resume helper ────────────────────────────────────────────────────────

    def resume_ctx(self, session_id: str) -> dict:
        """Return a dict that can be merged into _GLOBAL_CTX to resume a session."""
        state = self.load(session_id)
        ctx = dict(state.global_ctx_snapshot)
        ctx["_resume_emitted"] = state.emitted
        ctx["_resume_chunk_index"] = state.chunk_index
        ctx["_resume_engine_states"] = state.engine_states
        ctx["_resume_bandit_stats"] = state.bandit_stats
        ctx["_resume_pbmp_weights"] = state.pbmp_weights
        return ctx


# ── Module-level singleton ─────────────────────────────────────────────────────

_manager: Optional[SessionManager] = None


def get_manager(session_dir: Optional[Path] = None) -> SessionManager:
    global _manager
    if _manager is None or session_dir is not None:
        _manager = SessionManager(session_dir)
    return _manager

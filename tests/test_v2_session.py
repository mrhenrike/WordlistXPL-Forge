"""Fase 5 — SessionManager and checkpoint tests."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.session_manager import SessionManager, SessionState, get_manager


class TestSessionManager:
    def test_get_manager_singleton(self) -> None:
        m1 = get_manager()
        m2 = get_manager()
        assert m1 is m2

    def test_new_id_format(self) -> None:
        sid = SessionManager.new_id(label="test")
        assert isinstance(sid, str)
        assert "-" in sid
        assert len(sid) > 5

    def test_new_id_unique(self) -> None:
        ids = set()
        for _ in range(50):
            ids.add(SessionManager.new_id())
            time.sleep(0.001)
        assert len(ids) == 50

    def test_save_and_load(self, tmp_path: Path) -> None:
        mgr = SessionManager(session_dir=tmp_path)
        sid = SessionManager.new_id(label="save-test")
        state = SessionState(
            session_id=sid,
            created_at=time.time(),
            updated_at=time.time(),
            label="save-test",
            emitted=500,
            bytes_written=7000,
        )
        mgr.save(state)
        loaded = mgr.load(sid)
        assert loaded.emitted == 500
        assert loaded.session_id == sid

    def test_save_from_parts(self, tmp_path: Path) -> None:
        mgr = SessionManager(session_dir=tmp_path)
        sid = SessionManager.new_id(label="parts")
        mgr.save_from_parts(
            session_id=sid,
            emitted=1000,
            bytes_written=14000,
            chunk_index=1,
            global_ctx={"command": "profile"},
        )
        loaded = mgr.load(sid)
        assert loaded.emitted == 1000

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        mgr = SessionManager(session_dir=tmp_path)
        with pytest.raises(Exception):
            mgr.load("does-not-exist")

    def test_list_sessions(self, tmp_path: Path) -> None:
        mgr = SessionManager(session_dir=tmp_path)
        for i in range(3):
            sid = SessionManager.new_id(label=f"list-{i}")
            time.sleep(0.001)
            state = SessionState(
                session_id=sid,
                created_at=time.time(),
                updated_at=time.time(),
                label=f"list-{i}",
                emitted=i * 100,
            )
            mgr.save(state)
        sessions = mgr.list_sessions()
        assert len(sessions) >= 3

    def test_delete_session(self, tmp_path: Path) -> None:
        mgr = SessionManager(session_dir=tmp_path)
        sid = SessionManager.new_id(label="delete")
        state = SessionState(
            session_id=sid,
            created_at=time.time(),
            updated_at=time.time(),
            label="delete",
        )
        mgr.save(state)
        mgr.delete(sid)
        with pytest.raises(Exception):
            mgr.load(sid)

    def test_resume_ctx(self, tmp_path: Path) -> None:
        mgr = SessionManager(session_dir=tmp_path)
        sid = SessionManager.new_id(label="resume")
        state = SessionState(
            session_id=sid,
            created_at=time.time(),
            updated_at=time.time(),
            label="resume",
            emitted=200,
            bytes_written=2800,
            global_ctx_snapshot={"command": "pattern", "limit": 5000},
        )
        mgr.save(state)
        ctx = mgr.resume_ctx(sid)
        assert ctx["_resume_emitted"] == 200

    def test_resume_ctx_not_found(self, tmp_path: Path) -> None:
        mgr = SessionManager(session_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            mgr.resume_ctx("nonexistent")

    def test_describe_list(self, tmp_path: Path) -> None:
        mgr = SessionManager(session_dir=tmp_path)
        sid = SessionManager.new_id(label="desc")
        state = SessionState(
            session_id=sid,
            created_at=time.time(),
            updated_at=time.time(),
            label="desc",
            emitted=42,
        )
        mgr.save(state)
        desc = mgr.describe_list()
        assert isinstance(desc, str)

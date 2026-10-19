"""Fase 5 — Dockerfile and docker-compose validation tests."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestDockerfileStructure:
    def test_dockerfile_exists(self) -> None:
        assert (ROOT / "Dockerfile").exists()

    def test_dockerfile_has_stages(self) -> None:
        content = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        assert "FROM" in content
        assert "AS base" in content or "as base" in content

    def test_dockerfile_has_core_stage(self) -> None:
        content = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        assert "AS core" in content or "as core" in content

    def test_docker_compose_exists(self) -> None:
        assert (ROOT / "docker-compose.yml").exists()

    def test_docker_compose_valid_yaml(self) -> None:
        content = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        assert "services:" in content
        assert "wlf" in content.lower()

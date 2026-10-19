"""Fase 5 — Plugin schema validation tests."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.plugin_schema import (
    PLUGIN_SCHEMA,
    PluginValidationError,
    validate_manifest,
    load_and_validate,
)


class TestValidateManifest:
    def test_valid_manifest_no_errors(self) -> None:
        manifest = {
            "name": "my-plugin",
            "version": "1.0.0",
            "entry_point": "my_plugin.py",
        }
        errors = validate_manifest(manifest)
        assert errors == []

    def test_missing_required_fields(self) -> None:
        manifest: dict[str, object] = {}
        errors = validate_manifest(manifest)
        assert len(errors) == 3
        assert any("name" in e for e in errors)
        assert any("version" in e for e in errors)
        assert any("entry_point" in e for e in errors)

    def test_invalid_name_pattern(self) -> None:
        manifest = {
            "name": "INVALID NAME!",
            "version": "1.0.0",
            "entry_point": "x.py",
        }
        errors = validate_manifest(manifest)
        assert any("pattern" in e for e in errors)

    def test_invalid_version_pattern(self) -> None:
        manifest = {
            "name": "valid-name",
            "version": "not-semver",
            "entry_point": "x.py",
        }
        errors = validate_manifest(manifest)
        assert any("version" in e for e in errors)

    def test_wrong_type_for_string_field(self) -> None:
        manifest = {
            "name": 123,
            "version": "1.0.0",
            "entry_point": "x.py",
        }
        errors = validate_manifest(manifest)
        assert any("string" in e for e in errors)

    def test_wrong_type_for_int_field(self) -> None:
        manifest = {
            "name": "valid-name",
            "version": "1.0.0",
            "entry_point": "x.py",
            "vram_mb": "not-an-int",
        }
        errors = validate_manifest(manifest)
        assert any("int" in e for e in errors)

    def test_wrong_type_for_list_field(self) -> None:
        manifest = {
            "name": "valid-name",
            "version": "1.0.0",
            "entry_point": "x.py",
            "requires_extra": "should-be-list",
        }
        errors = validate_manifest(manifest)
        assert any("list" in e for e in errors)

    def test_int_min_violation(self) -> None:
        manifest = {
            "name": "valid-name",
            "version": "1.0.0",
            "entry_point": "x.py",
            "cpu_cores": 0,
        }
        errors = validate_manifest(manifest)
        assert any("cpu_cores" in e for e in errors)

    def test_description_max_length(self) -> None:
        manifest = {
            "name": "valid-name",
            "version": "1.0.0",
            "entry_point": "x.py",
            "description": "x" * 501,
        }
        errors = validate_manifest(manifest)
        assert any("max length" in e for e in errors)

    def test_full_manifest_all_optional(self) -> None:
        manifest = {
            "name": "full-plugin",
            "version": "2.1.0",
            "entry_point": "full.py",
            "description": "A full example",
            "author": "Test",
            "requires_extra": ["torch"],
            "vram_mb": 2048,
            "cpu_cores": 4,
            "min_wlf_version": "2.0.0",
            "tags": ["generation", "ml"],
        }
        errors = validate_manifest(manifest)
        assert errors == []

    def test_unknown_fields_ignored(self) -> None:
        manifest = {
            "name": "valid-name",
            "version": "1.0.0",
            "entry_point": "x.py",
            "custom_field": "anything",
        }
        errors = validate_manifest(manifest)
        assert errors == []


class TestLoadAndValidate:
    def test_load_json_manifest(self, tmp_path: Path) -> None:
        manifest = {
            "name": "json-plugin",
            "version": "1.0.0",
            "entry_point": "json_plugin.py",
        }
        p = tmp_path / "plugin.json"
        p.write_text(json.dumps(manifest), encoding="utf-8")
        result = load_and_validate(p)
        assert result["name"] == "json-plugin"

    def test_load_invalid_manifest_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "plugin.json"
        p.write_text(json.dumps({"bad": True}), encoding="utf-8")
        with pytest.raises(PluginValidationError):
            load_and_validate(p)

    def test_load_non_dict_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "plugin.json"
        p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with pytest.raises(PluginValidationError):
            load_and_validate(p)


class TestPluginSchema:
    def test_schema_has_required(self) -> None:
        assert "required" in PLUGIN_SCHEMA
        assert "name" in PLUGIN_SCHEMA["required"]

    def test_schema_has_properties(self) -> None:
        assert "properties" in PLUGIN_SCHEMA
        assert "name" in PLUGIN_SCHEMA["properties"]
        assert "version" in PLUGIN_SCHEMA["properties"]

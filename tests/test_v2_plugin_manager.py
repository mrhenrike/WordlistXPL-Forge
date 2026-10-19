"""Fase 5 — Plugin manager tests."""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wlf_modules.plugin_manager import (
    WLFPlugin,
    _REGISTRY,
    describe_all,
    discover,
    get_plugin,
    list_plugins,
    register_plugin,
    run_plugin,
)


class TestPluginRegistration:
    def test_register_and_get(self) -> None:
        original_registry = dict(_REGISTRY)
        try:
            @register_plugin
            class _TestPlug(WLFPlugin):
                name = "_test_registration"
                version = "0.0.1"

                def generate(self, profile, ctx):
                    yield ("test", 1.0)

            plug = get_plugin("_test_registration")
            assert plug is not None
            assert plug.name == "_test_registration"
        finally:
            _REGISTRY.clear()
            _REGISTRY.update(original_registry)

    def test_register_auto_name_from_class(self) -> None:
        original_registry = dict(_REGISTRY)
        try:
            @register_plugin
            class AutoNamed(WLFPlugin):
                version = "0.1.0"

                def generate(self, profile, ctx):
                    yield ("auto", 0.5)

            plug = get_plugin("autonamed")
            assert plug is not None
        finally:
            _REGISTRY.clear()
            _REGISTRY.update(original_registry)

    def test_list_plugins_returns_list(self) -> None:
        result = list_plugins()
        assert isinstance(result, list)

    def test_get_plugin_not_found(self) -> None:
        assert get_plugin("nonexistent_plugin_xyz") is None


class TestPluginDiscovery:
    def test_discover_empty_dir(self, tmp_path: Path) -> None:
        loaded = discover(plugin_dir=tmp_path, validate=False)
        assert loaded == []

    def test_discover_nonexistent_dir(self, tmp_path: Path) -> None:
        loaded = discover(plugin_dir=tmp_path / "no_such_dir", validate=False)
        assert loaded == []

    def test_discover_skips_underscore_files(self, tmp_path: Path) -> None:
        (tmp_path / "_private.py").write_text("x = 1")
        loaded = discover(plugin_dir=tmp_path, validate=False)
        assert "_private" not in loaded

    def test_discover_loads_py_files(self, tmp_path: Path) -> None:
        code = textwrap.dedent("""\
            import sys
            sys.path.insert(0, "{root}")
            from wlf_modules.plugin_manager import WLFPlugin, register_plugin

            @register_plugin
            class DiscoveryTestPlug(WLFPlugin):
                name = "_discovery_test"
                version = "0.0.1"
                def generate(self, profile, ctx):
                    yield ("found", 1.0)
        """.format(root=str(ROOT)))
        (tmp_path / "disc_test.py").write_text(code)
        original = dict(_REGISTRY)
        try:
            loaded = discover(plugin_dir=tmp_path, validate=False)
            assert "disc_test" in loaded
        finally:
            _REGISTRY.clear()
            _REGISTRY.update(original)


class TestPluginRunner:
    def test_run_unknown_plugin_raises(self) -> None:
        with pytest.raises(KeyError, match="not found"):
            list(run_plugin("does_not_exist", {}, {}))

    def test_run_plugin_generates_output(self) -> None:
        original = dict(_REGISTRY)
        try:
            @register_plugin
            class RunTestPlug(WLFPlugin):
                name = "_run_test"
                version = "0.0.1"

                def generate(self, profile, ctx):
                    for i in range(5):
                        yield (f"word_{i}", 0.8)

            results = list(run_plugin("_run_test", {}, {}))
            assert len(results) == 5
            assert results[0] == ("word_0", 0.8)
        finally:
            _REGISTRY.clear()
            _REGISTRY.update(original)


class TestPluginDescribe:
    def test_describe_all_no_plugins(self) -> None:
        original = dict(_REGISTRY)
        try:
            _REGISTRY.clear()
            desc = describe_all()
            assert "No plugins" in desc
        finally:
            _REGISTRY.clear()
            _REGISTRY.update(original)

    def test_wlf_plugin_describe(self) -> None:
        original = dict(_REGISTRY)
        try:
            @register_plugin
            class DescPlug(WLFPlugin):
                name = "_desc_test"
                version = "1.2.3"
                description = "A description"

                def generate(self, profile, ctx):
                    yield ("x", 0.5)

            plug = get_plugin("_desc_test")
            assert plug is not None
            desc = plug.describe()
            assert "_desc_test" in desc
            assert "1.2.3" in desc
        finally:
            _REGISTRY.clear()
            _REGISTRY.update(original)

    def test_check_requirements_all_met(self) -> None:
        original = dict(_REGISTRY)
        try:
            @register_plugin
            class ReqPlug(WLFPlugin):
                name = "_req_test"
                version = "0.0.1"
                requires_extra = ["sys", "os"]

                def generate(self, profile, ctx):
                    yield ("x", 0.5)

            plug = get_plugin("_req_test")
            assert plug is not None
            missing = plug.check_requirements()
            assert missing == []
        finally:
            _REGISTRY.clear()
            _REGISTRY.update(original)

    def test_check_requirements_missing(self) -> None:
        original = dict(_REGISTRY)
        try:
            @register_plugin
            class MissPlug(WLFPlugin):
                name = "_miss_test"
                version = "0.0.1"
                requires_extra = ["nonexistent_pkg_xyz"]

                def generate(self, profile, ctx):
                    yield ("x", 0.5)

            plug = get_plugin("_miss_test")
            assert plug is not None
            missing = plug.check_requirements()
            assert "nonexistent_pkg_xyz" in missing
        finally:
            _REGISTRY.clear()
            _REGISTRY.update(original)

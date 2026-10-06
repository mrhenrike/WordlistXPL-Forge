"""plugin_manager.py - Plugin architecture for extending WordlistXPL-Forge.

Plugins live in ~/.wlf/plugins/ and are discovered automatically.
Each plugin is a Python file (or package) that exports a WLFPlugin subclass.

Plugin contract::

    from wfh_modules.plugin_manager import WLFPlugin, register_plugin

    @register_plugin
    class MyPlugin(WLFPlugin):
        name    = "my_engine"
        version = "1.0.0"
        requires_extra = []       # pip extras needed (e.g. ["torch"])
        vram_mb = 0               # VRAM needed in MiB (0 = CPU only)
        cpu_cores = 1

        def generate(self, profile, ctx) -> Generator[tuple[str,float], None, None]:
            for i in range(ctx.get("limit", 1000)):
                yield (f"example_{i}", 0.5)

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generator, Optional, Type

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path.home() / ".wlf" / "plugins"
_REGISTRY: dict[str, "WLFPlugin"] = {}


# ── Base class ────────────────────────────────────────────────────────────────

class WLFPlugin(ABC):
    """Base class for all WLF plugins."""

    name: str = ""
    version: str = "0.1.0"
    description: str = ""
    requires_extra: list[str] = []
    vram_mb: int = 0
    cpu_cores: int = 1

    @abstractmethod
    def generate(
        self,
        profile: dict,
        ctx: dict,
    ) -> Generator[tuple[str, float], None, None]:
        """Generate (candidate, score) tuples.

        Args:
            profile: Target profile dict (same schema as profile YAML).
            ctx:     _GLOBAL_CTX dict with limit, ram_budget_pct, etc.
        """

    def check_requirements(self) -> list[str]:
        """Return list of unmet requirements (empty = all ok)."""
        missing = []
        for extra in self.requires_extra:
            try:
                importlib.import_module(extra)
            except ImportError:
                missing.append(extra)
        return missing

    def describe(self) -> str:
        return (
            f"{self.name} v{self.version} — {self.description}\n"
            f"  Requires: {self.requires_extra or 'none'} | "
            f"VRAM: {self.vram_mb}MB | CPU cores: {self.cpu_cores}"
        )


# ── Registration ──────────────────────────────────────────────────────────────

def register_plugin(cls: Type[WLFPlugin]) -> Type[WLFPlugin]:
    """Class decorator to register a plugin."""
    inst = cls()
    if not inst.name:
        inst.name = cls.__name__.lower()
    _REGISTRY[inst.name] = inst
    logger.debug("Plugin registered: %s", inst.name)
    return cls


def get_plugin(name: str) -> Optional[WLFPlugin]:
    return _REGISTRY.get(name)


def list_plugins() -> list[WLFPlugin]:
    return list(_REGISTRY.values())


# ── Discovery ─────────────────────────────────────────────────────────────────

def discover(plugin_dir: Optional[Path] = None) -> list[str]:
    """Scan plugin_dir for .py files and load them.  Returns list of loaded names."""
    d = plugin_dir or _PLUGIN_DIR
    if not d.exists():
        return []
    loaded = []
    for p in d.glob("*.py"):
        if p.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"wlf_plugin_{p.stem}", p)
            if spec is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            loaded.append(p.stem)
            logger.info("Plugin loaded: %s", p)
        except Exception as exc:
            logger.warning("Plugin load error %s: %s", p, exc)
    return loaded


def discover_packages(plugin_dir: Optional[Path] = None) -> list[str]:
    """Scan for plugin packages (directories with __init__.py)."""
    d = plugin_dir or _PLUGIN_DIR
    if not d.exists():
        return []
    loaded = []
    for p in d.iterdir():
        if p.is_dir() and (p / "__init__.py").exists():
            try:
                spec = importlib.util.spec_from_file_location(
                    f"wlf_plugin_pkg_{p.name}", p / "__init__.py"
                )
                if spec is None:
                    continue
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
                loaded.append(p.name)
            except Exception as exc:
                logger.warning("Plugin package error %s: %s", p, exc)
    return loaded


def auto_discover() -> list[str]:
    """Discover all plugins (files and packages) in the default plugin dir."""
    return discover() + discover_packages()


# ── Runner ────────────────────────────────────────────────────────────────────

def run_plugin(
    name: str,
    profile: dict,
    ctx: dict,
) -> Generator[tuple[str, float], None, None]:
    """Run a registered plugin by name; raise KeyError if not found."""
    plugin = _REGISTRY.get(name)
    if plugin is None:
        raise KeyError(f"Plugin not found: '{name}'. Available: {list(_REGISTRY)}")
    missing = plugin.check_requirements()
    if missing:
        raise RuntimeError(
            f"Plugin '{name}' requires: {missing}. "
            f"Install with: pip install {' '.join(missing)}"
        )
    return plugin.generate(profile, ctx)


def describe_all() -> str:
    if not _REGISTRY:
        return "No plugins loaded."
    return "\n".join(p.describe() for p in _REGISTRY.values())

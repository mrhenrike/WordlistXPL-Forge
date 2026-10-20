"""Persistent configuration file support (~/.wlf/config.yaml)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path(os.environ.get("WLF_CONFIG_DIR", "~/.wlf")).expanduser()
_CONFIG_FILE = _CONFIG_DIR / "config.yaml"

DEFAULTS: dict[str, Any] = {
    "threads": 5,
    "compute_mode": "auto",
    "use_ml": True,
    "limit": 0,
    "timeout": 0,
    "min_len": 0,
    "max_len": 0,
    "ram_budget_pct": 50.0,
    "vram_budget_mb": 4096,
    "chunk_lines": 0,
    "chunk_bytes": 0,
    "stream": False,
    "locale": "en",
    "model_dir": "",
    "output_dir": "",
}

_TEMPLATE = """\
# WordlistXPL-Forge configuration
# Persistent defaults  - CLI flags always override these values.
# Location: ~/.wlf/config.yaml  (override with WLF_CONFIG_DIR env var)

# ── Execution ────────────────────────────────────────────────────────────────
threads: 5                  # Worker threads (1-300)
compute_mode: auto          # cpu | gpu | cuda | rocm | mps | auto | hybrid
use_ml: true                # Enable ML-powered engines globally

# ── Limits ───────────────────────────────────────────────────────────────────
limit: 0                    # Global line limit (0 = unlimited)
timeout: 0                  # Global timeout in seconds (0 = unlimited)
min_len: 0                  # Minimum entry length (0 = no filter)
max_len: 0                  # Maximum entry length (0 = no filter)

# ── Resources ────────────────────────────────────────────────────────────────
ram_budget_pct: 50.0        # Max % of system RAM for ResourceGovernor
vram_budget_mb: 4096        # Max VRAM budget in MB for GPU engines
chunk_lines: 0              # Chunk size in lines (0 = auto)
chunk_bytes: 0              # Chunk size in bytes (0 = auto)
stream: false               # Stream output to stdout instead of buffering

# ── Locale ───────────────────────────────────────────────────────────────────
locale: en                  # Default locale (en, pt-br, es, fr, de)

# ── Paths ────────────────────────────────────────────────────────────────────
model_dir: ""               # Directory for ML model checkpoints
output_dir: ""              # Default output directory for generated wordlists
"""


def config_dir() -> Path:
    """Return the configuration directory path."""
    return _CONFIG_DIR


def config_path() -> Path:
    """Return the configuration file path."""
    return _CONFIG_FILE


def load_config() -> dict[str, Any]:
    """Load config from ~/.wlf/config.yaml, returning DEFAULTS on any error."""
    cfg = dict(DEFAULTS)
    if not _CONFIG_FILE.is_file():
        return cfg
    try:
        import yaml
    except ImportError:
        try:
            text = _CONFIG_FILE.read_text(encoding="utf-8")
            cfg.update(_parse_simple_yaml(text))
        except Exception:
            pass
        return cfg
    try:
        raw = yaml.safe_load(_CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            for key in DEFAULTS:
                if key in raw and raw[key] is not None:
                    cfg[key] = type(DEFAULTS[key])(raw[key])
    except Exception:
        pass
    return cfg


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Minimal key: value parser for when PyYAML is not installed."""
    result: dict[str, Any] = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if key not in DEFAULTS:
            continue
        default = DEFAULTS[key]
        if isinstance(default, bool):
            result[key] = val.lower() in ("true", "yes", "1", "on")
        elif isinstance(default, int):
            try:
                result[key] = int(val)
            except ValueError:
                pass
        elif isinstance(default, float):
            try:
                result[key] = float(val)
            except ValueError:
                pass
        else:
            if val.startswith(('"', "'")) and len(val) >= 2:
                val = val[1:-1]
            result[key] = val
    return result


def init_config(force: bool = False) -> Path:
    """Create default config file. Returns the path written."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if _CONFIG_FILE.exists() and not force:
        raise FileExistsError(f"Config already exists: {_CONFIG_FILE}")
    _CONFIG_FILE.write_text(_TEMPLATE, encoding="utf-8")
    return _CONFIG_FILE


def apply_config_to_ctx(ctx: dict[str, Any], cfg: dict[str, Any]) -> None:
    """Merge config values into _GLOBAL_CTX as defaults (CLI overrides later)."""
    for key in ("threads", "compute_mode", "use_ml", "limit", "timeout",
                "min_len", "max_len", "ram_budget_pct", "vram_budget_mb",
                "chunk_lines", "chunk_bytes", "stream"):
        if key in cfg:
            ctx[key] = cfg[key]

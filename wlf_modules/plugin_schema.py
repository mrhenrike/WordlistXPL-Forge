"""plugin_schema.py - Plugin manifest validation.

Validates plugin YAML manifests (plugin.yaml) against the WLF plugin
schema before loading.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

PLUGIN_SCHEMA: dict[str, Any] = {
    "required": ["name", "version", "entry_point"],
    "properties": {
        "name": {"type": "string", "pattern": r"^[a-z][a-z0-9_-]{1,63}$"},
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "description": {"type": "string", "max_length": 500},
        "author": {"type": "string"},
        "entry_point": {"type": "string"},
        "requires_extra": {"type": "list", "items": {"type": "string"}},
        "vram_mb": {"type": "int", "min": 0},
        "cpu_cores": {"type": "int", "min": 1},
        "min_wlf_version": {"type": "string"},
        "tags": {"type": "list", "items": {"type": "string"}},
    },
}


class PluginValidationError(Exception):
    """Raised when a plugin manifest fails validation."""


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Validate a plugin manifest dict against the schema.

    Args:
        manifest: Parsed YAML/JSON manifest.

    Returns:
        List of validation errors (empty = valid).
    """
    errors: list[str] = []

    for field in PLUGIN_SCHEMA["required"]:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    props = PLUGIN_SCHEMA["properties"]
    for key, value in manifest.items():
        if key not in props:
            continue
        spec = props[key]
        expected_type = spec.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Field '{key}' must be a string, got {type(value).__name__}")
        elif expected_type == "int" and not isinstance(value, int):
            errors.append(f"Field '{key}' must be an int, got {type(value).__name__}")
        elif expected_type == "list" and not isinstance(value, list):
            errors.append(f"Field '{key}' must be a list, got {type(value).__name__}")
        if expected_type == "string" and isinstance(value, str):
            import re
            pattern = spec.get("pattern")
            if pattern and not re.match(pattern, value):
                errors.append(f"Field '{key}' value '{value}' does not match pattern {pattern}")
            max_len = spec.get("max_length")
            if max_len and len(value) > max_len:
                errors.append(f"Field '{key}' exceeds max length {max_len}")
        if expected_type == "int" and isinstance(value, int):
            min_val = spec.get("min")
            if min_val is not None and value < min_val:
                errors.append(f"Field '{key}' must be >= {min_val}, got {value}")

    return errors


def load_and_validate(manifest_path: Path) -> dict[str, Any]:
    """Load and validate a plugin manifest YAML file.

    Args:
        manifest_path: Path to plugin.yaml.

    Returns:
        Validated manifest dict.

    Raises:
        PluginValidationError: If validation fails.
    """
    try:
        import yaml
        with manifest_path.open(encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
    except ImportError:
        import json
        json_path = manifest_path.with_suffix(".json")
        if json_path.exists():
            with json_path.open(encoding="utf-8") as f:
                manifest = json.load(f)
        else:
            raise PluginValidationError(
                f"Cannot load {manifest_path}: install PyYAML or provide plugin.json"
            )

    if not isinstance(manifest, dict):
        raise PluginValidationError(f"Manifest must be a dict, got {type(manifest).__name__}")

    errors = validate_manifest(manifest)
    if errors:
        raise PluginValidationError(
            f"Plugin manifest validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return manifest

# Plugin System

WordlistXPL-Forge supports external plugins for custom generation engines.

## Plugin Directory

Plugins are discovered from `~/.wlf/plugins/`. Each plugin is either:

- A single `.py` file (simple plugin)
- A directory with `__init__.py` and optional `plugin.yaml` manifest (package plugin)

## Plugin Contract

Every plugin must subclass `WLFPlugin` and use the `@register_plugin` decorator:

```python
from wlf_modules.plugin_manager import WLFPlugin, register_plugin

@register_plugin
class MyCustomEngine(WLFPlugin):
    name = "my-engine"
    version = "1.0.0"
    description = "Custom password generation engine"
    requires_extra = []       # pip packages needed (e.g. ["torch"])
    vram_mb = 0               # VRAM in MiB (0 = CPU only)
    cpu_cores = 1

    def generate(self, profile, ctx):
        limit = ctx.get("limit", 1000)
        for i in range(limit):
            yield (f"custom_{i}", 0.5)
```

## Manifest Schema (plugin.yaml)

Package plugins can include a `plugin.yaml` manifest for validation:

```yaml
name: my-engine
version: 1.0.0
description: Custom password generation engine
author: Your Name
entry_point: my_engine.py
requires_extra: []
vram_mb: 0
cpu_cores: 1
min_wlf_version: "2.0.0"
tags:
  - generation
  - custom
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Plugin identifier (`[a-z][a-z0-9_-]{1,63}`) |
| `version` | string | Semantic version (`X.Y.Z`) |
| `entry_point` | string | Python file with the `@register_plugin` class |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | `""` | Short description (max 500 chars) |
| `author` | string | `""` | Author name |
| `requires_extra` | list[str] | `[]` | pip packages required |
| `vram_mb` | int | `0` | VRAM requirement in MiB |
| `cpu_cores` | int | `1` | CPU cores used |
| `min_wlf_version` | string | `""` | Minimum WLF version |
| `tags` | list[str] | `[]` | Categorization tags |

## CLI Usage

```bash
# List loaded plugins
wlf plugin list

# Run a plugin
wlf plugin run my-engine -o output.lst

# Show plugin details
wlf plugin info my-engine
```

## Example: Fibonacci Plugin

File: `~/.wlf/plugins/fibonacci_plugin.py`

```python
from wlf_modules.plugin_manager import WLFPlugin, register_plugin

@register_plugin
class FibonacciPlugin(WLFPlugin):
    name = "fibonacci"
    version = "1.0.0"
    description = "Generate Fibonacci-based numeric passwords"

    def generate(self, profile, ctx):
        limit = ctx.get("limit", 1000)
        a, b, count = 0, 1, 0
        while count < limit:
            pw = str(a)
            if 4 <= len(pw) <= 20:
                yield (pw, max(0.1, 1.0 - count / limit))
                count += 1
            a, b = b, a + b
            if a > 10**20:
                break
```

## Validation

Manifests are validated at discovery time. Invalid manifests produce
warnings but do not prevent other plugins from loading. Use
`wlf_modules.plugin_schema.validate_manifest()` to validate
programmatically.

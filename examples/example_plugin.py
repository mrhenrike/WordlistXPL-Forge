"""Example WLF plugin — Fibonacci numeric passwords.

Demonstrates the plugin contract: subclass WLFPlugin, decorate with
@register_plugin, and implement generate().

To install: copy this file to ~/.wlf/plugins/
"""
from __future__ import annotations

from collections.abc import Generator
from typing import Any

from wlf_modules.plugin_manager import WLFPlugin, register_plugin


@register_plugin
class FibonacciPlugin(WLFPlugin):
    name = "fibonacci"
    version = "1.0.0"
    description = "Generate Fibonacci-based numeric passwords"

    def generate(
        self,
        profile: dict[str, Any],
        ctx: dict[str, Any],
    ) -> Generator[tuple[str, float], None, None]:
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

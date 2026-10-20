"""pt_br.py - Brazilian Portuguese locale engine (wraps br_deep_engine).

Provides backward-compatible access to BRDeepEngine through the
locale framework.  All actual generation logic lives in
``wlf_modules.br_deep_engine``; this module adapts it to the
BaseLocaleEngine interface.

Author: André Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

from collections.abc import Generator

from wlf_modules.locales import BaseLocaleEngine, register_engine


@register_engine
class PTBREngine(BaseLocaleEngine):
    locale_code = "pt-br"
    locale_name = "Brazilian Portuguese"
    locale_aliases = ["pt_br", "ptbr", "brazil", "brasil", "brasileiro"]

    def generate(self) -> Generator[tuple[str, float], None, None]:
        from wlf_modules.br_deep_engine import BRDeepEngine
        if self.profile:
            engine = BRDeepEngine(profile=self.profile, rng_seed=42)
        else:
            engine = BRDeepEngine(rng_seed=42)
        yield from engine.generate(max_candidates=self.max_candidates)

"""
CogPIE - Cognitive Pattern Inference Engine.

A 5-layer hybrid algorithm for targeted password candidate generation based on
cognitive bias modeling. Combines semantic expansion, cognitive transforms,
probabilistic ranking (Markov + PCFG hybrid), entropy-based scoring, and
policy-aware filtering.

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

__version__ = "0.1.0"

from wlf_modules.cogpie.engine import CogPIEEngine

__all__ = ["CogPIEEngine", "__version__"]

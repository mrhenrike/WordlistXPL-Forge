"""pipeline_dsl.py - YAML/JSON pipeline composition DSL for multi-engine generation.

Describes a complete generation pipeline declaratively. Parses the YAML,
resolves engine factories from registered builders, and hands off to
AsyncGeneratorPipeline for execution.

YAML schema::

    global:
      limit: 500000          # total candidates (0 = unlimited)
      min_len: 8
      max_len: 16
      emit_scores: false     # include score column in output

    stages:
      - engine: markov
        model: .model/rockyou.markov
        limit: 150000
        weight: 0.35
        params:
          beam_width: 100000

      - engine: pcfg
        model: .model/pcfg_grammar.json
        limit: 200000
        weight: 0.40
        params:
          zipf_s: 1.0
          top_structures: 80

      - engine: semantic
        profile: target.yaml
        limit: 100000
        weight: 0.25

    merge:
      strategy: weighted_rank   # weighted_rank | round_robin | score_only
      dedup: bloom              # bloom | exact | none
      output: candidates.lst

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Generator, Optional

logger = logging.getLogger(__name__)


# ── YAML loader (optional dep) ────────────────────────────────────────────────

def _load_yaml(path: str) -> dict:
    try:
        import yaml  # type: ignore
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except ImportError:
        pass
    # fallback: try JSON
    import json
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ── Engine factory registry ───────────────────────────────────────────────────

_FACTORIES: dict[str, Callable[[dict, dict], Generator]] = {}


def register_engine(name: str):
    """Decorator to register an engine factory function."""
    def _dec(fn):
        _FACTORIES[name] = fn
        return fn
    return _dec


def _get_factory(name: str, stage: dict, global_cfg: dict) -> Optional[Callable]:
    fn = _FACTORIES.get(name)
    if fn is None:
        fn = _FACTORIES.get(name.replace("-", "_"))
    if fn is None:
        logger.warning("No factory registered for engine '%s', skipping stage", name)
        return None
    return lambda: fn(stage, global_cfg)


# ── Built-in engine factories ─────────────────────────────────────────────────

@register_engine("markov")
def _markov_factory(stage: dict, _gcfg: dict):
    from wfh_modules.markov_engine import MarkovModel
    m = MarkovModel()
    path = stage.get("model") or ".model/markov_model.json"
    if not Path(path).exists():
        logger.error("Markov model not found: %s", path)
        return iter([])
    m.load(path)
    p = stage.get("params") or {}
    return m.generate(
        max_candidates=stage.get("limit", 0),
        min_length=_gcfg.get("min_len", 4),
        max_length=_gcfg.get("max_len", 16),
        beam_width=p.get("beam_width", 100_000),
    )


@register_engine("pcfg")
def _pcfg_factory(stage: dict, _gcfg: dict):
    from wfh_modules.pcfg_engine import PCFGGrammar
    g = PCFGGrammar()
    path = stage.get("model") or ".model/pcfg_grammar.json"
    if not Path(path).exists():
        logger.error("PCFG grammar not found: %s", path)
        return iter([])
    g.load(path)
    p = stage.get("params") or {}
    return g.generate(
        max_candidates=stage.get("limit", 0),
        beam_width=p.get("beam_width", 250_000),
        zipf_s=float(p.get("zipf_s", 0)),
        top_structures=int(p.get("top_structures", 50)),
        top_terminals=int(p.get("top_terminals", 80)),
    )


@register_engine("semantic")
def _semantic_factory(stage: dict, gcfg: dict):
    from wfh_modules.semantic_pcfg import generate_semantic
    from wfh_modules.profiler import load_profile_yaml
    pf = stage.get("profile")
    if not pf or not Path(pf).exists():
        logger.error("semantic engine requires valid 'profile' path")
        return iter([])
    profile = load_profile_yaml(pf)
    return generate_semantic(profile, max_candidates=stage.get("limit", 50_000))


@register_engine("mask")
def _mask_factory(stage: dict, _gcfg: dict):
    from wfh_modules.gpu_expand import iter_mask
    mask = stage.get("mask", "?l?l?l?d?d")
    return iter_mask(mask, max_candidates=stage.get("limit", 100_000))


@register_engine("prince")
def _prince_factory(stage: dict, gcfg: dict):
    from wfh_modules.prince_engine import PrinceEngine
    words_file = stage.get("words")
    if not words_file or not Path(words_file).exists():
        logger.error("prince engine requires valid 'words' path")
        return iter([])
    p = stage.get("params") or {}
    eng = PrinceEngine(
        min_elements=int(p.get("min_elements", 1)),
        max_elements=int(p.get("max_elements", 2)),
        limit=stage.get("limit", 0),
    )
    return eng.generate_from_file(words_file)


@register_engine("neural")
def _neural_factory(stage: dict, gcfg: dict):
    from wfh_modules.neural_engine import NeuralPasswordGenerator
    path = stage.get("model") or ".model/neural_lstm.pt"
    p = stage.get("params") or {}
    gen = NeuralPasswordGenerator()
    gen.load(path)
    return gen.generate(
        max_candidates=stage.get("limit", 10_000),
        temperature=float(p.get("temperature", 1.0)),
        prefix=p.get("prefix"),
        min_len=gcfg.get("min_len", 4),
        max_len=gcfg.get("max_len", 16),
    )


@register_engine("gan")
def _gan_factory(stage: dict, gcfg: dict):
    from wfh_modules.gan_engine import GANPasswordEngine
    p = stage.get("params") or {}
    eng = GANPasswordEngine(
        model_path=stage.get("model"),
        temperature=float(p.get("temperature", 1.0)),
        vram_budget_mb=gcfg.get("vram_budget_mb", 4096),
    )
    return eng.generate(max_candidates=stage.get("limit", 10_000))


@register_engine("transformer")
def _transformer_factory(stage: dict, gcfg: dict):
    from wfh_modules.transformer_engine import TransformerPasswordEngine
    p = stage.get("params") or {}
    eng = TransformerPasswordEngine(
        model_path=stage.get("model"),
        vram_budget_mb=gcfg.get("vram_budget_mb", 4096),
    )
    return eng.generate(
        max_candidates=stage.get("limit", 10_000),
        prefix=p.get("prefix"),
        pattern=p.get("pattern"),
        temperature=float(p.get("temperature", 1.0)),
    )


@register_engine("br_deep")
def _br_deep_factory(stage: dict, gcfg: dict):
    from wfh_modules.br_deep_engine import BRDeepEngine
    p = stage.get("params") or {}
    eng = BRDeepEngine(
        profile=stage.get("profile"),
        sector=p.get("sector"),
        include_cpf_patterns=bool(p.get("include_cpf_patterns", True)),
        include_cnpj_patterns=bool(p.get("include_cnpj_patterns", True)),
        include_cep_patterns=bool(p.get("include_cep_patterns", True)),
    )
    return eng.generate(max_candidates=stage.get("limit", 50_000))


# ── Pipeline execution ─────────────────────────────────────────────────────────

class PipelineDSL:
    """Parse and execute a YAML pipeline definition."""

    def __init__(self, pipeline_file: str, global_ctx: Optional[dict] = None) -> None:
        self.raw = _load_yaml(pipeline_file)
        self.global_ctx = global_ctx or {}

    def _global_cfg(self) -> dict:
        cfg = dict(self.global_ctx)
        cfg.update(self.raw.get("global") or {})
        return cfg

    def build_and_run(self) -> Generator[str, None, None]:
        """Build the pipeline and return a candidate generator."""
        from wfh_modules.async_pipeline import AsyncGeneratorPipeline, EngineSlot

        gcfg = self._global_cfg()
        stages = self.raw.get("stages") or []
        merge_cfg = self.raw.get("merge") or {}

        global_limit = int(gcfg.get("limit", 0))
        emit_scores = bool(gcfg.get("emit_scores", False))
        dedup = merge_cfg.get("dedup", "bloom")

        slots = []
        for stage in stages:
            engine = str(stage.get("engine", ""))
            factory_fn = _get_factory(engine, stage, gcfg)
            if factory_fn is None:
                continue
            slots.append(EngineSlot(
                name=engine,
                factory=factory_fn,
                weight=float(stage.get("weight", 1.0)),
                limit=int(stage.get("limit", 0)),
            ))

        use_bloom = dedup != "none"
        pipeline = AsyncGeneratorPipeline(
            slots,
            global_limit=global_limit,
            bloom_capacity=max(global_limit * 2, 2_000_000) if global_limit else 5_000_000,
            emit_scores=emit_scores,
        )
        if not use_bloom:
            pipeline.bloom = _NullBloom()  # type: ignore[assignment]
        return pipeline.run()

    def output_path(self) -> Optional[str]:
        return self.raw.get("merge", {}).get("output")


class _NullBloom:
    """Bloom filter replacement that never deduplicates."""
    def add(self, item: str) -> bool:
        return False


def execute_pipeline(pipeline_file: str, global_ctx: Optional[dict] = None) -> Generator[str, None, None]:
    """Parse and run a pipeline YAML file; yields candidate strings."""
    dsl = PipelineDSL(pipeline_file, global_ctx)
    return dsl.build_and_run()

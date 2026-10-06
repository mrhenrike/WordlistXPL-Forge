# WordlistXPL-Forge — Architecture

> Version 2.0.0

## Overview

WordlistXPL-Forge is a **pure wordlist generator**.  It does not crack passwords.
Other tools (Hashcat, JtR, Hydra, Aircrack-ng) consume its output.

```
                         ┌─────────────────────────────────────┐
                         │         wlf.py  (CLI entrypoint)   │
                         │   _GLOBAL_CTX  ·  argparse          │
                         └────────────────┬────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
   ┌──────────▼──────────┐  ┌─────────────▼──────────┐  ┌───────────▼────────┐
   │  Classical engines  │  │   Neural engines        │  │  Evolutionary      │
   │  markov_engine      │  │   neural_engine (LSTM)  │  │  map_elites        │
   │  pcfg_engine        │  │   gan_engine (GAN)      │  │  genetic_engine    │
   │  semantic_pcfg      │  │   vae_engine            │  │  pbmp_full         │
   │  pattern_engine     │  │   transformer_engine    │  └───────────┬────────┘
   │  prince_engine      │  │   diffusion_engine      │              │
   │  br_deep_engine     │  │   masked_lm_engine      │              │
   │  bayesian_full      │  │   tcn_engine            │              │
   │  domain_pcfg        │  │   flow_engine           │              │
   │  temporal_drift     │  └─────────────┬───────────┘              │
   │  password_graph     │                │                           │
   └──────────┬──────────┘                │                           │
              │                           │                           │
              └───────────────────────────┴───────────────────────────┘
                                          │
                             ┌────────────▼────────────┐
                             │  AsyncGeneratorPipeline  │
                             │  ┌─────────────────────┐ │
                             │  │  BloomFilter (dedup) │ │
                             │  │  Priority queue merge│ │
                             │  │  Score normalizer    │ │
                             │  └─────────────────────┘ │
                             └────────────┬─────────────┘
                                          │
                             ┌────────────▼─────────────┐
                             │    ResourceGovernor       │
                             │  RAM/VRAM polling         │
                             │  Chunk rotation           │
                             │  STOP_* codes             │
                             └────────────┬─────────────┘
                                          │
                             ┌────────────▼─────────────┐
                             │     _write_output()       │
                             │  tqdm progress bar        │
                             │  limit / timeout guard    │
                             │  stdout or file output    │
                             └──────────────────────────┘
```

## Core data flow

1. **CLI** parses args → populates `_GLOBAL_CTX` (threads, limit, timeout, compute_mode, etc.)
2. **Command handler** (`cmd_*`) creates one or more engine instances
3. **Engines** yield `str` or `(str, float)` tuples — **never** materialize full lists
4. **AsyncGeneratorPipeline** merges multiple engines via threaded queues + Bloom dedup
5. **ResourceGovernor** monitors RAM/VRAM; emits STOP codes if thresholds breached
6. **`_write_output()`** consumes the generator, applies limit/timeout, writes to file or stdout

## Key modules

| Module | Role |
|--------|------|
| `wlf.py` | CLI, `_GLOBAL_CTX`, `_write_output()`, all `cmd_*` handlers |
| `resource_governor.py` | Anti-OOM: RAM/VRAM monitoring, chunk rotation |
| `async_pipeline.py` | Multi-engine parallel merge with Bloom dedup |
| `score_normalizer.py` | Maps heterogeneous scores → [0,1] |
| `session_manager.py` | Checkpoint/resume — persists state to `~/.wlf/sessions/` |
| `pipeline_dsl.py` | YAML pipeline executor |
| `strategy_engine.py` | Bayesian structure priors + strategy plan |
| `bandit_router.py` | UCB1 multi-armed bandit for engine selection |
| `rl_router.py` | Actor-Critic RL extension of BanditRouter |
| `pbmp_full.py` | Full PBMP: P(strategy | history, context, behavior, population) |
| `explainer.py` | Candidate explanation: structure, entropy, engine provenance |
| `plugin_manager.py` | WLFPlugin ABC + discovery from `~/.wlf/plugins/` |
| `api_server.py` | REST API (FastAPI/aiohttp) with streaming NDJSON |

## Score normalization

All engines emit a raw score on different scales.  `score_normalizer.py` maps them to [0,1]:

| Engine family | Raw scale | Direction | Normalization |
|---------------|-----------|-----------|---------------|
| Markov / OMEN | COST (float) | lower = better | `1 - sigmoid(cost)` |
| PCFG | LOGPROB (negative) | higher = better | `(logp - min) / range` |
| GAN / Diffusion | PROB (0-1) | higher = better | identity |
| VAE | LOGLIK (negative) | higher = better | `(loglik + 30) / 25` |
| Transformer | PERPLEXITY | lower = better | `1 / (1 + perp/50)` |
| Semantic / Heuristic | HEURISTIC (0-1) | higher = better | identity |

## Generator contract

Every engine must:
- Yield `str` **or** `(str, float)` tuples
- Never accumulate the full list in memory
- Handle `GeneratorExit` gracefully (no leak)
- Accept `max_candidates: int` parameter

## Resource governance stop codes

| Code | Meaning |
|------|---------|
| `STOP_OK` | Limit reached normally |
| `STOP_LIMIT` | `--limit` exhausted |
| `STOP_TIMEOUT` | `--timeout` elapsed |
| `STOP_RAM` | RAM budget exceeded |
| `STOP_SHUTDOWN` | SIGINT/SIGTERM received |
| `STOP_DISK` | Disk space < 512 MB |

## Neural engines — optional torch pattern

```python
def _require_torch():
    try:
        import torch
        return torch
    except ImportError as exc:
        raise RuntimeError("pip install wordlistxpl-forge[neural]") from exc
```

Every neural engine calls `_require_torch()` at generation time. If unavailable,
the engine logs a warning and falls back to a CPU heuristic generator — the pipeline
continues without interruption.

## Session persistence

```
~/.wlf/sessions/
  <session_id>.json   ← SessionState (emitted, chunk_index, bandit_stats, etc.)
```

Resume:
```bash
python wlf.py session list
python wlf.py session resume abc123
```

## Plugin architecture

```python
# ~/.wlf/plugins/my_engine.py
from wfh_modules.plugin_manager import WLFPlugin, register_plugin

@register_plugin
class MyEngine(WLFPlugin):
    name = "my_engine"
    version = "1.0.0"

    def generate(self, profile, ctx):
        for i in range(ctx.get("limit", 1000)):
            yield (f"example_{i}", 0.5)
```

```bash
python wlf.py plugin list
python wlf.py plugin run my_engine --limit 10000 -o out.txt
```

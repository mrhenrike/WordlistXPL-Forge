# Changelog

All notable changes to WordlistXPL-Forge are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-10-06

### Added

- **Aurora CLI surface** — wired argparse for `pipeline`, `session`, `score`,
  `explain`, `serve`, `br-deep`, `pbmp`, `evolve`, `graph-expand`,
  `temporal-model`, `domain-pcfg`, `plugin`, `vae-interp`.
- Multi-engine modules: `async_pipeline`, `pipeline_dsl`, `session_manager`,
  `score_normalizer`, GAN/VAE/Transformer/Diffusion/Masked-LM engines,
  `br_deep_engine`, `pbmp_full`, MAP-Elites / genetic / RL router / Bayesian,
  TCN/flow/temporal drift/password graph/domain PCFG, `api_server`,
  `plugin_manager`, `explainer`.
- ResourceGovernor globals: `--ram-budget-pct`, `--vram-budget-mb`,
  `--chunk-lines`/`--chunk-bytes`, `--stream`, `--safe-default-limit`.
- Streaming helpers: `emit`, `maskgen`, `strategy`, `bandit`.
- Docs: `docs/COOKBOOK.md`, `CLI-REFERENCE.md`, `ARCHITECTURE.md`,
  `MODELS.md` / `MODELS-DEEP.md`, `INTEGRATIONS.md`, PT-BR guides.
- Packaging extras: `[gpu]`, `[api]` (FastAPI/uvicorn).

### Fixed

- v2 handlers called undefined `_error` and passed `_GLOBAL_CTX` dict into
  `_write_output` (expects an output path).
- Session `show`/`resume` now use `SessionManager.load` / `resume_ctx`.
- Profile load for `br-deep` / `pbmp` accepts JSON or YAML.

### Changed

- Package version aligned to **2.0.0** (`wlf.py` + `pyproject.toml`).

## [1.3.0] - prior

Baseline probabilistic engines (Markov/OMEN, PCFG), profiling, rules, list ops,
optional LSTM neural path, and ResourceGovernor foundations.

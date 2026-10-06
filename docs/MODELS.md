# Generation models matrix (WordlistXPL-Forge)

Authorized testing only. WLF **generates ordered candidates**; Hashcat/JtR crack.

Defaults are **safe** (stream, beam caps, RAM/VRAM governor). Large monoliths need `--chunk-lines` / explicit `--limit` / `--force`.

## Resource guards (all engines)

| Flag | Default | Effect |
|---|---|---|
| `--ram-budget-pct` | 50 | Stop when free RAM is too low |
| `--vram-budget-mb` | 4096 | Cap GPU batch / neural allocator |
| `--chunk-lines` / `--chunk-bytes` | 0 | Rotate `-o` files |
| `--stream` | off | Line-flush for pipes |
| `--safe-default-limit` | off | Cap at 5M if `--limit` omitted |
| `--limit` / `--timeout` | 0 | Global caps |

## Model → command

| Family | Priority | Command | Notes |
|---|---|---|---|
| ResourceGovernor + stream | P0 | global flags + `emit` | Anti-OOM; stdout pipe |
| Async multi-engine merge | P0 | `pipeline FILE.yaml` | **CLI-wired (v2.0)** |
| Session checkpoint | P0 | `session list\|show\|resume` | **CLI-wired** |
| Mask cartesian (GPU-aware) | P1 | `maskgen`, `emit --engine mask` | Chunked; `--compute gpu` |
| Leet / case | P1 | `leet --gpu`, `leet-perm` | `compute_backend.expand_leet_batch` |
| OMEN / Markov | P1 | `markov generate`, `emit --engine markov` | Cost heap + `--beam-width` |
| PCFG | P1 | `pcfg generate`, `emit --engine pcfg` | Prob heap + `--zipf-s` |
| BR deep | P1 | `br-deep` | CPF/CNPJ/CEP + PT-BR vocab |
| REST API | P1 | `serve` | Extra `[api]` |
| PRINCE | P2 | `prince` | Combinatorial chains |
| Semantic / personal PCFG | P2 | `emit --engine semantic`, `strategy --run` | NAME/YEAR/PET from YAML |
| Bandit router (UCB1) | P3 | `bandit` | Arm pick via proxy reward |
| PBMP full / lite | P3 | `pbmp`, `strategy` | Weighted engine plan |
| Genetic / MAP-Elites | P3 | `evolve` | Population search |
| Graph / temporal / domain PCFG | P3–P4 | `graph-expand`, `temporal-model`, `domain-pcfg` | |
| Neural LSTM | P4 | `neural` + `[gpu]` extra | VRAM governor; not default |
| GAN / VAE / Transformer | P1–P2 modules | `pipeline` stages / `vae-interp` | Optional torch |
| TUI / PassLLM | open | — | Next cycle / P5 |

v2 commands require a current checkout: `python wlf.py --help` must list `pipeline`, `br-deep`, `serve`, etc. See [CHANGELOG.md](../CHANGELOG.md) and [CLI-REFERENCE.md](CLI-REFERENCE.md).

## Streaming first

```bash
# Ordered stream to stdout (no giant .txt)
python wlf.py --stream --limit 10000 emit --engine pcfg --model .model/pcfg_grammar.json

# Mask under governor
python wlf.py --compute gpu --vram-budget-mb 4096 maskgen --mask '?l?l?d?d' --limit 50000

# Profile plan + light run
python wlf.py strategy --profile-file target.yaml --run --output-wordlist /tmp/cands.lst
```

## GPU extras

```bash
pip install -r requirements-gpu.txt
# or: pip install wordlistxpl-forge[gpu]
python wlf.py --compute gpu leet password --gpu --max-results 256
```

Torch is **optional**. Without it, mask/leet fall back to CPU chunks.

## Quality under budget

```bash
python wlf.py --ram-budget-pct 80 --limit 10000 cover --corpus sample.lst
python wlf.py --safe-default-limit maskgen --mask '?l?l?l?d' -o /tmp/m.lst
python scripts/smoke_governor.py
```

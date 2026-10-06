# WordlistXPL-Forge — Models Deep Dive

> Version 2.0.0 — Technical reference for all generation engines.

---

## Classical engines

### Markov Chain (`markov_engine.py`)

**Algorithm:** Variable-order Markov model trained on character sequences.

- Order 1–6: `P(c_n | c_{n-1}, …, c_{n-k})`
- Positional n-gram tables for suffix boosting
- Score type: **COST** (lower = more probable)
- CPU only, no dependencies

**When to use:** Fast baseline generation, 100k–10M candidates/minute.

```bash
python wlf.py markov --order 3 --limit 1000000 -o markov3.txt
python wlf.py markov --order 5 --train data/rockyou.txt --limit 500000 -o markov5.txt
```

---

### PCFG (`pcfg_engine.py`)

**Algorithm:** Probabilistic Context-Free Grammar trained on password structure.

- Learns P(structure) × ∏ P(segment | type, length)
- Structures: A6D2S1 → 6 alpha + 2 digit + 1 special
- Score type: **LOGPROB**

**When to use:** When you have a reference corpus and want structure-faithful generation.

```bash
python wlf.py pcfg --train data/rockyou.txt --limit 500000 -o pcfg.txt
python wlf.py pcfg --model models/pcfg.json --limit 500000
```

---

### Semantic PCFG (`semantic_pcfg.py`)

Extends PCFG with semantic segment categories:
- `WORD` → dictionary words (by frequency)
- `NAME` → first/last names
- `DATE` → date patterns
- `BRAND` → brand/company tokens

```bash
python wlf.py emit --engine semantic --limit 200000 -o semantic.txt
```

---

### Domain PCFG (`domain_pcfg.py`)

Auto-trains a PCFG from sector vocabulary (corporate, healthcare, finance, gov, ecommerce, gaming).

```bash
python wlf.py domain-pcfg --sector corporate --limit 200000 -o corp_pcfg.txt
python wlf.py domain-pcfg --sector finance --corpus data/finance_corpus.txt
```

---

### PRINCE (`prince_engine.py`)

Password Research and Investigation of New Candidates Engine.

- Generates all ordered combinations of word-chain segments from a wordlist
- Equivalent to PRINCE-style chain expansion

```bash
python wlf.py prince --wordlist words.txt --limit 500000 -o prince.txt
```

---

## Neural engines

All neural engines:
1. Call `_require_torch()` at generation time
2. Fall back to CPU heuristic if PyTorch unavailable
3. Accept `--model-path` to load a custom checkpoint
4. Emit `(password, score)` tuples

Install neural extras:
```bash
pip install wordlistxpl-forge[neural]
```

---

### GAN (`gan_engine.py`)

**Algorithm:** Generative Adversarial Network (PassGAN / GNPassGAN architecture).

- Generator: LSTM/Conv → discrete character vocabulary
- Discriminator: estimates probability of "real" password
- Score type: **PROB** (discriminator confidence)

**Compatible checkpoints:** PassGAN, GNPassGAN, custom

```bash
python wlf.py neural gan --limit 200000 -o gan.txt
python wlf.py neural gan --model-path models/passgan.pt --limit 500000
```

---

### VAE (`vae_engine.py`)

**Algorithm:** Variational Autoencoder — encodes passwords to latent `(μ, σ)`, samples around anchors.

- Encode → decode pipeline
- Interpolation between two passwords in latent space
- Score type: **LOGLIK**

```bash
python wlf.py neural vae --limit 200000 -o vae.txt
python wlf.py neural vae --anchor "Admin2024!" --anchor-sigma 0.5 --limit 100000
python wlf.py vae-interp "Admin2024!" "admin@2026" --steps 20 -o interp.txt
```

---

### Transformer (`transformer_engine.py`)

**Algorithm:** Autoregressive transformer (GPT-style), left-to-right generation.

- Compatible with PassGPT checkpoint (`javirandor/passgpt-10characters`)
- Supports hashcat-style pattern conditioning: `--pattern "?u?l?l?d?d?s"`
- Score type: **LOGPROB**

```bash
python wlf.py neural transformer --limit 200000 -o transformer.txt
python wlf.py neural transformer --prefix "Admin" --limit 100000
python wlf.py neural transformer --pattern "?u?l?l?d?d?s" --limit 50000
```

---

### Diffusion (`diffusion_engine.py`)

**Algorithm:** DDPM with cosine schedule over discrete character vocabulary.

- Denoising: Gaussian noise → iterative denoising → character sequence
- Classifier-free guidance for structure conditioning
- Score type: **PROB**

```bash
python wlf.py neural diffusion --limit 100000 -o diffusion.txt
python wlf.py neural diffusion --denoise-steps 50 --temperature 0.8
```

---

### Masked LM (`masked_lm_engine.py`)

**Algorithm:** BERT-style bidirectional masked language model.

- `fill` mode: fill `?`-masked positions in a template
- `sample` mode: iterative mask → fill → remask → refill
- `guided` mode: per-position charset class constraints

Compatible with PGMaP checkpoints.

```bash
# Fill template
python wlf.py neural masked-lm fill "Admin????@2026!" --limit 50000

# Iterative sampling
python wlf.py neural masked-lm --limit 200000 --iterations 5 -o mlm.txt
```

---

### TCN (`tcn_engine.py`)

**Algorithm:** Temporal Convolutional Network — causal dilated convolutions.

- Receptive field: `(kernel-1) × 2^n_layers` characters
- Residual connections + dropout
- Parallel training (no sequential dependency)
- Score type: **PROB**

```bash
python wlf.py neural tcn --limit 200000 -o tcn.txt
python wlf.py neural tcn --model-path models/tcn.pt --temperature 0.9
```

---

### Normalizing Flow (`flow_engine.py`)

**Algorithm:** Real-NVP coupling layers — invertible mapping between Gaussian prior and password space.

- Exact log-likelihood computation
- Efficient sampling via inverse pass
- Score type: **LOGLIK**

```bash
python wlf.py neural flow --limit 100000 -o flow.txt
```

---

## Evolutionary engines

### MAP-Elites (`map_elites.py`)

**Algorithm:** Quality-diversity MAP-Elites over a 3D behaviour space:
- Dimension 1: password length (6–20)
- Dimension 2: charset diversity (0–4 classes)
- Dimension 3: entropy band (low/medium/high/very_high)

Grid shape: 15 × 5 × 4 = 300 cells. Maintains one elite per cell.

Mutation operators: substitution, insertion, deletion, leet, capitalise, append_year, append_special.
Crossover: uniform (50%) or two-point.

```bash
python wlf.py evolve --mode map-elites --limit 200000 -o map_elites.txt
python wlf.py evolve --mode map-elites --seed-file rockyou_top10k.txt --limit 500000
```

---

### Genetic Algorithm (`genetic_engine.py`)

**Algorithm:** Tournament selection + crossover + mutation.

- Tournament size: k=3
- Elitism: top-20 survive unchanged each generation
- Population: 500 individuals
- Multi-objective support (fitness + diversity)

```bash
python wlf.py evolve --mode genetic --limit 200000 -o genetic.txt
python wlf.py evolve --mode genetic --seed-file seeds.txt --limit 500000
```

---

## Brazilian Deep Engine (`br_deep_engine.py`)

Specialized for Brazilian targets:

| Token type | Examples |
|-----------|---------|
| Names | Ana, Carlos, Eduardo, Fernanda |
| Gírias | trampo, mano, saudades, vacilão |
| Banks | itau, bradesco, nubank, caixa, bb |
| Telecoms | vivo, tim, claro, oi |
| Govt patterns | inss, receita, cpf, cnpj, pix |
| CEP regions | cep_01 (SP), cep_20 (RJ), cep_40 (BA) |
| CPF patterns* | structural patterns only — no valid real CPFs |
| Special dates | carnaval, copas, datas_nacionais |

> *CPF/CNPJ patterns do NOT generate real valid numbers. They generate structural patterns (###.###.###-##) for testing password policy, not document validation.

```bash
python wlf.py br-deep --sector corporate --limit 500000 -o br_corp.txt
python wlf.py br-deep --profile-file alvo.json --no-cpf --limit 200000
```

---

## Temporal Drift Engine (`temporal_drift.py`)

Models how passwords evolve from 2019→2026:

1. **Year increment**: `senha2020` → `senha2021` → ... → `senha2026`
2. **Leet escalation**: `admin` → `@dmin` → `@dm1n` → `@dm!n`
3. **Seasonal tokens**: `covid`, `vacina`, `copa2022`, `lula`, `chatgpt`, `ia2026`
4. **Complexity creep**: `empresa` → `Empresa123!` → `Empr3s@2026`

```bash
python wlf.py temporal-model --seed-file seeds.txt \
  --base-year 2019 --target-year 2026 \
  --limit 200000 -o temporal.txt
```

---

## Password Graph (`password_graph.py`)

Builds a co-occurrence graph from a corpus:
- **Nodes:** character n-grams, structural segments
- **Edges:** co-occurrence weight within the same password
- **Ranking:** PageRank over edge weights

Generation: random walk → concatenate path → filter by length.

```bash
python wlf.py graph-expand rockyou_top100k.txt --limit 200000 -o graph.txt
```

---

## Bayesian Full Engine (`bayesian_full.py`)

TarGuess-style demographic-informed Bayesian PCFG:

- **Prior:** `Dirichlet(α)` over grammar non-terminals
- **Likelihood:** `P(password | grammar) = P(structure) × ∏ P(segment)`
- **Posterior:** Dirichlet pseudo-count update as evidence arrives
- **Context weighting:** profile tokens (name, dates, keywords) get extra weight

```bash
python wlf.py emit --engine bayesian --profile-file alvo.json --limit 200000
```

---

## PBMP — Full Controller (`pbmp_full.py`)

**P(Strategy_{t+1} | History, Context, Behavior, Population)**

Online linear policy gradient model. Selects which engine to run next based on:
- Context features (profile, sector)
- History features (last coverage_delta, entropy_gain)
- Population features (charset distribution, total generated)

Reward = `coverage_delta` (fraction of structurally new candidates).

```bash
python wlf.py pbmp --profile-file alvo.json --n-engines 5
```

---

## RL Router (`rl_router.py`)

Actor-Critic router extending UCB1 BanditRouter.

- **State:** context + recent rewards + arm stats (8+5+n×3 features)
- **Policy:** 2-layer MLP softmax over arms
- **Value:** 2-layer MLP scalar baseline
- **Training:** online A2C, one gradient step per arm pull
- **Warm-up:** first 30 steps use UCB1, then switches to neural policy

---

## Pipeline DSL (`pipeline_dsl.py`)

YAML-defined multi-engine pipeline. All engines run in parallel threads,
merged via priority queue (by score), deduped via Bloom filter.

```yaml
output: out/result.txt
limit: 1000000
threads: 4
engines:
  - name: markov
    weight: 0.3
    limit: 300000
    params:
      order: 3
  - name: br_deep
    weight: 0.2
    limit: 200000
    params:
      sector: corporate
```

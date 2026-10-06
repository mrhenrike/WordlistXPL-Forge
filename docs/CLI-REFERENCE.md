# WordlistXPL-Forge — CLI Reference

> Version 2.0.0 — Complete command reference with parameters and examples.

**AUTHORIZED USE ONLY** — For systems you own or have explicit written permission to test.

---

## Global options

These options apply to all subcommands:

```
-o, --output FILE          Output file (default: stdout)
--limit N                  Maximum lines to generate (default: 0 = unlimited)
--timeout SECONDS          Stop after N seconds
--threads N                Worker threads (default: auto)
--compute {auto,cpu,gpu}   Compute backend (default: auto)
--ram-budget-pct FLOAT     RAM usage budget percent (default: 50)
--vram-budget-mb INT       VRAM budget in MiB (default: 4096)
--chunk-lines N            Rotate output chunk every N lines
--chunk-bytes N            Rotate output chunk every N bytes
--stream                   Enable streaming mode (no buffering)
--min-len N                Minimum password length filter
--max-len N                Maximum password length filter
-v, --verbose              Verbose output
--version                  Show version and exit
```

---

## Commands

### charset

Generate all combinations from a character set.

```
python wlf.py charset MIN_LEN MAX_LEN CHARS [options]

Arguments:
  MIN_LEN    Minimum length
  MAX_LEN    Maximum length
  CHARS      Character set string (e.g. "abc123!@")

Options:
  --create-charset FILE    Save charset definition to file

Examples:
  python wlf.py charset 6 8 "abcdefghijklmnopqrstuvwxyz0123456789"
  python wlf.py charset 8 8 "abc123" --limit 1000000 -o out.txt
```

---

### pattern

Generate from a pattern template.

```
python wlf.py pattern [options]

Options:
  -t, --template TMPL      Pattern template string
  --vars KEY=VAL ...       Variable definitions
  -i, --interactive        Interactive pattern builder

Template tokens:
  X         uppercase letter
  x         lowercase letter
  d         digit
  {cod}     variable substitution
  ?u        uppercase (hashcat style)
  ?l        lowercase
  ?d        digit
  ?s        special char

Examples:
  python wlf.py pattern -t "XX{cod}@corp.com" --vars cod=1200-1350
  python wlf.py pattern -t "Admin?d?d?d?s" --limit 50000
```

---

### profile

Interactive personal profiling → tailored wordlist.

```
python wlf.py profile [options]

Options:
  --name NAME              Target full name
  --nick NICK              Nickname
  --birthdate DATE         Birthday (YYYYMMDD or DD/MM/YYYY)
  --partner NAME           Partner name
  --pets NAMES             Pet names (comma-separated)
  --company NAME           Company/employer
  --keywords WORDS         Extra keywords (comma-separated)
  --depth {1,2,3,4,5}      Generation depth (default: 3)

Examples:
  python wlf.py profile
  python wlf.py profile --name "Maria Santos" --birthdate 19901205 \
    --company Acme --depth 4 -o maria.txt
```

---

### corp

Corporate profile → employee/service wordlist.

```
python wlf.py corp [options]

Options:
  --domain DOMAIN          Company domain
  --company NAME           Company name
  --year INT               Reference year
  --prefix PREFIX          Username prefix pattern
  --dept DEPT              Department

Examples:
  python wlf.py corp --domain acme.com --company "Acme Corp" -o corp.txt
```

---

### br-deep

Brazilian deep profile generation.

```
python wlf.py br-deep [options]

Options:
  --profile-file FILE      JSON profile file
  --sector SECTOR          Sector: corporate, finance, gov, healthcare, ecommerce
  --no-cpf                 Skip CPF structural patterns
  --no-cnpj                Skip CNPJ structural patterns
  --no-cep                 Skip CEP region tokens
  --cep-prefix XX          Focus on specific CEP prefix (e.g. 01 for SP capital)

Examples:
  python wlf.py br-deep --sector corporate --limit 500000 -o br_corp.txt
  python wlf.py br-deep --profile-file alvo.json --no-cpf -o br_alvo.txt
```

---

### emit

Multi-engine wordlist emission.

```
python wlf.py emit [options]

Options:
  --engine ENGINE          Engine name (markov, pcfg, semantic, neural, gan, etc.)
  --model-path PATH        Path to model checkpoint
  --profile-file FILE      JSON profile for context-aware engines
  --temperature FLOAT      Sampling temperature (default: 1.0)
  --min-len N              Minimum candidate length
  --max-len N              Maximum candidate length

Examples:
  python wlf.py emit --engine markov --limit 1000000 -o markov.txt
  python wlf.py emit --engine gan --compute gpu --limit 500000 -o gan.txt
  python wlf.py emit --engine bayesian --profile-file alvo.json --limit 200000
```

---

### pipeline

Run a YAML multi-engine pipeline.

```
python wlf.py pipeline PIPELINE_FILE [options]

Arguments:
  PIPELINE_FILE    Path to pipeline YAML file

Examples:
  python wlf.py pipeline my_pipeline.yaml
  python wlf.py pipeline my_pipeline.yaml --limit 500000 -o out.txt
```

---

### session

Manage generation sessions.

```
python wlf.py session {list,show,resume} [SESSION_ID]

Subcommands:
  list                     List all saved sessions
  show SESSION_ID          Show session details
  resume SESSION_ID        Resume a session (merges state into context)

Examples:
  python wlf.py session list
  python wlf.py session resume abc123def
```

---

### score / explain

Explain and score a candidate password.

```
python wlf.py score PASSWORD
python wlf.py explain PASSWORD

Examples:
  python wlf.py score "Admin2024!"
  python wlf.py explain "P@ssw0rd"
```

**Sample output:**
```
Candidate : 'Admin2024!'
Engine    : heuristic
Score     : raw=0.0000  normalized=0.7250
Structure : U1L4D4S1
Length    : 10
Entropy   : 3.32 bits/char
Strength  : medium
Charset   : 62 chars (upper, lower, digit, special)
Notes     : matches common pattern U+L+D+S
```

---

### evolve

Evolutionary generation (genetic or MAP-Elites).

```
python wlf.py evolve [options]

Options:
  --mode {genetic,map-elites}   Algorithm (default: genetic)
  --seed-file FILE              Seed wordlist to initialize population
  --population-size N           GA population size (default: 500)
  --generations N               Warmup generations (default: 20)

Examples:
  python wlf.py evolve --mode map-elites --limit 200000 -o map_elites.txt
  python wlf.py evolve --mode genetic --seed-file rockyou_1k.txt --limit 200000
```

---

### pbmp

Show PBMP strategy distribution.

```
python wlf.py pbmp [options]

Options:
  --profile-file FILE      JSON profile for context features
  --n-engines N            Number of top strategies to show (default: 5)

Examples:
  python wlf.py pbmp --n-engines 8
  python wlf.py pbmp --profile-file alvo.json
```

---

### temporal-model

Temporal drift generation across years.

```
python wlf.py temporal-model [options]

Options:
  --seed-file FILE         Seed word list
  --base-year INT          Start year (default: 2019)
  --target-year INT        End year (default: 2026)
  --leet-level {0,1,2,3}   Max leet substitution level (default: 2)

Examples:
  python wlf.py temporal-model --seed-file seeds.txt \
    --base-year 2020 --target-year 2026 --limit 100000 -o temporal.txt
```

---

### graph-expand

Graph-based expansion from a corpus.

```
python wlf.py graph-expand CORPUS_FILE [options]

Options:
  --walk-length N          Random walk steps (default: 4)
  --ngrams N,M,...         N-gram sizes (default: 2,3,4)

Examples:
  python wlf.py graph-expand rockyou_100k.txt --limit 200000 -o graph.txt
```

---

### domain-pcfg

Domain-specific PCFG generation.

```
python wlf.py domain-pcfg [options]

Options:
  --sector SECTOR          Sector: corporate, healthcare, education,
                           finance, gov, ecommerce, gaming
  --corpus-file FILE       Extra training corpus
  --save-model FILE        Save trained model to JSON

Examples:
  python wlf.py domain-pcfg --sector finance --limit 200000 -o finance.txt
  python wlf.py domain-pcfg --sector gov --corpus-file gov_words.txt
```

---

### vae-interp

VAE latent space interpolation.

```
python wlf.py vae-interp PW_FROM PW_TO [options]

Options:
  --steps N                Interpolation steps (default: 10)
  --model-path PATH        VAE checkpoint path

Examples:
  python wlf.py vae-interp "senha123" "S3nh@2026!" --steps 20 -o interp.txt
```

---

### plugin

Plugin management.

```
python wlf.py plugin {list,run} [options]

Subcommands:
  list                     List discovered plugins
  run NAME                 Run plugin by name

Examples:
  python wlf.py plugin list
  python wlf.py plugin run my_engine --limit 10000 -o out.txt
```

---

### serve

Start the REST API server.

```
python wlf.py serve [options]

Options:
  --host HOST              Bind host (default: 127.0.0.1)
  --port PORT              Bind port (default: 8771)
  --api-key KEY            API key (default: no auth)

Examples:
  python wlf.py serve
  python wlf.py serve --host 0.0.0.0 --port 8771 --api-key secretkey
```

**API endpoints:**
```
GET  /v1/status            Server health
GET  /v1/engines           List engines
GET  /v1/docs              Swagger UI
POST /v1/generate          Stream wordlist (NDJSON)
GET  /v1/sessions          List sessions
POST /v1/sessions/{id}/resume  Resume session
```

---

### analyze

Statistical analysis of an existing wordlist.

```
python wlf.py analyze WORDLIST [options]

Options:
  --format {table,markdown,json}   Output format
  --top-n N                        Show top N patterns (default: 20)

Examples:
  python wlf.py analyze rockyou.txt --format markdown
  python wlf.py analyze out.lst --top-n 50 --format json
```

---

### merge

Merge and deduplicate wordlists.

```
python wlf.py merge FILE1 FILE2 ... [options]

Options:
  --sort {alpha,frequency,length,random}  Sort order
  --unique                                Remove duplicates

Examples:
  python wlf.py merge list1.txt list2.txt --sort frequency -o merged.txt
```

---

### mangle

Apply Hashcat-style mangling rules to a wordlist.

```
python wlf.py mangle WORDLIST [options]

Options:
  --rules RULES_FILE       Custom rules file
  --preset {best64,dive,t0XlC}  Use preset rules

Examples:
  python wlf.py mangle wordlist.txt --preset best64 -o mangled.txt
  python wlf.py mangle wordlist.txt --rules my.rules -o out.txt
```

---

### leet

Leet speak transformation.

```
python wlf.py leet WORD [options]

Options:
  -m, --mode {basic,medium,advanced,all}   Substitution level

Examples:
  python wlf.py leet password -m advanced
  python wlf.py leet senha -m all -o leet_senha.txt
```

---

### neural

Neural model subcommands.

```
python wlf.py neural {lstm,gan,vae,transformer,diffusion,masked-lm,tcn,flow} [options]

Options:
  --model-path PATH        Checkpoint file
  --temperature FLOAT      Sampling temperature (default: 1.0)
  --prefix STRING          Prefix conditioning (transformer only)
  --pattern MASK           Hashcat mask conditioning (transformer only)
  --anchor PASSWORD        Anchor password (VAE only)
  --anchor-sigma FLOAT     Latent sigma (VAE only)
  --fill-template TMPL     Fill template (masked-lm only, ? = mask)

Examples:
  python wlf.py neural gan --limit 200000 -o gan.txt
  python wlf.py neural transformer --prefix "Admin" --limit 100000
  python wlf.py neural vae --anchor "password123" --limit 50000
  python wlf.py neural masked-lm fill "Admin????@2025!" --limit 50000
```

---

### strategy

Show strategy plan for a profile.

```
python wlf.py strategy [options]

Options:
  --profile-file FILE      JSON profile
  --depth INT              Analysis depth

Examples:
  python wlf.py strategy --profile-file alvo.json
```

---

### strength

Estimate password strength / entropy.

```
python wlf.py strength PASSWORD

Examples:
  python wlf.py strength "Admin2024!"
  python wlf.py strength "P@ssw0rd"
```

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (bad arguments) |
| 2 | Engine error |
| 3 | Resource limit hit (RAM/VRAM) |
| 130 | Interrupted (Ctrl+C) |

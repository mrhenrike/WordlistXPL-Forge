# `neural`

Character-level neural password generation (optional [neural] extra).

## Syntax

```text
 __          _______ _    _         
 \ \        / /  ____| |  | |        
  \ \  /\  / /| |__  | |__| |       
   \ \/  \/ / |  __| |  __  |       
    \  /\  /  | |    | |  | |       
     \/  \/   |_|    |_|  |_|       

  WordlistXPL-Forge  v1.0.0
  Author: André Henrique (@mrhenrike)
  Unified wordlist generation for pentest & red team

usage: wlf.py neural [-h] [--wordlist FILE [FILE ...]] [--model PATH]
                     [--epochs EPOCHS] [--batch-size BATCH_SIZE]
                     [--embed EMBED] [--hidden HIDDEN] [--layers LAYERS]
                     [--max-lines MAX_LINES] [--count COUNT]
                     [--temperature TEMPERATURE] [--prefix PREFIX]
                     [--mask MASK] [--max-len MAX_LEN] [--adapt FILE]
                     [--dpg-steps DPG_STEPS] [--adapter {passgpt,hf}]
                     [--no-dedupe] [--seed SEED] [-o OUTPUT]
                     [{train,generate}]

Character-level neural password generation (FLA/PassGPT style).
Requires the optional extra: pip install wordlistxpl-forge[neural].
Supports temperature sampling, guided generation with a prefix or
mask, Dynamic Password Guessing, and external PassGPT adapters.

Examples:
  wlf.py neural train --wordlist rockyou.txt --epochs 5
  wlf.py --limit 100000 neural generate --temperature 0.9 -o out.lst
  wlf.py --limit 5000 neural generate --prefix admin --mask '?u?l?l?l?d?d'
  wlf.py --limit 100000 neural generate --adapt cracked.txt
  wlf.py --limit 5000 neural generate --adapter passgpt --model javirandor/passgpt-10characters

positional arguments:
  {train,generate}      Action (default: generate)

options:
  -h, --help            show this help message and exit
  --wordlist FILE [FILE ...]
                        Training file(s) (train mode)
  --model PATH          Model path (.pt) or adapter model name
  --epochs EPOCHS       Training epochs
  --batch-size BATCH_SIZE
                        Training batch size
  --embed EMBED         Embedding dim
  --hidden HIDDEN       LSTM hidden size
  --layers LAYERS       LSTM layers
  --max-lines MAX_LINES
                        Max training lines (0 = all)
  --count COUNT         Candidates to generate (generate mode)
  --temperature TEMPERATURE
                        Sampling temperature (default: 1.0)
  --prefix PREFIX       Guided prefix
  --mask MASK           Guided hashcat-style mask
  --max-len MAX_LEN     Max candidate length (default: 32)
  --adapt FILE          Recovered passwords for Dynamic Password Guessing
  --dpg-steps DPG_STEPS
                        DPG adaptation steps (default: 200)
  --adapter {passgpt,hf}
                        Use an external HuggingFace causal LM adapter
  --no-dedupe           Allow duplicate candidates
  --seed SEED           RNG seed (0 = nondeterministic)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `neural_action` | 'generate' | no | Action (default: generate) |
| `--wordlist` | - | no | Training file(s) (train mode) |
| `--model` | '.model/neural_lstm.pt' | no | Model path (.pt) or adapter model name |
| `--epochs` | 5 | no | Training epochs |
| `--batch-size` | 256 | no | Training batch size |
| `--embed` | 64 | no | Embedding dim |
| `--hidden` | 256 | no | LSTM hidden size |
| `--layers` | 2 | no | LSTM layers |
| `--max-lines` | 0 | no | Max training lines (0 = all) |
| `--count` | 10000 | no | Candidates to generate (generate mode) |
| `--temperature` | 1.0 | no | Sampling temperature (default: 1.0) |
| `--prefix` | '' | no | Guided prefix |
| `--mask` | '' | no | Guided hashcat-style mask |
| `--max-len` | 32 | no | Max candidate length (default: 32) |
| `--adapt` | - | no | Recovered passwords for Dynamic Password Guessing |
| `--dpg-steps` | 200 | no | DPG adaptation steps (default: 200) |
| `--adapter` | - | no | Use an external HuggingFace causal LM adapter |
| `--no-dedupe` | False | no | Allow duplicate candidates |
| `--seed` | 0 | no | RNG seed (0 = nondeterministic) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf neural --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

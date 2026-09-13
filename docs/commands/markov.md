# `markov`

Positional Markov chain password generator (OMEN-style).

## Syntax

```text
__          _______ _    _         
 \ \        / /  ____| |  | |        
  \ \  /\  / /| |__  | |__| |       
   \ \/  \/ / |  __| |  __  |       
    \  /\  /  | |    | |  | |       
     \/  \/   |_|    |_|  |_|       

  WordlistXPL-Forge  v1.2.0
  Author: André Henrique (@mrhenrike)
  Unified wordlist generation for pentest & red team

usage: wlf.py markov [-h] [--wordlist FILE [FILE ...]] [--model FILE]
                     [--model-output FILE] [--order ORDER]
                     [--smoothing SMOOTHING] [--max-lines MAX_LINES]
                     [--max-cost MAX_COST] [--min-len MIN_LEN]
                     [--max-len MAX_LEN] [--limit LIMIT] [-o OUTPUT]
                     [{train,generate}]

Positional Markov chain password generator (OMEN-style).
Learns character transition probabilities per position and
generates candidates in ascending cost order.

Examples:
  wlf.py markov train --wordlist rockyou.txt --order 4
  wlf.py markov generate --limit 500000
  wlf.py markov generate --min-len 8 --max-len 12 --max-cost 30

positional arguments:
  {train,generate}      Action: train or generate (default: generate)

options:
  -h, --help            show this help message and exit
  --wordlist FILE [FILE ...]
                        Training file(s)
  --model FILE          Model file (default: .model/markov_model.json)
  --model-output FILE   Output path for trained model
  --order ORDER         N-gram order (default: 3)
  --smoothing SMOOTHING
                        Laplace smoothing alpha for unseen n-grams (default:
                        0.01)
  --max-lines MAX_LINES
                        Max training lines (0 = unlimited)
  --max-cost MAX_COST   Max total cost threshold (0 = no limit)
  --min-len MIN_LEN     Min password length (default: 4)
  --max-len MAX_LEN     Max password length (default: 16)
  --limit LIMIT         Max candidates (0 = unlimited)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `markov_action` | 'generate' | no | Action: train or generate (default: generate) |
| `--wordlist` | - | no | Training file(s) |
| `--model` | '.model/markov_model.json' | no | Model file (default: .model/markov_model.json) |
| `--model-output` | - | no | Output path for trained model |
| `--order` | 3 | no | N-gram order (default: 3) |
| `--smoothing` | 0.01 | no | Laplace smoothing alpha for unseen n-grams (default: 0.01) |
| `--max-lines` | 0 | no | Max training lines (0 = unlimited) |
| `--max-cost` | 0 | no | Max total cost threshold (0 = no limit) |
| `--min-len` | 4 | no | Min password length (default: 4) |
| `--max-len` | 16 | no | Max password length (default: 16) |
| `--limit` | 0 | no | Max candidates (0 = unlimited) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf markov --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


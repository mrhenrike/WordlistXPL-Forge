# `maya-rank`

maya-rank

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

usage: wlf.py maya-rank [-h] [-o OUTPUT] [--top TOP]
                        [--backend {auto,torch,fallback}] [--use-gpu]
                        [--min-score MIN_SCORE]
                        wordlist

positional arguments:
  wordlist              Wordlist to rank

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Ranked output file
  --top TOP             Keep top N candidates (0=all)
  --backend {auto,torch,fallback}
  --use-gpu             Use GPU for torch backend (optional)
  --min-score MIN_SCORE
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Wordlist to rank |
| `-o, --output` | - | no | Ranked output file |
| `--top` | 0 | no | Keep top N candidates (0=all) |
| `--backend` | 'auto' | no |  |
| `--use-gpu` | False | no | Use GPU for torch backend (optional) |
| `--min-score` | 0.0 | no |  |

## Input combinations

- Minimum: `wlf maya-rank --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


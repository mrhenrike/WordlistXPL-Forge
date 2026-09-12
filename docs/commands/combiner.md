# `combiner`

Generate wordlists from keyword permutations with connectors.

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

usage: wlf.py combiner [-h] [--keywords-file FILE] [--connectors LIST]
                       [--tails LIST] [--depth DEPTH] [--abbreviation]
                       [--reverse] [--leet] [--lowercase] [--min-len MIN_LEN]
                       [--max-len MAX_LEN] [-o OUTPUT]
                       [keywords ...]

Generate wordlists from keyword permutations with connectors.

Examples:
  wlf.py combiner admin password secret
  wlf.py combiner admin test --connectors ',-,_,.,EMPTY' --leet --reverse
  wlf.py combiner --keywords-file keywords.txt --depth 3 --abbreviation
  wlf.py combiner brandx corp 2026 --tails '!,@,#,123' -o wordlist.lst

positional arguments:
  keywords              Keywords to combine

options:
  -h, --help            show this help message and exit
  --keywords-file FILE  File with one keyword per line
  --connectors LIST     Comma-separated connectors (use EMPTY for no
                        separator, default: EMPTY,-,_,.,@,#)
  --tails LIST          Comma-separated numeric/special tails to append
  --depth DEPTH         Max permutation depth (0 = all, default: 0)
  --abbreviation        Generate abbreviation variants
  --reverse             Generate reversed variants
  --leet                Generate leet speak variants
  --lowercase           Add lowercase duplicates
  --min-len MIN_LEN     Minimum output length (default: 1)
  --max-len MAX_LEN     Maximum output length (default: 64)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `keywords` | - | no | Keywords to combine |
| `--keywords-file` | - | no | File with one keyword per line |
| `--connectors` | - | no | Comma-separated connectors (use EMPTY for no separator, default: EMPTY,-,_,.,@,#) |
| `--tails` | - | no | Comma-separated numeric/special tails to append |
| `--depth` | 0 | no | Max permutation depth (0 = all, default: 0) |
| `--abbreviation` | False | no | Generate abbreviation variants |
| `--reverse` | False | no | Generate reversed variants |
| `--leet` | False | no | Generate leet speak variants |
| `--lowercase` | False | no | Add lowercase duplicates |
| `--min-len` | 1 | no | Minimum output length (default: 1) |
| `--max-len` | 64 | no | Maximum output length (default: 64) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf combiner --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


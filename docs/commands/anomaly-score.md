# `anomaly-score`

Score each password in a wordlist using a native ensemble of

## Syntax

```text
__          _______ _    _         
 \ \        / /  ____| |  | |        
  \ \  /\  / /| |__  | |__| |       
   \ \/  \/ / |  __| |  __  |       
    \  /\  /  | |    | |  | |       
     \/  \/   |_|    |_|  |_|       

  WordlistXPL-Forge  v1.1.0
  Author: André Henrique (@mrhenrike)
  Unified wordlist generation for pentest & red team

usage: wlf.py anomaly-score [-h] [--top N] [--max-lines MAX_LINES] [-o FILE]
                            WORDLIST

Score each password in a wordlist using a native ensemble of
IsolationForest-lite and HBOS-lite algorithms. No external
ML library required. Higher score = more anomalous.

Examples:
  wlf.py anomaly-score labs/labs_passwords.lst --top 50
  wlf.py anomaly-score leak.txt --top 100 -o rare.txt
  wlf.py anomaly-score corpus.lst --max-lines 200000

positional arguments:
  WORDLIST              Input wordlist file path

options:
  -h, --help            show this help message and exit
  --top N               Return only the top-N most anomalous entries (0 = all)
  --max-lines MAX_LINES
                        Maximum lines to read from wordlist (default: 100000)
  -o, --output FILE     Save scored password list to file (one per line, no
                        scores)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `WORDLIST` | - | yes | Input wordlist file path |
| `--top` | 0 | no | Return only the top-N most anomalous entries (0 = all) |
| `--max-lines` | 100000 | no | Maximum lines to read from wordlist (default: 100000) |
| `-o, --output` | - | no | Save scored password list to file (one per line, no scores) |

## Input combinations

- Minimum: `wlf anomaly-score --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


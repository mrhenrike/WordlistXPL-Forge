# `analyze`

analyze

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

usage: wlf.py analyze [-h] [--top TOP] [--masks] [--base-words]
                      [--base-output FILE] [--base-ranked] [--position-freq]
                      [--all-masks] [--mask-optindex] [--mask-csv FILE]
                      [--time-budget TIME_BUDGET] [--pps PPS] [--use-gpu]
                      [--format {text,json,csv,markdown}] [-o OUTPUT]
                      wordlist

positional arguments:
  wordlist              Wordlist to analyze

options:
  -h, --help            show this help message and exit
  --top TOP             Top N most frequent (default: 20)
  --masks               Include Hashcat mask analysis (?u?l?d?s frequency)
  --base-words          Extract base words (strip trailing digits/specials)
  --base-output FILE    Save base words to file
  --base-ranked         Show base words with frequency ranking (pipal parity)
  --position-freq       Show character frequency by position (pipal
                        Frequency_Checker)
  --all-masks           Show ALL masks (not just top N)
  --mask-optindex       PACK maskgen optindex ranking with time budget
  --mask-csv FILE       Export PACK-compatible mask CSV (requires --mask-
                        optindex)
  --time-budget TIME_BUDGET
                        Crack time budget hours for --mask-optindex
  --pps PPS             Passwords/sec for --mask-optindex (0=auto)
  --use-gpu             GPU PPS for --mask-optindex (optional)
  --format {text,json,csv,markdown}
                        Output format: text, json, csv, markdown (default:
                        text)
  -o, --output OUTPUT   Save report to file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Wordlist to analyze |
| `--top` | 20 | no | Top N most frequent (default: 20) |
| `--masks` | False | no | Include Hashcat mask analysis (?u?l?d?s frequency) |
| `--base-words` | False | no | Extract base words (strip trailing digits/specials) |
| `--base-output` | - | no | Save base words to file |
| `--base-ranked` | False | no | Show base words with frequency ranking (pipal parity) |
| `--position-freq` | False | no | Show character frequency by position (pipal Frequency_Checker) |
| `--all-masks` | False | no | Show ALL masks (not just top N) |
| `--mask-optindex` | False | no | PACK maskgen optindex ranking with time budget |
| `--mask-csv` | - | no | Export PACK-compatible mask CSV (requires --mask-optindex) |
| `--time-budget` | 1.0 | no | Crack time budget hours for --mask-optindex |
| `--pps` | 0 | no | Passwords/sec for --mask-optindex (0=auto) |
| `--use-gpu` | False | no | GPU PPS for --mask-optindex (optional) |
| `--format` | 'text' | no | Output format: text, json, csv, markdown (default: text) |
| `-o, --output` | - | no | Save report to file |

## Input combinations

- Minimum: `wlf analyze --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


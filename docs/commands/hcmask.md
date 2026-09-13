# `hcmask`

Export a hashcat .hcmask from a wordlist mask distribution.

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

usage: wlf.py hcmask [-h] --wordlist FILE [--top TOP] [--min-count MIN_COUNT]
                     [-o FILE]

Analyze the mask distribution of a wordlist and export a hashcat
.hcmask file (most frequent masks first).

Examples:
  wlf.py hcmask --wordlist leaked.txt -o masks.hcmask
  wlf.py hcmask --wordlist leaked.txt --top 50 --min-count 5 -o top.hcmask

options:
  -h, --help            show this help message and exit
  --wordlist FILE       Input wordlist
  --top TOP             Keep only the top N masks (0 = all)
  --min-count MIN_COUNT
                        Minimum occurrences to keep a mask (default: 1)
  -o, --output FILE     Output .hcmask file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--wordlist` | - | yes | Input wordlist |
| `--top` | 0 | no | Keep only the top N masks (0 = all) |
| `--min-count` | 1 | no | Minimum occurrences to keep a mask (default: 1) |
| `-o, --output` | - | no | Output .hcmask file |

## Input combinations

- Minimum: `wlf hcmask --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

# `merge`

merge

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

usage: wlf.py merge [-h] [--min-len MIN_LEN] [--max-len MAX_LEN]
                    [--no-numeric] [--filter FILTER] [--no-dedupe]
                    [--sort {alpha,length,random,frequency}] [-o OUTPUT]
                    files [files ...]

positional arguments:
  files                 Input wordlists

options:
  -h, --help            show this help message and exit
  --min-len MIN_LEN
  --max-len MAX_LEN
  --no-numeric          Remove purely numeric entries
  --filter FILTER       Include regex filter (only matches pass)
  --no-dedupe
  --sort {alpha,length,random,frequency}
                        Sort mode: alpha, length, random, or frequency (most
                        common first)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `files` | - | yes | Input wordlists |
| `--min-len` | 6 | no |  |
| `--max-len` | 128 | no |  |
| `--no-numeric` | False | no | Remove purely numeric entries |
| `--filter` | - | no | Include regex filter (only matches pass) |
| `--no-dedupe` | False | no |  |
| `--sort` | - | no | Sort mode: alpha, length, random, or frequency (most common first) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf merge --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


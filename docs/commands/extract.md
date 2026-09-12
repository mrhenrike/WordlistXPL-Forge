# `extract`

extract

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

usage: wlf.py extract [-h] [--min-len MIN_LEN] [--max-len MAX_LEN] [-o OUTPUT]
                      files [files ...]

positional arguments:
  files                Input files (max 50)

options:
  -h, --help           show this help message and exit
  --min-len MIN_LEN
  --max-len MAX_LEN
  -o, --output OUTPUT  Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `files` | - | yes | Input files (max 50) |
| `--min-len` | 4 | no |  |
| `--max-len` | 64 | no |  |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf extract --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


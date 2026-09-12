# `kwalk`

Generate passwords based on physical keyboard adjacency walks.

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

usage: wlf.py kwalk [-h] [--layout LAYOUT] [--min-len MIN_LEN]
                    [--max-len MAX_LEN] [--max-changes MAX_CHANGES]
                    [--directions LIST] [--no-shift] [--start-chars CHARS]
                    [--route START:DIRS] [--route-file FILE] [--list-layouts]
                    [--limit LIMIT] [-o OUTPUT]

Generate passwords based on physical keyboard adjacency walks.
Supports QWERTY, AZERTY, QWERTZ, Dvorak, and numpad layouts.

Examples:
  wlf.py kwalk --min-len 6 --max-len 10
  wlf.py kwalk --layout qwerty,numpad --no-shift
  wlf.py kwalk --max-changes 2 --start-chars qaz1
  wlf.py kwalk --list-layouts

options:
  -h, --help            show this help message and exit
  --layout LAYOUT       Comma-separated layout names (default: qwerty)
  --min-len MIN_LEN     Min walk length (default: 4)
  --max-len MAX_LEN     Max walk length (default: 10)
  --max-changes MAX_CHANGES
                        Max direction changes per walk (default: 3)
  --directions LIST     Comma-separated directions: N,S,E,W,NE,NW,SE,SW
  --no-shift            Exclude shifted layer (uppercase/symbols)
  --start-chars CHARS   Restrict starting characters
  --route START:DIRS    Explicit walk route, e.g. q:3467 or q,3467 (0-7 =
                        N..NW)
  --route-file FILE     Route file: one 'start dirs' per line (kwprocessor-
                        style)
  --list-layouts        List available keyboard layouts
  --limit LIMIT         Max candidates (0 = unlimited)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--layout` | 'qwerty' | no | Comma-separated layout names (default: qwerty) |
| `--min-len` | 4 | no | Min walk length (default: 4) |
| `--max-len` | 10 | no | Max walk length (default: 10) |
| `--max-changes` | 3 | no | Max direction changes per walk (default: 3) |
| `--directions` | - | no | Comma-separated directions: N,S,E,W,NE,NW,SE,SW |
| `--no-shift` | False | no | Exclude shifted layer (uppercase/symbols) |
| `--start-chars` | - | no | Restrict starting characters |
| `--route` | - | no | Explicit walk route, e.g. q:3467 or q,3467 (0-7 = N..NW) |
| `--route-file` | - | no | Route file: one 'start dirs' per line (kwprocessor-style) |
| `--list-layouts` | False | no | List available keyboard layouts |
| `--limit` | 0 | no | Max candidates (0 = unlimited) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf kwalk --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: timeout

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


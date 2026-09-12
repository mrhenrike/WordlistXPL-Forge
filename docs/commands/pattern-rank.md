# `pattern-rank`

Analyze a password wordlist for structural patterns:

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

usage: wlf.py pattern-rank [-h] [--layout LAYOUT] [--max-lines MAX_LINES]
                           wordlist

Analyze a password wordlist for structural patterns:
keyboard walks, PT-BR month names, top Hashcat masks.

Examples:
  wlf.py pattern-rank passwords.lst
  wlf.py pattern-rank leaked.txt --layout qwerty --max-lines 100000

positional arguments:
  wordlist              Wordlist to analyze

options:
  -h, --help            show this help message and exit
  --layout LAYOUT       Keyboard layout for walk detection (default: qwerty)
  --max-lines MAX_LINES
                        Max lines to analyze (default: 500000)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Wordlist to analyze |
| `--layout` | 'qwerty' | no | Keyboard layout for walk detection (default: qwerty) |
| `--max-lines` | 500000 | no | Max lines to analyze (default: 500000) |

## Input combinations

- Minimum: `wlf pattern-rank --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


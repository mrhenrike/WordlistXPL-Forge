# `rulegen`

Analyze real passwords to discover transformation rules

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

usage: wlf.py rulegen [-h] [--wordlist FILE [FILE ...]] [--dictionary FILE]
                      [--top-rules TOP_RULES] [--max-lines MAX_LINES]
                      [-o OUTPUT]

Analyze real passwords to discover transformation rules
and generate hashcat-compatible .rule files.

Examples:
  wlf.py rulegen --wordlist leaked.txt -o rules.rule
  wlf.py rulegen --wordlist passwords.lst --dictionary english.txt --top-rules 200
  wlf.py rulegen --wordlist hashes.pot --max-lines 100000

options:
  -h, --help            show this help message and exit
  --wordlist FILE [FILE ...]
                        Password file(s) to analyze
  --dictionary FILE     Optional base word dictionary for matching
  --top-rules TOP_RULES
                        Number of top rules to output (default: 100)
  --max-lines MAX_LINES
                        Max passwords to analyze (0 = all)
  -o, --output OUTPUT   Output file (.rule for hashcat format)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--wordlist` | - | no | Password file(s) to analyze |
| `--dictionary` | - | no | Optional base word dictionary for matching |
| `--top-rules` | 100 | no | Number of top rules to output (default: 100) |
| `--max-lines` | 0 | no | Max passwords to analyze (0 = all) |
| `-o, --output` | - | no | Output file (.rule for hashcat format) |

## Input combinations

- Minimum: `wlf rulegen --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


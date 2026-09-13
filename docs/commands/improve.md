# `improve`

improve

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

usage: wlf.py improve [-h] [-o OUTPUT] [--leet {basic,medium,aggressive}]
                      [--no-years] [--no-specials] [--year-start YEAR_START]
                      [--year-end YEAR_END] [--min-len MIN_LEN]
                      [--max-len MAX_LEN]
                      wordlist

positional arguments:
  wordlist              Source wordlist

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Output file
  --leet {basic,medium,aggressive}
  --no-years
  --no-specials
  --year-start YEAR_START
  --year-end YEAR_END
  --min-len MIN_LEN
  --max-len MAX_LEN
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Source wordlist |
| `-o, --output` | - | no | Output file |
| `--leet` | 'basic' | no |  |
| `--no-years` | False | no |  |
| `--no-specials` | False | no |  |
| `--year-start` | 2020 | no |  |
| `--year-end` | 2027 | no |  |
| `--min-len` | 6 | no |  |
| `--max-len` | 32 | no |  |

## Input combinations

- Minimum: `wlf improve --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


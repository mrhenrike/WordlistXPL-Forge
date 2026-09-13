# `leet`

leet

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

usage: wlf.py leet [-h] [-m {basic,medium,aggressive,custom}]
                   [--custom-map CUSTOM_MAP] [--max-results MAX_RESULTS]
                   [-o OUTPUT]
                   word

positional arguments:
  word                  Base word

options:
  -h, --help            show this help message and exit
  -m, --mode {basic,medium,aggressive,custom}
                        Leet substitution mode
  --custom-map CUSTOM_MAP
                        Custom mapping (e.g. a=@,4;t=7;s=$;l=1,|)
  --max-results MAX_RESULTS
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `word` | - | yes | Base word |
| `-m, --mode` | 'basic' | no | Leet substitution mode |
| `--custom-map` | '' | no | Custom mapping (e.g. a=@,4;t=7;s=$;l=1,\|) |
| `--max-results` | 10000 | no |  |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf leet --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


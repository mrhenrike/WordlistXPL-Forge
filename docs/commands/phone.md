# `phone`

phone

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

usage: wlf.py phone [-h] [--country COUNTRY] [--state STATE] [--ddi DDI]
                    [--ddd DDD] [--type {mobile,landline,both}]
                    [--pattern PATTERN] [--formats FORMATS] [--suffix SUFFIX]
                    [--prefix-file FILE] [--digit-length N] [-o OUTPUT]

options:
  -h, --help            show this help message and exit
  --country COUNTRY     Country name (e.g. brazil, usa, uk)
  --state STATE         State/region code (e.g. SP, NY)
  --ddi DDI             Manual DDI override (e.g. 55)
  --ddd DDD             Manual DDD/area code override (e.g. 11)
  --type {mobile,landline,both}
                        Phone type to generate
  --pattern PATTERN     Custom digit pattern (X=any digit, e.g. '9XXXX-XXXX')
  --formats FORMATS     Output formats: e164,local,bare (comma-sep, default:
                        e164,local)
  --suffix SUFFIX       Append suffix to each generated number (pnwgen parity)
  --prefix-file FILE    File with one prefix per line (pnwgen multi-prefix
                        mode)
  --digit-length N      Override digit count for brute-force (4-10, pnwgen
                        parity)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--country` | - | no | Country name (e.g. brazil, usa, uk) |
| `--state` | - | no | State/region code (e.g. SP, NY) |
| `--ddi` | - | no | Manual DDI override (e.g. 55) |
| `--ddd` | - | no | Manual DDD/area code override (e.g. 11) |
| `--type` | 'both' | no | Phone type to generate |
| `--pattern` | - | no | Custom digit pattern (X=any digit, e.g. '9XXXX-XXXX') |
| `--formats` | 'e164,local' | no | Output formats: e164,local,bare (comma-sep, default: e164,local) |
| `--suffix` | - | no | Append suffix to each generated number (pnwgen parity) |
| `--prefix-file` | - | no | File with one prefix per line (pnwgen multi-prefix mode) |
| `--digit-length` | - | no | Override digit count for brute-force (4-10, pnwgen parity) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf phone --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 1

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


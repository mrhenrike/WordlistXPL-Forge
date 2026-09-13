# `cupp`

Generate password candidates from a personal profile

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

usage: wlf.py cupp [-h] [--first-name FIRST_NAME] [--last-name LAST_NAME]
                   [--nick NICK] [--birth BIRTH] [--pet PET]
                   [--company COMPANY] [--words WORD [WORD ...]]
                   [--max-output MAX_OUTPUT] [-o OUTPUT]

Generate password candidates from a personal profile
(names, dates, pets, company, custom words).

Examples:
  wlf.py cupp --first-name PessoaX --last-name CorpX --company BrandX -o out.lst
  wlf.py cupp --nick robotx --birth 01/1990 --words petx robotx --max-output 50000

options:
  -h, --help            show this help message and exit
  --first-name FIRST_NAME
                        Target first name
  --last-name LAST_NAME
                        Target last name
  --nick NICK           Nickname or handle
  --birth BIRTH         Birth date
  --pet PET             Pet name
  --company COMPANY     Company name
  --words WORD [WORD ...]
                        Extra words
  --max-output MAX_OUTPUT
                        Max candidates (0 = unlimited)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--first-name` | - | no | Target first name |
| `--last-name` | - | no | Target last name |
| `--nick` | - | no | Nickname or handle |
| `--birth` | - | no | Birth date |
| `--pet` | - | no | Pet name |
| `--company` | - | no | Company name |
| `--words` | - | no | Extra words |
| `--max-output` | 0 | no | Max candidates (0 = unlimited) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf cupp --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


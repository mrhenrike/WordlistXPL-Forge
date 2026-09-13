# `osint-perm`

Generate password candidates from OSINT profile fields

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

usage: wlf.py osint-perm [-h] [--first-name FIRST_NAME]
                         [--last-name LAST_NAME] [--nick NICK] [--birth BIRTH]
                         [--pet PET] [--phone PHONE] [--complexity 0-5]
                         [--keywords WORD [WORD ...]] [-o OUTPUT]

Generate password candidates from OSINT profile fields
(name, nickname, birth date, pet, phone, keywords).

Examples:
  wlf.py osint-perm --first-name PessoaX --last-name CorpX -o out.lst
  wlf.py osint-perm --nick robotx --birth 01/1990 --complexity 2 -o out.lst

options:
  -h, --help            show this help message and exit
  --first-name FIRST_NAME
                        Target first name
  --last-name LAST_NAME
                        Target last name
  --nick NICK           Nickname or handle
  --birth BIRTH         Birth date (DD/MM/YYYY or MM/YYYY)
  --pet PET             Pet name
  --phone PHONE         Phone number
  --complexity 0-5      Permutation depth (default: 1)
  --keywords WORD [WORD ...]
                        Extra keywords
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--first-name` | - | no | Target first name |
| `--last-name` | - | no | Target last name |
| `--nick` | - | no | Nickname or handle |
| `--birth` | - | no | Birth date (DD/MM/YYYY or MM/YYYY) |
| `--pet` | - | no | Pet name |
| `--phone` | - | no | Phone number |
| `--complexity` | 1 | no | Permutation depth (default: 1) |
| `--keywords` | - | no | Extra keywords |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf osint-perm --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


# `corp-prefixes`

Generate username variations with department, role, and functional prefixes.

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

usage: wlf.py corp-prefixes [-h] [--names NAME1,NAME2] [--file FILE]
                            [--domain DOMAIN] [--no-at] [--prefixes pfx1,pfx2]
                            [--categories cat1,cat2] [--sector SECTOR]
                            [--separators SEP] [--no-numeric]
                            [--list-prefixes] [--config FILE] [-o OUTPUT]

Generate username variations with department, role, and functional prefixes.

All patterns loaded from data/corp_prefix_patterns.json - no hardcoded data.
No real company names ever stored or generated.

Prefix categories:
  department  - ti, helpdesk, adm, rh, fin, seg, dev, redes, ...
  role        - svc, admin, ger, dir, analista, trainee, ...
  contractor  - ext, externo, terceiro, vendor, pj, ...
  temp        - temp, tmp, provisorio, ...
  generic     - user, usr, account, login, ...

Examples:
  wlf.py corp-prefixes --names 'PessoaX' --domain acme.example
  wlf.py corp-prefixes --names 'PessoaX' --prefixes svc,adm --separators .
  wlf.py corp-prefixes --names 'PessoaX' --categories department,role
  wlf.py corp-prefixes --names 'PessoaX' --sector judicial
  wlf.py corp-prefixes --list-prefixes
  wlf.py corp-prefixes --file employees.txt --domain corp.example -o prefixed.lst

options:
  -h, --help            show this help message and exit
  --names NAME1,NAME2   Comma-separated full names
  --file FILE           File with employee names
  --domain DOMAIN       Company domain for @domain suffix
  --no-at               Omit @domain suffix from output
  --prefixes pfx1,pfx2  Explicit prefix list (e.g. svc,adm,ti). Overrides
                        --categories.
  --categories cat1,cat2
                        Prefix categories to include: department, role,
                        contractor, temp, generic
  --sector SECTOR       Force sector label for prefix selection
                        (energia_utilities, judicial, financas, saude,
                        governo, generic, ...)
  --separators SEP      Separator(s) between prefix and name parts (default:
                        '.')
  --no-numeric          Skip numeric suffix variants
  --list-prefixes       List all available prefix groups and exit
  --config FILE         Custom prefix patterns JSON file (default:
                        data/corp_prefix_patterns.json)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--names` | - | no | Comma-separated full names |
| `--file` | - | no | File with employee names |
| `--domain` | '' | no | Company domain for @domain suffix |
| `--no-at` | False | no | Omit @domain suffix from output |
| `--prefixes` | - | no | Explicit prefix list (e.g. svc,adm,ti). Overrides --categories. |
| `--categories` | - | no | Prefix categories to include: department, role, contractor, temp, generic |
| `--sector` | - | no | Force sector label for prefix selection (energia_utilities, judicial, financas, saude, governo, generic, ...) |
| `--separators` | '.' | no | Separator(s) between prefix and name parts (default: '.') |
| `--no-numeric` | False | no | Skip numeric suffix variants |
| `--list-prefixes` | False | no | List all available prefix groups and exit |
| `--config` | - | no | Custom prefix patterns JSON file (default: data/corp_prefix_patterns.json) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf corp-prefixes --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


# `mutate`

Given an existing password, generate all mutations:

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

usage: wlf.py mutate [-h] [--leet-mode {basic,v2,v3,all,none}]
                     [--prefixes P1,P2,...] [--suffixes S1,S2,...]
                     [--min-len MIN_LEN] [--max-len MAX_LEN] [-o OUTPUT]
                     password

Given an existing password, generate all mutations:
case variants, leet substitutions, reversed, duplicated,
vowels stripped, and cartesian product with prefixes/suffixes.

Examples:
  wlf.py mutate "1q2w3e4r"
  wlf.py mutate "minhasenha" --leet-mode basic --min-len 8
  wlf.py mutate "abc123" --prefixes _,! --suffixes @0x90,#0x90,EMPTY
  wlf.py mutate "senha" --leet-mode none -o mutations.lst

positional arguments:
  password              Existing password to mutate

options:
  -h, --help            show this help message and exit
  --leet-mode {basic,v2,v3,all,none}
                        Leet substitution table (default: all)
  --prefixes P1,P2,...  Extra prefixes (comma-separated). Use EMPTY for empty
                        string.
  --suffixes S1,S2,...  Extra suffixes (comma-separated). Use EMPTY for empty
                        string.
  --min-len MIN_LEN     Minimum result length (default: 1)
  --max-len MAX_LEN     Maximum result length (default: 128)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `password` | - | yes | Existing password to mutate |
| `--leet-mode` | 'all' | no | Leet substitution table (default: all) |
| `--prefixes` | - | no | Extra prefixes (comma-separated). Use EMPTY for empty string. |
| `--suffixes` | - | no | Extra suffixes (comma-separated). Use EMPTY for empty string. |
| `--min-len` | 1 | no | Minimum result length (default: 1) |
| `--max-len` | 128 | no | Maximum result length (default: 128) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf mutate --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 2
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


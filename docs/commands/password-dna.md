# `password-dna`

Analyze 1-10 known passwords from a target to extract behavioral DNA:

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

usage: wlf.py password-dna [-h] [--file FILE] [--depth {quick,normal,deep}]
                           [--show-dna] [-o OUTPUT]
                           [passwords ...]

Analyze 1-10 known passwords from a target to extract behavioral DNA:
structural patterns, word banks, separator habits, number placement,
capitalization style, and leet preferences. Then generate a wordlist
of candidates matching the same behavioral profile.

Minimum: 1 password. Ideal: 3+ passwords. Maximum: 10.

Examples:
  wlf.py password-dna "Empresa@2024" "empresa#2025" "Empresa!123"
  wlf.py password-dna --file known_passwords.txt --depth deep -o candidates.lst
  wlf.py password-dna "P@ssw0rd1" --depth quick --show-dna
  wlf.py password-dna "PessoaX99" "pessoax.corpx@2024" "CorpX#pessoax1"

positional arguments:
  passwords             Known target passwords (1-10)

options:
  -h, --help            show this help message and exit
  --file FILE           File with known passwords (one per line, max 10)
  --depth {quick,normal,deep}
                        Generation depth: quick (~2K), normal (~15K), deep
                        (~100K+)
  --show-dna            Print the extracted DNA profile before generating
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `passwords` | - | no | Known target passwords (1-10) |
| `--file` | - | no | File with known passwords (one per line, max 10) |
| `--depth` | 'normal' | no | Generation depth: quick (~2K), normal (~15K), deep (~100K+) |
| `--show-dna` | False | no | Print the extracted DNA profile before generating |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf password-dna --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


# `phrase`

Extract the first letter of each word in a phrase and generate

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

usage: wlf.py phrase [-h] [--prefixes P1,P2,...] [--suffixes S1,S2,...]
                     [-o OUTPUT]
                     phrase

Extract the first letter of each word in a phrase and generate
password variants with case mutations, leet substitutions, and
prefix/suffix combinations, including hacker patterns (@0x90, #0x90).

PT-BR: 'mais' is replaced by '+' (common informal shorthand).

Examples:
  wlf.py phrase "é mais fácil pedir do que tentar quebrar"
  wlf.py phrase "minha empresa segura" --suffixes @0x90,#0x90
  wlf.py phrase "apenas um teste" --prefixes _,__ -o out.lst

positional arguments:
  phrase                Input phrase

options:
  -h, --help            show this help message and exit
  --prefixes P1,P2,...  Extra prefixes (comma-separated). Use EMPTY for empty
                        string.
  --suffixes S1,S2,...  Extra suffixes (comma-separated). Use EMPTY for empty
                        string.
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `phrase` | - | yes | Input phrase |
| `--prefixes` | - | no | Extra prefixes (comma-separated). Use EMPTY for empty string. |
| `--suffixes` | - | no | Extra suffixes (comma-separated). Use EMPTY for empty string. |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf phrase --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 2
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


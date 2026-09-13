# `xor`

xor

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

usage: wlf.py xor [-h] (--brute HEX | --encrypt TEXT | --decrypt HEX)
                  [--key KEY] [-o OUTPUT]

options:
  -h, --help           show this help message and exit
  --brute HEX          Brute-force single-byte key
  --encrypt TEXT       Encrypt text
  --decrypt HEX        Decrypt hex string
  --key KEY            Key for encrypt/decrypt
  -o, --output OUTPUT  Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--brute` | - | no | Brute-force single-byte key |
| `--encrypt` | - | no | Encrypt text |
| `--decrypt` | - | no | Decrypt hex string |
| `--key` | - | no | Key for encrypt/decrypt |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf xor --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


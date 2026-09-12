# `hash-id`

Identify likely hash algorithms for a digest.

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

usage: wlf.py hash-id [-h] [--wordlist FILE] [-o OUTPUT] [hash]

Identify likely hash algorithms for a digest, with the matching
hashcat mode where known.

Examples:
  wlf.py hash-id 5f4dcc3b5aa765d61d8327deb882cf99
  wlf.py hash-id --wordlist hashes.txt -o identified.txt

positional arguments:
  hash                 Hash string to identify

options:
  -h, --help           show this help message and exit
  --wordlist FILE      Identify every hash in a file
  -o, --output OUTPUT  Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `hash` | - | no | Hash string to identify |
| `--wordlist` | - | no | Identify every hash in a file |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf hash-id --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

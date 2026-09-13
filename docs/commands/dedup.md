# `dedup`

Deduplicate a wordlist without sorting, preserving order.

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

usage: wlf.py dedup [-h] [--bloom] [--capacity CAPACITY] [-o OUTPUT] WORDLIST

Order-preserving deduplication, optionally with a Bloom filter
for very large inputs (lower memory, tiny false-positive rate).

Examples:
  wlf.py dedup big.txt -o unique.txt
  wlf.py dedup huge.txt --bloom --capacity 50000000 -o unique.txt

positional arguments:
  WORDLIST             Input wordlist

options:
  -h, --help           show this help message and exit
  --bloom              Use a Bloom filter instead of an exact set
  --capacity CAPACITY  Expected distinct count for the Bloom filter
  -o, --output OUTPUT  Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Input wordlist |
| `--bloom` | False | no | Use a Bloom filter instead of an exact set |
| `--capacity` | 1000000 | no | Expected distinct count for the Bloom filter |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf dedup --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

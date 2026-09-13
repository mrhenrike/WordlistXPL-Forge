# `subtract`

Remove entries present in other files (rli style).

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

usage: wlf.py subtract [-h] --remove FILE [FILE ...] [-o OUTPUT] WORDLIST

Yield entries from the input that are not present in any of the
removal files. Useful to skip already-cracked or known lists.

Examples:
  wlf.py subtract candidates.txt --remove cracked.txt -o todo.txt
  wlf.py subtract all.txt --remove a.txt b.txt -o remaining.txt

positional arguments:
  WORDLIST              Input wordlist

options:
  -h, --help            show this help message and exit
  --remove FILE [FILE ...]
                        File(s) whose entries are removed from the output
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Input wordlist |
| `--remove` | - | yes | File(s) whose entries are removed from the output |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf subtract --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

# `reverse`

Reverse the line order of a wordlist (equivalent to 'tac').

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

usage: wlf.py reverse [-h] [--inplace] [-o OUTPUT] wordlist

Reverse the line order of a wordlist (equivalent to 'tac').

Examples:
  wlf.py reverse list.lst -o reversed.lst
  wlf.py reverse list.lst --inplace

positional arguments:
  wordlist             Wordlist to reverse

options:
  -h, --help           show this help message and exit
  --inplace            Overwrite original file
  -o, --output OUTPUT  Output file (default: stdout)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Wordlist to reverse |
| `--inplace` | False | no | Overwrite original file |
| `-o, --output` | - | no | Output file (default: stdout) |

## Input combinations

- Minimum: `wlf reverse --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


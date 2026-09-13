# `split`

Split a wordlist by count, size or entry length.

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

usage: wlf.py split [-h] [--lines LINES] [--size SIZE] [--by-length]
                    [-o PREFIX]
                    WORDLIST

Split a wordlist into multiple parts. Choose one mode:
  --lines N     N entries per part
  --size SPEC   max size per part (e.g. 50MB)
  --by-length   one file per entry length (splitlen style)

Examples:
  wlf.py split big.txt --lines 1000000 -o part
  wlf.py split big.txt --size 100MB -o chunk
  wlf.py split words.txt --by-length -o bylen

positional arguments:
  WORDLIST             Input wordlist

options:
  -h, --help           show this help message and exit
  --lines LINES        Max entries per part
  --size SIZE          Max size per part (e.g. 50MB)
  --by-length          Group entries into one file per length
  -o, --output PREFIX  Output path prefix (default: input path)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Input wordlist |
| `--lines` | 0 | no | Max entries per part |
| `--size` | '' | no | Max size per part (e.g. 50MB) |
| `--by-length` | False | no | Group entries into one file per length |
| `-o, --output` | - | no | Output path prefix (default: input path) |

## Input combinations

- Minimum: `wlf split --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

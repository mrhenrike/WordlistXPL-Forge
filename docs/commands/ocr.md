# `ocr`

ocr

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

usage: wlf.py ocr [-h] [--lang LANG] [-o OUTPUT] image

positional arguments:
  image                Image path

options:
  -h, --help           show this help message and exit
  --lang LANG          OCR languages (default: pt,en)
  -o, --output OUTPUT  Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `image` | - | yes | Image path |
| `--lang` | 'pt,en' | no | OCR languages (default: pt,en) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf ocr --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


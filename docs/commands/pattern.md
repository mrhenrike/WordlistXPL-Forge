# `pattern`

pattern

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

usage: wlf.py pattern [-h] [-t TEMPLATE] [-f TEMPLATE_FILE]
                      [--vars KEY=VALUE [KEY=VALUE ...]] [-o OUTPUT]

options:
  -h, --help            show this help message and exit
  -t, --template TEMPLATE
                        Template (e.g. XX{cod}@corp.example.com)
  -f, --template-file TEMPLATE_FILE
                        Template file
  --vars KEY=VALUE [KEY=VALUE ...]
                        Variables (e.g. cod=1200-1300 company=BrandX,CorpX)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `-t, --template` | - | no | Template (e.g. XX{cod}@corp.example.com) |
| `-f, --template-file` | - | no | Template file |
| `--vars` | - | no | Variables (e.g. cod=1200-1300 company=BrandX,CorpX) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf pattern --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 2
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


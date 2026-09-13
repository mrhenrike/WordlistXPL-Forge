# `num2text`

Converts a number (up to 12 digits) into its digit-by-digit word

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

usage: wlf.py num2text [-h] [--number N] [--range START-END] [--lang LANG]
                       [--separators SEP1,SEP2,...] [--no-leet]
                       [--min-len MIN_LEN] [--max-len MAX_LEN] [-o OUTPUT]

Converts a number (up to 12 digits) into its digit-by-digit word
representation and generates multiple case, leet and separator variants.

Language codes accepted:
  en / en-us / en-gb  - English (default)    one, two, three, ...
  pt / pt-pt          - European Portuguese   um, dois, tres, ...
  br / pt-br          - Brazilian Portuguese  um/uma, dois/duas, tres, ...
  es / es-es / es-mx  - Spanish               uno, dos, tres, ...

Examples:
  wlf num2text --number 123
  wlf num2text --number 123 --lang pt
  wlf num2text --number 123 --lang br
  wlf num2text --number 123 --lang es
  wlf num2text --number 1206 --lang en --separators -,_,@
  wlf num2text --range 0-9999 --lang en -o labs/labs_number2text.lst

options:
  -h, --help            show this help message and exit
  --number N            Single number to convert (up to 12 digits)
  --range START-END     Range of numbers to convert (e.g. 0-9999)
  --lang LANG           Digit language: en (default), pt, br, es - also: en-
                        us, pt-br, es-mx, etc.
  --separators SEP1,SEP2,...
                        Word separators (default: "", -, _, ., @, #, !)
  --no-leet             Skip leet substitutions
  --min-len MIN_LEN     Minimum entry length
  --max-len MAX_LEN     Maximum entry length
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--number` | - | no | Single number to convert (up to 12 digits) |
| `--range` | - | no | Range of numbers to convert (e.g. 0-9999) |
| `--lang` | 'en' | no | Digit language: en (default), pt, br, es - also: en-us, pt-br, es-mx, etc. |
| `--separators` | - | no | Word separators (default: "", -, _, ., @, #, !) |
| `--no-leet` | False | no | Skip leet substitutions |
| `--min-len` | 0 | no | Minimum entry length |
| `--max-len` | 0 | no | Maximum entry length |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf num2text --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


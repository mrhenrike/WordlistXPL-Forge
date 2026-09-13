# `charset`

charset

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

usage: wlf.py charset [-h] [-f CHARSET_FILE] [-p PATTERN] [--mask MASK]
                      [--custom-charset1 CHARS] [--digits N_DIGITS]
                      [--lower N_LOWER] [--upper N_UPPER]
                      [--special N_SPECIAL] [--create-charset FILE]
                      [-o OUTPUT]
                      [min_len] [max_len] [charset]

positional arguments:
  min_len               Minimum length (also fixed length for --constrained)
  max_len               Maximum length
  charset               Charset: built-in name or direct character string

options:
  -h, --help            show this help message and exit
  -f, --charset-file CHARSET_FILE
                        .cfg charset file
  -p, --pattern PATTERN
                        Pattern with Crunch-style placeholders (@,%,^,...)
  --mask MASK           Hashcat-style mask (e.g. ?u?l?l?d?d?s - ?u=upper
                        ?l=lower ?d=digit ?s=special ?a=all)
  --custom-charset1 CHARS
                        Custom charset for ?1 placeholder in mask
  --digits N_DIGITS     Exact digit count (constrained composition mode)
  --lower N_LOWER       Exact lowercase count (constrained composition mode)
  --upper N_UPPER       Exact uppercase count (constrained composition mode)
  --special N_SPECIAL   Exact special char count (constrained composition
                        mode)
  --create-charset FILE
                        Wizard to create a charset file
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `min_len` | 6 | no | Minimum length (also fixed length for --constrained) |
| `max_len` | 8 | no | Maximum length |
| `charset` | 'lalpha' | no | Charset: built-in name or direct character string |
| `-f, --charset-file` | - | no | .cfg charset file |
| `-p, --pattern` | - | no | Pattern with Crunch-style placeholders (@,%%,^,...) |
| `--mask` | - | no | Hashcat-style mask (e.g. ?u?l?l?d?d?s - ?u=upper ?l=lower ?d=digit ?s=special ?a=all) |
| `--custom-charset1` | - | no | Custom charset for ?1 placeholder in mask |
| `--digits` | 0 | no | Exact digit count (constrained composition mode) |
| `--lower` | 0 | no | Exact lowercase count (constrained composition mode) |
| `--upper` | 0 | no | Exact uppercase count (constrained composition mode) |
| `--special` | 0 | no | Exact special char count (constrained composition mode) |
| `--create-charset` | - | no | Wizard to create a charset file |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf charset --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 2
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


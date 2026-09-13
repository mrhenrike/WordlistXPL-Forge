# `iwlgen`

Generates wordlists from keyword permutations with optional

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

usage: wlf.py iwlgen [-h] --keywords KW1,KW2,... [--connectors CHARS] [--leet]
                     [--abbreviation] [--reverse] [--num-tails SPEC]
                     [--min-length MIN_LENGTH] [--max-length MAX_LENGTH]
                     [-o OUTPUT]

Generates wordlists from keyword permutations with optional
leet substitution, abbreviation, reversal, and numeric tails.
Native Python 3 port of intelligence-wordlist-generator.

Examples:
  wlf.py iwlgen --keywords admin,router,2024 --connectors @.
  wlf.py iwlgen --keywords empresa,corp --leet --abbreviation
  wlf.py iwlgen --keywords cisco,admin --num-tails 1-99 --connectors ._
  wlf.py iwlgen --keywords guest,pass --connectors '' -o out.lst

options:
  -h, --help            show this help message and exit
  --keywords KW1,KW2,...
                        Comma-separated keywords (e.g. admin,router,2024)
  --connectors CHARS    Connector characters to join keywords, specified as a
                        string. Each character becomes a separate connector
                        (default: '._-@' empty). Example: --connectors '@._'
                        uses @, ., _ and also empty string.
  --leet                Apply leet-speak substitutions to generated words
  --abbreviation        Generate single-character abbreviation variants
  --reverse             Generate element-reversal variants
  --num-tails SPEC      Numeric tail specs, comma-separated (e.g.
                        '1,2,01-05,2024')
  --min-length MIN_LENGTH
                        Minimum entry length (default: 4)
  --max-length MAX_LENGTH
                        Maximum entry length (default: 64)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--keywords` | - | yes | Comma-separated keywords (e.g. admin,router,2024) |
| `--connectors` | '' | no | Connector characters to join keywords, specified as a string. Each character becomes a separate connector (default: '._-@' empty). Example: --connectors '@._' uses @, ., _ and also empty string. |
| `--leet` | False | no | Apply leet-speak substitutions to generated words |
| `--abbreviation` | False | no | Generate single-character abbreviation variants |
| `--reverse` | False | no | Generate element-reversal variants |
| `--num-tails` | - | no | Numeric tail specs, comma-separated (e.g. '1,2,01-05,2024') |
| `--min-length` | 4 | no | Minimum entry length (default: 4) |
| `--max-length` | 64 | no | Maximum entry length (default: 64) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf iwlgen --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


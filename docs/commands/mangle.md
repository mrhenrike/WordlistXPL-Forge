# `mangle`

Apply transformation rules to every word in a wordlist.

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

usage: wlf.py mangle [-h] [--rules RULES] [--list-rules] [--overseer]
                     [--masks LIST] [--time-budget TIME_BUDGET] [--pps PPS]
                     [--use-gpu] [--capswap] [-o OUTPUT]
                     [wordlist]

Apply transformation rules to every word in a wordlist.

Rules (inspired by Hashcat/John rule engine):
  capitalize   - Capitalize first letter
  upper        - Uppercase entire word
  lower        - Lowercase entire word
  reverse      - Reverse the word
  toggle       - Toggle case of all chars
  append_num   - Append 0-99, common years
  prepend_num  - Prepend 0-9
  append_special - Append !, @, #, $, %, etc.
  leet_basic   - Basic leet substitutions
  duplicate    - Duplicate the word (e.g. passpass)
  strip_vowels - Remove all vowels

Examples:
  wlf.py mangle wordlist.lst -o mangled.lst
  wlf.py mangle wordlist.lst --rules capitalize,leet_basic,append_num
  wlf.py mangle wordlist.lst --list-rules

positional arguments:
  wordlist              Wordlist to mangle

options:
  -h, --help            show this help message and exit
  --rules RULES         Comma-separated rule names or 'all' (default: all)
  --list-rules          List available mangling rules and exit
  --overseer            PyMangler Overseer mask mode with time budget
  --masks LIST          Comma-separated masks for Overseer (w,wd,wds,...)
  --time-budget TIME_BUDGET
                        Crack time budget in hours for Overseer (default: 1.0)
  --pps PPS             Passwords/sec for Overseer budget (0=auto CPU/GPU)
  --use-gpu             Use GPU PPS defaults in Overseer mode (optional)
  --capswap             Enable positional capswap in Overseer mode
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | no | Wordlist to mangle |
| `--rules` | 'all' | no | Comma-separated rule names or 'all' (default: all) |
| `--list-rules` | False | no | List available mangling rules and exit |
| `--overseer` | False | no | PyMangler Overseer mask mode with time budget |
| `--masks` | - | no | Comma-separated masks for Overseer (w,wd,wds,...) |
| `--time-budget` | 1.0 | no | Crack time budget in hours for Overseer (default: 1.0) |
| `--pps` | 0 | no | Passwords/sec for Overseer budget (0=auto CPU/GPU) |
| `--use-gpu` | False | no | Use GPU PPS defaults in Overseer mode (optional) |
| `--capswap` | False | no | Enable positional capswap in Overseer mode |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf mangle --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


# `prince`

PRINCE (PRobability INfinite Chained Elements) attack mode.

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

usage: wlf.py prince [-h] --wordlist FILE [--min-len MIN_LEN]
                     [--max-len MAX_LEN] [--min-elem MIN_ELEM]
                     [--max-elem MAX_ELEM] [--separator SEPARATOR]
                     [--case-permute] [--wordlen-min WORDLEN_MIN]
                     [--wordlen-max WORDLEN_MAX] [--superchop SUPERCHOP]
                     [--max-words MAX_WORDS] [--limit LIMIT] [-o OUTPUT]

PRINCE (PRobability INfinite Chained Elements) attack mode.
Generates passwords by chaining elements from a wordlist.
Discovers multi-word passwords like 'correcthorsebatterystaple'.

Examples:
  wlf.py prince --wordlist base_words.txt --min-elem 2 --max-elem 4
  wlf.py prince --wordlist words.txt --separator '-' --case-permute
  wlf.py prince --wordlist top1000.txt --min-len 8 --max-len 20 --limit 500000

options:
  -h, --help            show this help message and exit
  --wordlist FILE       Input wordlist (element source)
  --min-len MIN_LEN     Min password length (default: 1)
  --max-len MAX_LEN     Max password length (default: 32)
  --min-elem MIN_ELEM   Min elements per chain (default: 1)
  --max-elem MAX_ELEM   Max elements per chain (default: 4)
  --separator SEPARATOR
                        Element separator (default: empty, use EMPTY for none)
  --case-permute        Generate case permutations
  --wordlen-min WORDLEN_MIN
                        Min element word length (0 = no filter)
  --wordlen-max WORDLEN_MAX
                        Max element word length (0 = no filter)
  --superchop SUPERCHOP
                        Truncate each element to N chars (pp64 superchop
                        parity)
  --max-words MAX_WORDS
                        Max words to load from file (0 = all)
  --limit LIMIT         Max candidates (0 = unlimited)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--wordlist` | - | yes | Input wordlist (element source) |
| `--min-len` | 1 | no | Min password length (default: 1) |
| `--max-len` | 32 | no | Max password length (default: 32) |
| `--min-elem` | 1 | no | Min elements per chain (default: 1) |
| `--max-elem` | 4 | no | Max elements per chain (default: 4) |
| `--separator` | '' | no | Element separator (default: empty, use EMPTY for none) |
| `--case-permute` | False | no | Generate case permutations |
| `--wordlen-min` | 0 | no | Min element word length (0 = no filter) |
| `--wordlen-max` | 0 | no | Max element word length (0 = no filter) |
| `--superchop` | 0 | no | Truncate each element to N chars (pp64 superchop parity) |
| `--max-words` | 0 | no | Max words to load from file (0 = all) |
| `--limit` | 0 | no | Max candidates (0 = unlimited) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf prince --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


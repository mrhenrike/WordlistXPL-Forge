# `keyspace`

Estimate candidate count and time to exhaust.

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

usage: wlf.py keyspace [-h] [--mask MASK] [--charset CHARSET]
                       [--min-len MIN_LEN] [--max-len MAX_LEN]
                       [--wordlist WORDLIST] [--rules RULES] [--pps PPS]

Estimate keyspace and time-to-exhaust for a mask, a charset over
a length range, or a wordlist optionally multiplied by a rule set.

Examples:
  wlf.py keyspace --mask '?u?l?l?l?d?d?d?d'
  wlf.py keyspace --charset abcdef0123456789 --min-len 6 --max-len 8
  wlf.py keyspace --wordlist base.txt --rules best64.rule --pps 5e9

options:
  -h, --help           show this help message and exit
  --mask MASK          Hashcat mask string
  --charset CHARSET    Charset for brute-force estimate
  --min-len MIN_LEN    Min length (charset mode)
  --max-len MAX_LEN    Max length (charset mode)
  --wordlist WORDLIST  Wordlist for count-based estimate
  --rules RULES        Rule file multiplier (wordlist mode)
  --pps PPS            Guess rate in passwords/second (default: 1e9)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--mask` | - | no | Hashcat mask string |
| `--charset` | - | no | Charset for brute-force estimate |
| `--min-len` | 1 | no | Min length (charset mode) |
| `--max-len` | 1 | no | Max length (charset mode) |
| `--wordlist` | - | no | Wordlist for count-based estimate |
| `--rules` | - | no | Rule file multiplier (wordlist mode) |
| `--pps` | 1000000000 | no | Guess rate in passwords/second (default: 1e9) |

## Input combinations

- Minimum: `wlf keyspace --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

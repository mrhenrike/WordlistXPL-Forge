# `strength`

zxcvbn-style password strength and entropy estimation.

## Syntax

```text
 __          _______ _    _         
 \ \        / /  ____| |  | |        
  \ \  /\  / /| |__  | |__| |       
   \ \/  \/ / |  __| |  __  |       
    \  /\  /  | |    | |  | |       
     \/  \/   |_|    |_|  |_|       

  WordlistXPL-Forge  v1.0.0
  Author: André Henrique (@mrhenrike)
  Unified wordlist generation for pentest & red team

usage: wlf.py strength [-h] [--wordlist FILE] [--dictionary FILE] [--hibp]
                       [--max-lines MAX_LINES] [-o OUTPUT]
                       [password]

Estimate password guessability with pattern matching (dictionary,
l33t, sequences, repeats, keyboard, dates), report entropy and a
0-4 score, and derive crack times per scenario and per hash.
Optionally check exposure against HIBP with k-anonymity.

Examples:
  wlf.py strength 'Summer2024!'
  wlf.py strength 'P@ssw0rd' --hibp
  wlf.py strength --wordlist candidates.txt -o scored.tsv

positional arguments:
  password              Password to score

options:
  -h, --help            show this help message and exit
  --wordlist FILE       Score every entry in a wordlist
  --dictionary FILE     Extra dictionary of known words
  --hibp                Check HIBP via k-anonymity (single password mode)
  --max-lines MAX_LINES
                        Max lines to score in wordlist mode (0 = all)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `password` | - | no | Password to score |
| `--wordlist` | - | no | Score every entry in a wordlist |
| `--dictionary` | - | no | Extra dictionary of known words |
| `--hibp` | False | no | Check HIBP via k-anonymity (single password mode) |
| `--max-lines` | 0 | no | Max lines to score in wordlist mode (0 = all) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf strength --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

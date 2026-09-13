# `passphrase`

Diceware and mnemonic passphrase generation using a CSPRNG.

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

usage: wlf.py passphrase [-h] [--wordlist FILE] [--count COUNT]
                         [--words WORDS] [--separator SEPARATOR]
                         [--capitalize] [--number] [--symbol] [-o OUTPUT]

Generate memorable passphrases from a word list using a secure
random source. Ships a built-in list; pass a larger list (for
example the EFF long wordlist) with --wordlist for more entropy.

Examples:
  wlf.py passphrase --count 20
  wlf.py passphrase --words 5 --separator . --capitalize --number
  wlf.py passphrase --wordlist eff_large_wordlist.txt --words 6 --symbol

options:
  -h, --help            show this help message and exit
  --wordlist FILE       Custom word list (default: built-in)
  --count COUNT         Number of passphrases (default: 20)
  --words WORDS         Words per passphrase (default: 4)
  --separator SEPARATOR
                        Separator between words (default: '-')
  --capitalize          Capitalize each word
  --number              Append a random digit
  --symbol              Append a random symbol
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--wordlist` | - | no | Custom word list (default: built-in) |
| `--count` | 20 | no | Number of passphrases (default: 20) |
| `--words` | 4 | no | Words per passphrase (default: 4) |
| `--separator` | '-' | no | Separator between words (default: '-') |
| `--capitalize` | False | no | Capitalize each word |
| `--number` | False | no | Append a random digit |
| `--symbol` | False | no | Append a random symbol |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf passphrase --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

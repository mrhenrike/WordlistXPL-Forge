# `leet-perm`

Apply full cartesian leet substitution to each line of a wordlist.

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

usage: wlf.py leet-perm [-h] [-o OUTPUT] [-m {medium,custom}]
                        [--custom-map CUSTOM_MAP]
                        [--max-per-word MAX_PER_WORD] [--max-lines MAX_LINES]
                        wordlist

Apply full cartesian leet substitution to each line of a wordlist.
Useful as a post-pass after profile or combiner generation.

Examples:
  wlf.py leet-perm words.lst -o leet_words.lst
  wlf.py leet-perm base.lst --max-per-word 256 --max-lines 5000

positional arguments:
  wordlist              Input wordlist (one token per line)

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Output file
  -m, --mode {medium,custom}
                        Leet map preset (default: medium)
  --custom-map CUSTOM_MAP
                        Custom char map (e.g. a=@,4;t=7;s=$)
  --max-per-word MAX_PER_WORD
                        Max variants per input word (default: 512)
  --max-lines MAX_LINES
                        Max input lines to process (0 = all)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Input wordlist (one token per line) |
| `-o, --output` | - | no | Output file |
| `-m, --mode` | 'medium' | no | Leet map preset (default: medium) |
| `--custom-map` | '' | no | Custom char map (e.g. a=@,4;t=7;s=$) |
| `--max-per-word` | 512 | no | Max variants per input word (default: 512) |
| `--max-lines` | 0 | no | Max input lines to process (0 = all) |

## Input combinations

- Minimum: `wlf leet-perm --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


# `isp-keygen`

Generate vendor-specific WiFi password wordlists based on known

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

usage: wlf.py isp-keygen [-h] [--isp ISP] [--direction {forward,reverse,both}]
                         [--limit LIMIT] [--estimate]
                         [--word5-file WORD5_FILE] [--word6-file WORD6_FILE]
                         [--list-isps] [-o OUTPUT]

Generate vendor-specific WiFi password wordlists based on known
ISP default password patterns.

Xfinity/Comcast pattern: word5 + 4digit + word6
  e.g., fever7538harbor (15 chars, lowercase + digits)

Keyspace: 686 × 10,000 × 685 = ~4.7 billion per direction.

Examples:
  wlf.py isp-keygen --list-isps
  wlf.py isp-keygen --isp xfinity_comcast --estimate
  wlf.py isp-keygen --isp xfinity_comcast --limit 1000 -o sample.lst
  wlf.py isp-keygen --isp xfinity_comcast --direction both -o full.lst
  wlf.py isp-keygen --isp xfinity_comcast --direction reverse --limit 500000 -o rev.lst
  wlf.py isp-keygen --isp xfinity_comcast --word5-file custom5.txt -o custom.lst

options:
  -h, --help            show this help message and exit
  --isp ISP             ISP pattern name (default: xfinity_comcast)
  --direction {forward,reverse,both}
                        Generation direction (default: forward)
  --limit LIMIT         Max entries to generate (0 = all)
  --estimate            Show keyspace estimate only, don't generate
  --word5-file WORD5_FILE
                        Custom 5-letter word file (overrides built-in)
  --word6-file WORD6_FILE
                        Custom 6-letter word file (overrides built-in)
  --list-isps           List available ISP patterns and exit
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--isp` | 'xfinity_comcast' | no | ISP pattern name (default: xfinity_comcast) |
| `--direction` | 'forward' | no | Generation direction (default: forward) |
| `--limit` | 0 | no | Max entries to generate (0 = all) |
| `--estimate` | False | no | Show keyspace estimate only, don't generate |
| `--word5-file` | - | no | Custom 5-letter word file (overrides built-in) |
| `--word6-file` | - | no | Custom 6-letter word file (overrides built-in) |
| `--list-isps` | False | no | List available ISP patterns and exit |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf isp-keygen --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


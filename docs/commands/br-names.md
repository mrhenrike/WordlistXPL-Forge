# `br-names`

Loads name lists from the BRWordList submodule and produces

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

usage: wlf.py br-names [-h]
                       [--category {names,surnames,full_names,initials,rev_initials,a-z,all}]
                       [--leet] [--brwordlist-path PATH] [-o OUTPUT]

Loads name lists from the BRWordList submodule and produces
a deduplicated username wordlist suitable for credential attacks.

Requires: git submodule update --init submodules/Wordlists/BRWordList

Examples:
  wlf.py br-names
  wlf.py br-names --category surnames -o surnames.lst
  wlf.py br-names --category all --leet -o names_leet.lst
  wlf.py br-names --brwordlist-path /opt/BRWordList

options:
  -h, --help            show this help message and exit
  --category {names,surnames,full_names,initials,rev_initials,a-z,all}
                        Name category to load (default: names)
  --leet                Also generate basic leet variants
  --brwordlist-path PATH
                        Explicit path to BRWordList root (auto-detected if
                        omitted)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--category` | 'names' | no | Name category to load (default: names) |
| `--leet` | False | no | Also generate basic leet variants |
| `--brwordlist-path` | - | no | Explicit path to BRWordList root (auto-detected if omitted) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf br-names --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


# `rules`

Apply, convert or optimize hashcat and John rules against a wordlist.

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

usage: wlf.py rules [-h] [--wordlist FILE] [--rules FILE] [--rule STR]
                    [--to {hashcat,john}] [--dedupe] [-o OUTPUT]
                    [{apply,convert,optimize}]

Rule engine: run hashcat and John the Ripper rules against a
wordlist (like hashcat --stdout -r), convert between the two
dialects, or optimize a rule file.

Examples:
  wlf.py rules apply --wordlist base.txt --rules best64.rule -o out.lst
  wlf.py rules apply --wordlist base.txt --rule 'c $1;$2;so0' --dedupe
  wlf.py rules convert --rules hc.rule --to john -o jtr.rule
  wlf.py rules optimize --rules messy.rule -o clean.rule

positional arguments:
  {apply,convert,optimize}
                        Action (default: apply)

options:
  -h, --help            show this help message and exit
  --wordlist FILE       Input wordlist (for apply)
  --rules FILE          Rule file (one rule per line, # comments)
  --rule STR            Inline rule(s), separated by ';'
  --to {hashcat,john}   Target dialect for convert (default: john)
  --dedupe              Suppress duplicate outputs (apply mode)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `rules_action` | 'apply' | no | Action (default: apply) |
| `--wordlist` | - | no | Input wordlist (for apply) |
| `--rules` | - | no | Rule file (one rule per line, # comments) |
| `--rule` | - | no | Inline rule(s), separated by ';' |
| `--to` | 'john' | no | Target dialect for convert (default: john) |
| `--dedupe` | False | no | Suppress duplicate outputs (apply mode) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf rules --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

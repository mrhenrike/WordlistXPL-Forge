# `curate`

Rank lists by crack rate and merge the best (weakpass style).

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

usage: wlf.py curate [-h] --candidates FILE [FILE ...] --reference FILE
                     [--metric {hitrate,hits}] [--top-k TOP_K]
                     [--max-reference MAX_REFERENCE] [-o OUTPUT]

Rank candidate lists by crack rate against a reference and merge
the top performers into a single deduplicated wordlist.

Examples:
  wlf.py curate --candidates a.txt b.txt c.txt --reference test.txt --top-k 2 -o best.txt
  wlf.py curate --candidates *.txt --reference test.txt --metric hits

options:
  -h, --help            show this help message and exit
  --candidates FILE [FILE ...]
                        Candidate list file(s)
  --reference FILE      Reference password file
  --metric {hitrate,hits}
                        Ranking metric (default: hitrate)
  --top-k TOP_K         Number of top lists to merge (default: 2)
  --max-reference MAX_REFERENCE
                        Max reference entries (0 = all)
  -o, --output OUTPUT   Merged output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--candidates` | - | yes | Candidate list file(s) |
| `--reference` | - | yes | Reference password file |
| `--metric` | 'hitrate' | no | Ranking metric (default: hitrate) |
| `--top-k` | 2 | no | Number of top lists to merge (default: 2) |
| `--max-reference` | 0 | no | Max reference entries (0 = all) |
| `-o, --output` | - | no | Merged output file |

## Input combinations

- Minimum: `wlf curate --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

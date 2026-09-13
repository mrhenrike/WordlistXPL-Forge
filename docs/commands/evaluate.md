# `evaluate`

Compare engines by guess-number and coverage (MAYA style).

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

usage: wlf.py evaluate [-h] --candidates FILE [FILE ...] --reference FILE
                       [--labels L1,L2,...] [--cutoffs N1,N2,...]
                       [--max-candidates MAX_CANDIDATES]
                       [--max-reference MAX_REFERENCE] [-o OUTPUT]

Evaluate one or more candidate lists against a reference test set,
reporting coverage, median guess number and cumulative hits at
configurable cutoffs. Each candidate list represents an engine.

Examples:
  wlf.py evaluate --candidates pcfg.lst markov.lst --labels pcfg,markov --reference test.txt
  wlf.py evaluate --candidates a.lst b.lst --reference test.txt --cutoffs 1e3,1e5,1e7

options:
  -h, --help            show this help message and exit
  --candidates FILE [FILE ...]
                        Candidate list file(s)
  --reference FILE      Reference (ground-truth) password file
  --labels L1,L2,...    Comma-separated labels for the candidate lists
  --cutoffs N1,N2,...   Guess-count cutoffs (default: 1e3,1e4,1e5,1e6,1e7)
  --max-candidates MAX_CANDIDATES
                        Max lines per candidate (0 = all)
  --max-reference MAX_REFERENCE
                        Max reference entries (0 = all)
  -o, --output OUTPUT   Save report to file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--candidates` | - | yes | Candidate list file(s) |
| `--reference` | - | yes | Reference (ground-truth) password file |
| `--labels` | - | no | Comma-separated labels for the candidate lists |
| `--cutoffs` | - | no | Guess-count cutoffs (default: 1e3,1e4,1e5,1e6,1e7) |
| `--max-candidates` | 0 | no | Max lines per candidate (0 = all) |
| `--max-reference` | 0 | no | Max reference entries (0 = all) |
| `-o, --output` | - | no | Save report to file |

## Input combinations

- Minimum: `wlf evaluate --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

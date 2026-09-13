# `benchmark`

Benchmark a generated wordlist against a reference password set.

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

usage: wlf.py benchmark [-h] --wordlist FILE --reference FILE
                        [--max-candidates MAX_CANDIDATES]
                        [--max-reference MAX_REFERENCE] [--json FILE]
                        [-o OUTPUT]

Benchmark a generated wordlist against a reference password set.
Measures hit rate, coverage, efficiency, diversity, and more.
Inspired by MAYA (IEEE S&P 2026) benchmarking framework.

Examples:
  wlf.py benchmark --wordlist generated.lst --reference rockyou.txt
  wlf.py benchmark --wordlist out.lst --reference test_set.txt --json report.json
  wlf.py benchmark --wordlist my_list.lst --reference leaked.txt --max-candidates 1000000

options:
  -h, --help            show this help message and exit
  --wordlist FILE       Generated wordlist to evaluate
  --reference FILE      Reference password set (ground truth)
  --max-candidates MAX_CANDIDATES
                        Max lines to read from wordlist (0 = all)
  --max-reference MAX_REFERENCE
                        Max lines to read from reference (0 = all)
  --json FILE           Save results as JSON report
  -o, --output OUTPUT   Save text report to file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--wordlist` | - | yes | Generated wordlist to evaluate |
| `--reference` | - | yes | Reference password set (ground truth) |
| `--max-candidates` | 0 | no | Max lines to read from wordlist (0 = all) |
| `--max-reference` | 0 | no | Max lines to read from reference (0 = all) |
| `--json` | - | no | Save results as JSON report |
| `-o, --output` | - | no | Save text report to file |

## Input combinations

- Minimum: `wlf benchmark --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


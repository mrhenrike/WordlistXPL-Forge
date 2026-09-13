# `dns`

dns

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

usage: wlf.py dns [-h] [-d DOMAIN] [--domain-list FILE] [-w WORDLIST]
                  [--words WORDS [WORDS ...]] [-t TEMPLATE]
                  [--template-file FILE] [--separator SEPARATOR]
                  [--match-regex REGEX] [--filter-regex REGEX] [--no-prefixes]
                  [--no-suffixes] [--enrich] [--clusterbomb]
                  [--payload KEY=FILE] [--dnscewl]
                  [--numeric-range NUMERIC_RANGE]
                  [--extension-swap TLD [TLD ...]] [--estimate] [-o OUTPUT]

options:
  -h, --help            show this help message and exit
  -d, --domain DOMAIN   Target domain (required unless --domain-list)
  --domain-list FILE    File with one domain per line (multi-domain mode)
  -w, --wordlist WORDLIST
                        Words file
  --words WORDS [WORDS ...]
                        Direct word list
  -t, --template TEMPLATE
                        Inline template (e.g. dev-{word}.{domain})
  --template-file FILE  YAML file with permutation templates (alterx-
                        compatible)
  --separator SEPARATOR
                        Custom separator between tokens (e.g. _ or .)
  --match-regex REGEX   Include only output matching this regex
  --filter-regex REGEX  Exclude output matching this regex
  --no-prefixes
  --no-suffixes
  --enrich              Extract tokens from input FQDNs to enrich payloads
                        (alterx -enrich)
  --clusterbomb         Use ClusterBomb mode with built-in alterx patterns and
                        payloads
  --payload KEY=FILE    Custom payload file (key=file, can repeat). Keys:
                        word, number, region
  --dnscewl             Add DNSCewl-style mutations (append/prepend/numeric-
                        range)
  --numeric-range NUMERIC_RANGE
                        Numeric range for DNSCewl mutations (default: 10)
  --extension-swap TLD [TLD ...]
                        Swap TLD extensions (e.g. com.au co.uk org)
  --estimate            Estimate output size without generating
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `-d, --domain` | '' | no | Target domain (required unless --domain-list) |
| `--domain-list` | - | no | File with one domain per line (multi-domain mode) |
| `-w, --wordlist` | - | no | Words file |
| `--words` | - | no | Direct word list |
| `-t, --template` | - | no | Inline template (e.g. dev-{word}.{domain}) |
| `--template-file` | - | no | YAML file with permutation templates (alterx-compatible) |
| `--separator` | - | no | Custom separator between tokens (e.g. _ or .) |
| `--match-regex` | - | no | Include only output matching this regex |
| `--filter-regex` | - | no | Exclude output matching this regex |
| `--no-prefixes` | False | no |  |
| `--no-suffixes` | False | no |  |
| `--enrich` | False | no | Extract tokens from input FQDNs to enrich payloads (alterx -enrich) |
| `--clusterbomb` | False | no | Use ClusterBomb mode with built-in alterx patterns and payloads |
| `--payload` | - | no | Custom payload file (key=file, can repeat). Keys: word, number, region |
| `--dnscewl` | False | no | Add DNSCewl-style mutations (append/prepend/numeric-range) |
| `--numeric-range` | 10 | no | Numeric range for DNSCewl mutations (default: 10) |
| `--extension-swap` | - | no | Swap TLD extensions (e.g. com.au co.uk org) |
| `--estimate` | False | no | Estimate output size without generating |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf dns --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


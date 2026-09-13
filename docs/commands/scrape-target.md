# `scrape-target`

Lightweight target spider: crawl a URL and extract

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

usage: wlf.py scrape-target [-h] --url URL [--depth DEPTH] [--min-len MIN_LEN]
                            [--max-pages MAX_PAGES] [-o OUTPUT]

Lightweight target spider: crawl a URL and extract
unique words suitable for wordlist generation.

Examples:
  wlf.py scrape-target --url https://example.com -o words.lst
  wlf.py scrape-target --url https://corp.com --depth 3 --max-pages 50

options:
  -h, --help            show this help message and exit
  --url URL             Target URL to crawl
  --depth DEPTH         Crawl depth (default: 2)
  --min-len MIN_LEN     Min word length (default: 4)
  --max-pages MAX_PAGES
                        Max pages to fetch (default: 20)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--url` | - | yes | Target URL to crawl |
| `--depth` | 2 | no | Crawl depth (default: 2) |
| `--min-len` | 4 | no | Min word length (default: 4) |
| `--max-pages` | 20 | no | Max pages to fetch (default: 20) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf scrape-target --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


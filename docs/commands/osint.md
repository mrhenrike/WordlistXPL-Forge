# `osint`

Advanced OSINT wordlists from Wayback, GitHub org, NER and enrichment.

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

usage: wlf.py osint [-h] [--wayback DOMAIN] [--github-org ORG]
                    [--limit-urls LIMIT_URLS] [--max-repos MAX_REPOS]
                    [--enrich] [--provider {ollama,openai}] [--model MODEL]
                    [--lowercase] [-o OUTPUT]

Build hyper-contextual wordlists from passive OSINT. Collects
historical URLs from the Wayback Machine and public repository
metadata from a GitHub organization, extracts entities, and can
optionally enrich the result locally or with an LLM provider.

Examples:
  wlf.py osint --wayback example.com -o words.lst
  wlf.py osint --github-org acme --lowercase -o org.lst
  wlf.py osint --wayback example.com --github-org acme --enrich -o rich.lst
  wlf.py osint --github-org acme --enrich --provider ollama --model llama3

options:
  -h, --help            show this help message and exit
  --wayback DOMAIN      Collect from the Wayback Machine for a domain
  --github-org ORG      Collect from a GitHub organization
  --limit-urls LIMIT_URLS
                        Max Wayback URLs to fetch (default: 5000)
  --max-repos MAX_REPOS
                        Max GitHub repos to inspect (default: 200)
  --enrich              Enrich results (local heuristic or LLM provider)
  --provider {ollama,openai}
                        LLM provider for --enrich (optional)
  --model MODEL         LLM model name for --provider (default: llama3)
  --lowercase           Lowercase all output
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--wayback` | - | no | Collect from the Wayback Machine for a domain |
| `--github-org` | - | no | Collect from a GitHub organization |
| `--limit-urls` | 5000 | no | Max Wayback URLs to fetch (default: 5000) |
| `--max-repos` | 200 | no | Max GitHub repos to inspect (default: 200) |
| `--enrich` | False | no | Enrich results (local heuristic or LLM provider) |
| `--provider` | - | no | LLM provider for --enrich (optional) |
| `--model` | 'llama3' | no | LLM model name for --provider (default: llama3) |
| `--lowercase` | False | no | Lowercase all output |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf osint --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

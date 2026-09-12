# `scrape`

scrape

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

usage: wlf.py scrape [-h] [-d DEPTH] [--min-word MIN_WORD]
                     [--max-word MAX_WORD] [--emails] [--meta] [--auth AUTH]
                     [--proxy PROXY] [--user-agent USER_AGENT]
                     [--header NAME:VALUE] [--no-stopwords]
                     [--stopwords-file FILE] [--delay DELAY] [--with-numbers]
                     [--with-spaces] [--urls-file FILE] [--capture-paths]
                     [--capture-subdomains] [--include-js] [--include-css]
                     [--include-pdf] [--lowercase]
                     [--subdomain-strategy {exact,children,all}]
                     [--output-emails FILE] [--output-urls FILE] [--stream]
                     [-o OUTPUT]
                     url

positional arguments:
  url                   Target URL

options:
  -h, --help            show this help message and exit
  -d, --depth DEPTH     Crawl depth (default: 2)
  --min-word MIN_WORD   Minimum word length to extract (default: 6)
  --max-word MAX_WORD   Maximum word length to extract (default: 32)
  --emails              Extract email addresses
  --meta                Extract metadata (Author, Generator)
  --auth AUTH           HTTP Basic Auth (user:password)
  --proxy PROXY         HTTP/SOCKS proxy URL (e.g. http://127.0.0.1:8080)
  --user-agent USER_AGENT
                        Custom User-Agent string
  --header NAME:VALUE   Extra HTTP header (can be repeated)
  --no-stopwords        Exclude common EN/PT-BR stop-words from output
  --stopwords-file FILE
                        Custom stop-words file (one word per line)
  --delay DELAY         Delay between requests in seconds (default: 0.5)
  --with-numbers        Include words containing digits (normally excluded)
  --with-spaces         Include multi-word phrases (space-separated tokens)
  --urls-file FILE      File with one URL per line (multi-URL scraping mode)
  --capture-paths       Extract URL path segments as additional words
  --capture-subdomains  Extract subdomain labels as additional words
  --include-js          Include words from JavaScript content (cewler parity)
  --include-css         Include words from CSS content (cewler parity)
  --include-pdf         Extract text from PDF files found during crawl
                        (requires pypdf)
  --lowercase           Lowercase all extracted words
  --subdomain-strategy {exact,children,all}
                        Subdomain crawl scope: exact (default), children, all
  --output-emails FILE  Write extracted emails to separate file
  --output-urls FILE    Write visited URLs to separate file
  --stream              Flush output after each page (real-time streaming,
                        requires -o)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `url` | - | yes | Target URL |
| `-d, --depth` | 2 | no | Crawl depth (default: 2) |
| `--min-word` | 6 | no | Minimum word length to extract (default: 6) |
| `--max-word` | 32 | no | Maximum word length to extract (default: 32) |
| `--emails` | False | no | Extract email addresses |
| `--meta` | False | no | Extract metadata (Author, Generator) |
| `--auth` | - | no | HTTP Basic Auth (user:password) |
| `--proxy` | - | no | HTTP/SOCKS proxy URL (e.g. http://127.0.0.1:8080) |
| `--user-agent` | - | no | Custom User-Agent string |
| `--header` | - | no | Extra HTTP header (can be repeated) |
| `--no-stopwords` | False | no | Exclude common EN/PT-BR stop-words from output |
| `--stopwords-file` | - | no | Custom stop-words file (one word per line) |
| `--delay` | 0.5 | no | Delay between requests in seconds (default: 0.5) |
| `--with-numbers` | False | no | Include words containing digits (normally excluded) |
| `--with-spaces` | False | no | Include multi-word phrases (space-separated tokens) |
| `--urls-file` | - | no | File with one URL per line (multi-URL scraping mode) |
| `--capture-paths` | False | no | Extract URL path segments as additional words |
| `--capture-subdomains` | False | no | Extract subdomain labels as additional words |
| `--include-js` | False | no | Include words from JavaScript content (cewler parity) |
| `--include-css` | False | no | Include words from CSS content (cewler parity) |
| `--include-pdf` | False | no | Extract text from PDF files found during crawl (requires pypdf) |
| `--lowercase` | False | no | Lowercase all extracted words |
| `--subdomain-strategy` | 'exact' | no | Subdomain crawl scope: exact (default), children, all |
| `--output-emails` | - | no | Write extracted emails to separate file |
| `--output-urls` | - | no | Write visited URLs to separate file |
| `--stream` | False | no | Flush output after each page (real-time streaming, requires -o) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf scrape --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


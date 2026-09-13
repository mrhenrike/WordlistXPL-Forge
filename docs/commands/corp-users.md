# `corp-users`

Generate corporate username/password lists from employee names.

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

usage: wlf.py corp-users [-h] [--domain DOMAIN] [--company COMPANY]
                         [--file FILE] [--search COMPANY_NAME]
                         [--names NAME1,NAME2,...] [--max-results MAX_RESULTS]
                         [--no-api] [--separators SEP] [--subdomain SUB1,SUB2]
                         [--no-users] [--no-at] [--passwords] [--combo]
                         [--year-start YEAR_START] [--year-end YEAR_END]
                         [-o OUTPUT] [--no-ml]

Generate corporate username/password lists from employee names.

Name sources (choose one or combine):
  --file       Load names from txt/csv/xlsx/pdf file
  --search     Search online via Google dorks (no API needed)
  --names      Comma-separated names inline

LinkedIn API (optional):
  Set LINKEDIN_RAPIDAPI_KEY env var to enable API-based search.
  Without it, Google dorks are used automatically.

Username patterns generated (default separator: '.'; use --separators to change):
  firstname.lastname  f.lastname  flastname  lastname.firstname
  firstname  lastname  firstnamel  initials  and 15+ more

Examples:
  wlf.py corp-users --domain acme.example --file employees.txt
  wlf.py corp-users --domain acme.example --search 'BrandX'
  wlf.py corp-users --domain acme.example --names 'PessoaX,PersonY'
  wlf.py corp-users --domain acme.example --file names.txt --combo -o combo.lst
  wlf.py corp-users --domain acme.example --subdomain corp-ad -o admins.lst

options:
  -h, --help            show this help message and exit
  --domain DOMAIN       Company domain (e.g. acme.example)
  --company COMPANY     Company trade name (for passwords). Defaults to domain
                        prefix.
  --file FILE           File with employee names (txt/csv/xlsx/pdf/docx)
  --search COMPANY_NAME
                        Search online for employee names (Google dorks)
  --names NAME1,NAME2,...
                        Comma-separated full names inline
  --max-results MAX_RESULTS
                        Max online search results (default: 50)
  --no-api              Skip LinkedIn API even if LINKEDIN_RAPIDAPI_KEY is set
  --separators SEP      Username separator(s) used between name parts.
                        Default: '.' (dot only). Examples: --separators _ |
                        --separators .,_ | --separators all (uses . _ - and
                        empty) | --separators none (no separator).
  --subdomain SUB1,SUB2
                        Subdomain(s) for admin patterns (e.g.
                        corp-ad,webmail)
  --no-users            Skip username generation (only passwords or combo)
  --no-at               Omit @domain suffix from usernames
  --passwords           Also generate password list
  --combo               Generate user:password combo list
  --year-start YEAR_START
                        Password year range start (default: 2020)
  --year-end YEAR_END   Password year range end (default: 2026)
  -o, --output OUTPUT   Output file
  --no-ml               Disable ML-based ranking (use original rule-based
                        order)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--domain` | '' | no | Company domain (e.g. acme.example) |
| `--company` | '' | no | Company trade name (for passwords). Defaults to domain prefix. |
| `--file` | - | no | File with employee names (txt/csv/xlsx/pdf/docx) |
| `--search` | - | no | Search online for employee names (Google dorks) |
| `--names` | - | no | Comma-separated full names inline |
| `--max-results` | 50 | no | Max online search results (default: 50) |
| `--no-api` | False | no | Skip LinkedIn API even if LINKEDIN_RAPIDAPI_KEY is set |
| `--separators` | - | no | Username separator(s) used between name parts. Default: '.' (dot only). Examples: --separators _ \| --separators .,_ \| --separators all (uses . _ - and empty) \| --separators none (no separator). |
| `--subdomain` | - | no | Subdomain(s) for admin patterns (e.g. corp-ad,webmail) |
| `--no-users` | False | no | Skip username generation (only passwords or combo) |
| `--no-at` | False | no | Omit @domain suffix from usernames |
| `--passwords` | False | no | Also generate password list |
| `--combo` | False | no | Generate user:password combo list |
| `--year-start` | 2020 | no | Password year range start (default: 2020) |
| `--year-end` | 2026 | no | Password year range end (default: 2026) |
| `-o, --output` | - | no | Output file |
| `--no-ml` | True | no | Disable ML-based ranking (use original rule-based order) |

## Input combinations

- Minimum: `wlf corp-users --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 1

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


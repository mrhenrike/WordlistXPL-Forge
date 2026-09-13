# `sanitize`

Sanitize an existing wordlist applying filters in order:

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

usage: wlf.py sanitize [-h] [--min-len MIN_LEN] [--max-len MAX_LEN]
                       [--sort {alpha,alpha-rev,length,length-rev,random,frequency}]
                       [--filter REGEX] [--exclude REGEX] [--no-dedupe]
                       [--keep-blank] [--keep-comments] [--strip-control]
                       [--inplace] [-o OUTPUT]
                       wordlist

Sanitize an existing wordlist applying filters in order:
  1. Remove comments (#)     2. Remove blank lines
  3. Filter by length        4. Filter by regex
  5. Deduplicate             6. Sort

Examples:
  wlf.py sanitize list.lst --inplace
  wlf.py sanitize list.lst --min-len 8 --sort alpha -o clean.lst
  wlf.py sanitize list.lst --filter '^[a-zA-Z]' --exclude '\d{3,}$' -o out.lst
  wlf.py sanitize list.lst --min-len 6 --max-len 20 --sort length-rev -o out.lst

positional arguments:
  wordlist              Wordlist to sanitize

options:
  -h, --help            show this help message and exit
  --min-len MIN_LEN     Minimum length (removes shorter entries)
  --max-len MAX_LEN     Maximum length (removes longer entries)
  --sort {alpha,alpha-rev,length,length-rev,random,frequency}
                        Sort mode: alpha, alpha-rev, length, length-rev,
                        random, frequency
  --filter REGEX        Include regex - keep only matching lines
  --exclude REGEX       Exclude regex - remove matching lines
  --no-dedupe           Do not remove duplicates
  --keep-blank          Keep blank lines
  --keep-comments       Keep comment lines (#)
  --strip-control       Remove control characters (tabs, null bytes, escape
                        sequences) from lines
  --inplace             Overwrite original file
  -o, --output OUTPUT   Output file (default: stdout)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `wordlist` | - | yes | Wordlist to sanitize |
| `--min-len` | - | no | Minimum length (removes shorter entries) |
| `--max-len` | - | no | Maximum length (removes longer entries) |
| `--sort` | - | no | Sort mode: alpha, alpha-rev, length, length-rev, random, frequency |
| `--filter` | - | no | Include regex - keep only matching lines |
| `--exclude` | - | no | Exclude regex - remove matching lines |
| `--no-dedupe` | False | no | Do not remove duplicates |
| `--keep-blank` | False | no | Keep blank lines |
| `--keep-comments` | False | no | Keep comment lines (#) |
| `--strip-control` | False | no | Remove control characters (tabs, null bytes, escape sequences) from lines |
| `--inplace` | False | no | Overwrite original file |
| `-o, --output` | - | no | Output file (default: stdout) |

## Input combinations

- Minimum: `wlf sanitize --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


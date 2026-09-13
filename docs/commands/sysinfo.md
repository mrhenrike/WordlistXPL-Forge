# `sysinfo`

Display detected CPU, RAM, GPU and compute backend.

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

usage: wlf.py sysinfo [-h] [--crc32-stress N]

Display detected CPU, RAM, GPU and compute backend.
Shows current --threads and --compute settings.

Examples:
  wlf.py sysinfo
  wlf.py sysinfo --crc32-stress 150000
  wlf.py --compute gpu sysinfo
  wlf.py --threads 20 sysinfo

options:
  -h, --help        show this help message and exit
  --crc32-stress N  Run CRC32 dedup stress test with N synthetic lines
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--crc32-stress` | 0 | no | Run CRC32 dedup stress test with N synthetic lines |

## Input combinations

- Minimum: `wlf sysinfo --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


# `profile`

profile

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

usage: wlf.py profile [-h] [--name NAME] [--nick NICK] [--birth BIRTH]
                      [--profile-file FILE] [--year-start YYYY]
                      [--year-end YYYY] [--suffix-range START-END]
                      [--leet {basic,medium,aggressive,none}]
                      [--surname SURNAME] [--old-passwords PWD [PWD ...]]
                      [--depth {3,4,5}] [--parents NAME [NAME ...]]
                      [--siblings NAME [NAME ...]] [--engines SPEC]
                      [--max-candidates N] [--timeout SECS] [-o OUTPUT]

options:
  -h, --help            show this help message and exit
  --name NAME           Target full name
  --nick NICK           Nickname or alias
  --birth BIRTH         Date of birth (dd/mm/yyyy, ddmmyyyy, yyyy, or age)
  --profile-file FILE   Load profile from YAML file (non-interactive mode)
  --year-start YYYY     Include year range from this year (e.g. 2000)
  --year-end YYYY       Include year range to this year (e.g. 2026)
  --suffix-range START-END
                        Append numeric suffix range (e.g. 00-99 or 1-9999)
  --leet {basic,medium,aggressive,none}
                        Leet speak mode (default: from profile YAML or basic)
  --surname SURNAME     Surname (separate from first name, CUPP parity)
  --old-passwords PWD [PWD ...]
                        Known old passwords to mutate (elpscrk parity)
  --depth {3,4,5}       Permutation depth: 3 (default), 4 (enhanced), 5 (max
                        BEWGor)
  --parents NAME [NAME ...]
                        Parent names (BEWGor parity)
  --siblings NAME [NAME ...]
                        Sibling names (BEWGor parity)
  --engines SPEC        Engine selection: preset name
                        (light/medium/potent/nuclear), numeric IDs (1,3,5),
                        range (1-10), or 'all'. Skips interactive engine menu
                        when provided.
  --max-candidates N    Hard limit on generated candidates (0 = unlimited)
  --timeout SECS        Pipeline timeout in seconds (0 = no timeout)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--name` | - | no | Target full name |
| `--nick` | - | no | Nickname or alias |
| `--birth` | - | no | Date of birth (dd/mm/yyyy, ddmmyyyy, yyyy, or age) |
| `--profile-file` | - | no | Load profile from YAML file (non-interactive mode) |
| `--year-start` | - | no | Include year range from this year (e.g. 2000) |
| `--year-end` | - | no | Include year range to this year (e.g. 2026) |
| `--suffix-range` | - | no | Append numeric suffix range (e.g. 00-99 or 1-9999) |
| `--leet` | - | no | Leet speak mode (default: from profile YAML or basic) |
| `--surname` | - | no | Surname (separate from first name, CUPP parity) |
| `--old-passwords` | - | no | Known old passwords to mutate (elpscrk parity) |
| `--depth` | 3 | no | Permutation depth: 3 (default), 4 (enhanced), 5 (max BEWGor) |
| `--parents` | - | no | Parent names (BEWGor parity) |
| `--siblings` | - | no | Sibling names (BEWGor parity) |
| `--engines` | - | no | Engine selection: preset name (light/medium/potent/nuclear), numeric IDs (1,3,5), range (1-10), or 'all'. Skips interactive engine menu when provided. |
| `--max-candidates` | 0 | no | Hard limit on generated candidates (0 = unlimited) |
| `--timeout` | 0.0 | no | Pipeline timeout in seconds (0 = no timeout) |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf profile --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 1

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


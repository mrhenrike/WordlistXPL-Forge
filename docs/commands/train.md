# `train`

Train the statistical pattern model for corporate credential generation.

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

usage: wlf.py train [-h] [--csv FILE] [--wordlist FILE] [--usernames FILE]
                    [--auto] [--uid-col UID_COL] [--eid-col EID_COL]
                    [--mail-col MAIL_COL] [--max-rows MAX_ROWS]
                    [--max-lines MAX_LINES] [--seclists [PATH]]
                    [--seclists-categories CAT [CAT ...]] [-o FILE]

Train the statistical pattern model for corporate credential generation.

Privacy: only structural patterns are extracted - no raw usernames,
passwords, company names, or personal data are ever stored.

Examples:
  wlf.py train --csv export.csv --auto -o .model/pattern_model.json
  wlf.py train --auto
  wlf.py train --seclists
  wlf.py train --seclists /path/to/SecLists --seclists-categories password frequency
  wlf.py train --auto --seclists
  wlf.py train --csv users.csv --wordlist labs/labs_passwords.lst --usernames username_br.lst
  wlf.py train --csv export.csv --uid-col samaccountname --mail-col mail

options:
  -h, --help            show this help message and exit
  --csv FILE            AD export CSV file(s) to train from (can repeat for
                        multiple files)
  --wordlist FILE       Password wordlist file(s) to train from
  --usernames FILE      Username list file(s) to train from
  --auto                Auto-discover and train from known local wordlists
                        (labs/labs_passwords.lst, username_br.lst, etc.)
  --uid-col UID_COL     CSV column name for username/samaccountname (default:
                        userid)
  --eid-col EID_COL     CSV column name for employee ID (default: employeeid)
  --mail-col MAIL_COL   CSV column name for work email (default: workemail)
  --max-rows MAX_ROWS   Max CSV rows to process (0 = all)
  --max-lines MAX_LINES
                        Max lines to read from wordlists (default: 500000)
  --seclists [PATH]     Train from SecLists corpus (auto-discover or specify
                        path)
  --seclists-categories CAT [CAT ...]
                        SecLists categories to train: password username
                        frequency (default: all)
  -o, --output FILE     Output model file (default: .model/pattern_model.json)
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--csv` | [] | no | AD export CSV file(s) to train from (can repeat for multiple files) |
| `--wordlist` | [] | no | Password wordlist file(s) to train from |
| `--usernames` | [] | no | Username list file(s) to train from |
| `--auto` | False | no | Auto-discover and train from known local wordlists (labs/labs_passwords.lst, username_br.lst, etc.) |
| `--uid-col` | 'userid' | no | CSV column name for username/samaccountname (default: userid) |
| `--eid-col` | 'employeeid' | no | CSV column name for employee ID (default: employeeid) |
| `--mail-col` | 'workemail' | no | CSV column name for work email (default: workemail) |
| `--max-rows` | 0 | no | Max CSV rows to process (0 = all) |
| `--max-lines` | 500000 | no | Max lines to read from wordlists (default: 500000) |
| `--seclists` | - | no | Train from SecLists corpus (auto-discover or specify path) |
| `--seclists-categories` | - | no | SecLists categories to train: password username frequency (default: all) |
| `-o, --output` | - | no | Output model file (default: .model/pattern_model.json) |

## Input combinations

- Minimum: `wlf train --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


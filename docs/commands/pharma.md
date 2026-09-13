# `pharma`

Generates wordlists based on common credential patterns in retail chain environments.

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

usage: wlf.py pharma [-h] [--brand BRAND] [--ids IDS] [--cnpj CNPJ]
                     [--abbrevs ABBREVS] [--separators SEPARATORS]
                     [--partners PARTNERS] [--domains DOMAINS]
                     [--mode {passwords,usernames,both}] [--no-padding]
                     [--min-len MIN_LEN] [--max-len MAX_LEN] [-o OUTPUT]

Generates wordlists based on common credential patterns in retail chain environments.

Password patterns:
  abbrev+sep+id       Brand#1206  ABBREV_1206  abbrev1206
  partner+cnpj        system01234567890123
  abbrev+sep+cnpj     AB-01234567890123

Username patterns:
  abbrev+id@domain    XX1206@corp.com  xx0100@corp.com
  IJ/LJ/TC+id         IJ1206  IJ120601  IJ120602  LJ0100

Examples:
  wlf pharma --brand BrandX --ids 1200-1210 -o out.lst
  wlf pharma --brand RetailCo --abbrevs RC,RET --cnpj 01234567890123 --mode passwords
  wlf pharma --brand BrandX --ids 5,6,7,8 --domains corp.example --mode usernames
  wlf pharma --brand BrandX --ids 1206 --partners system,partner --separators @,#

options:
  -h, --help            show this help message and exit
  --brand, -b BRAND     Brand/company name (default: BrandX)
  --ids IDS             Store ID range '1200-1210' or list '1206,1207,1208'
  --cnpj CNPJ           Tax ID(s) comma-separated (e.g. 01234567890123)
  --abbrevs ABBREVS     Extra abbreviations comma-separated (e.g.
                        AB,ABBRV,ABR)
  --separators SEPARATORS
                        Separators comma-separated (default:
                        @,#,!,&,_,-,.,*,'')
  --partners PARTNERS   System/partner prefixes comma-separated (default:
                        system,portal,erp,...)
  --domains DOMAINS     Email domains for usernames comma-separated (e.g.
                        corp.example)
  --mode {passwords,usernames,both}
                        Generation mode: passwords | usernames | both
                        (default: both)
  --no-padding          Skip zero-padded ID variants (0100, 01206...)
  --min-len MIN_LEN     Minimum length of generated entries
  --max-len MAX_LEN     Maximum length of generated entries
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--brand, -b` | 'BrandX' | no | Brand/company name (default: BrandX) |
| `--ids` | - | no | Store ID range '1200-1210' or list '1206,1207,1208' |
| `--cnpj` | - | no | Tax ID(s) comma-separated (e.g. 01234567890123) |
| `--abbrevs` | - | no | Extra abbreviations comma-separated (e.g. AB,ABBRV,ABR) |
| `--separators` | - | no | Separators comma-separated (default: @,#,!,&,_,-,.,*,'') |
| `--partners` | - | no | System/partner prefixes comma-separated (default: system,portal,erp,...) |
| `--domains` | - | no | Email domains for usernames comma-separated (e.g. corp.example) |
| `--mode` | 'both' | no | Generation mode: passwords \| usernames \| both (default: both) |
| `--no-padding` | False | no | Skip zero-padded ID variants (0100, 01206...) |
| `--min-len` | 0 | no | Minimum length of generated entries |
| `--max-len` | 0 | no | Maximum length of generated entries |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf pharma --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 2
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


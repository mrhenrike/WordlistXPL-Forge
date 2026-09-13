# `default-creds`

Query the consolidated default credentials database.

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

usage: wlf.py default-creds [-h] [--vendor VENDOR] [--protocol PROTOCOL]
                            [--category CATEGORY]
                            [--format {combo,user,pass,json}] [--snmp]
                            [--snmp-version {v2,v3}] [--list-vendors]
                            [--list-protocols] [-o OUTPUT]

Query the consolidated default credentials database.

Contains factory-default user:password pairs from 25+ vendors,
SNMP community strings and SNMPv3 defaults.

Sources: RouterXPL-Forge, routersploit, MikrotikAPI-BF.

Examples:
  wlf.py default-creds -o all_defaults.lst
  wlf.py default-creds --vendor mikrotik -o mikrotik.lst
  wlf.py default-creds --vendor huawei --format json
  wlf.py default-creds --snmp -o snmp_communities.lst
  wlf.py default-creds --snmp --snmp-version v3 -o snmpv3.lst
  wlf.py default-creds --format user -o usernames.lst
  wlf.py default-creds --list-vendors

options:
  -h, --help            show this help message and exit
  --vendor VENDOR       Filter by vendor name (partial match)
  --protocol PROTOCOL   Filter by protocol (api, ssh, telnet, http)
  --category CATEGORY   Filter by category (router, printer, ics)
  --format {combo,user,pass,json}
                        Output format (default: combo = user:pass)
  --snmp                Output SNMP community strings instead of credentials
  --snmp-version {v2,v3}
                        SNMP version (default: v2)
  --list-vendors        List all vendors in the database and exit
  --list-protocols      List all protocols in the database and exit
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--vendor` | - | no | Filter by vendor name (partial match) |
| `--protocol` | - | no | Filter by protocol (api, ssh, telnet, http) |
| `--category` | - | no | Filter by category (router, printer, ics) |
| `--format` | 'combo' | no | Output format (default: combo = user:pass) |
| `--snmp` | False | no | Output SNMP community strings instead of credentials |
| `--snmp-version` | 'v2' | no | SNMP version (default: v2) |
| `--list-vendors` | False | no | List all vendors in the database and exit |
| `--list-protocols` | False | no | List all protocols in the database and exit |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf default-creds --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


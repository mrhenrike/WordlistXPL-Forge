# `default-creds`

Query the **local** default credentials corpus under `generated/` (gitignored; not shipped in the public tree).

Place or build: `generated/default-creds.json` (for example via `python3 update_wordlists.py`), or pass `--db`.

## Syntax

```text
usage: wlf.py default-creds [-h] [--vendor VENDOR] [--protocol PROTOCOL]
                            [--category CATEGORY]
                            [--format {combo,user,pass,json}] [--snmp]
                            [--snmp-version {v2,v3}] [--list-vendors]
                            [--list-protocols] [--db DB] [-o OUTPUT]

Query the local default-credentials corpus under generated/
(gitignored; not shipped in the public tree).

Place or build: generated/default-creds.json
  python3 update_wordlists.py

Examples:
  wlf.py default-creds -o all_defaults.lst
  wlf.py default-creds --vendor mikrotik -o mikrotik.lst
  wlf.py default-creds --vendor huawei --format json
  wlf.py default-creds --snmp -o snmp_communities.lst
  wlf.py default-creds --list-vendors
  wlf.py default-creds --db /path/to/default-creds.json -o out.lst
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
| `--db` | `generated/default-creds.json` | no | Path to default-creds JSON |
| `-o, --output` | - | no | Output file |

## Notes

Credential corpora stay local under `generated/`. The public tree ships the generator, not brute-force dumps.

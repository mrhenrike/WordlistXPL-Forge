# Command coverage

Generated from live `wlf.py` argparse. 100% of subparsers plus nested `pcfg`/`markov` modes.

| Command | Help check | Help exit | Valid smoke | Invalid smoke | Status |
|---------|------------|-----------|-------------|---------------|--------|
| (globals) | `wlf --help` | 0 | n/a | n/a | ok |
| charset | `wlf charset --help` | 0 | exit 2 | exit 0 | ok |
| pattern | `wlf pattern --help` | 0 | exit 2 | exit 0 | ok |
| profile | `wlf profile --help` | 0 | exit 0 | exit 1 | ok |
| corp | `wlf corp --help` | 0 | exit 0 | exit 1 | ok |
| corp-users | `wlf corp-users --help` | 0 | exit 0 | exit 1 | ok |
| phone | `wlf phone --help` | 0 | exit 0 | exit 1 | ok |
| scrape | `wlf scrape --help` | 0 | exit 0 | exit 2 | ok |
| ocr | `wlf ocr --help` | 0 | exit 0 | exit 2 | ok |
| extract | `wlf extract --help` | 0 | exit 0 | exit 2 | ok |
| mutate | `wlf mutate --help` | 0 | exit 2 | exit 2 | ok |
| num2text | `wlf num2text --help` | 0 | exit 0 | exit 0 | ok |
| phrase | `wlf phrase --help` | 0 | exit 2 | exit 2 | ok |
| leet | `wlf leet --help` | 0 | exit 0 | exit 2 | ok |
| leet-perm | `wlf leet-perm --help` | 0 | exit 0 | exit 2 | ok |
| xor | `wlf xor --help` | 0 | exit 0 | exit 2 | ok |
| analyze | `wlf analyze --help` | 0 | exit 0 | exit 2 | ok |
| merge | `wlf merge --help` | 0 | exit 0 | exit 2 | ok |
| dns | `wlf dns --help` | 0 | exit 0 | exit 0 | ok |
| pharma | `wlf pharma --help` | 0 | exit 2 | exit 0 | ok |
| sanitize | `wlf sanitize --help` | 0 | exit 0 | exit 2 | ok |
| reverse | `wlf reverse --help` | 0 | exit 0 | exit 2 | ok |
| mangle | `wlf mangle --help` | 0 | exit 0 | exit 0 | ok |
| improve | `wlf improve --help` | 0 | exit 0 | exit 2 | ok |
| maya-rank | `wlf maya-rank --help` | 0 | exit 0 | exit 2 | ok |
| osint-perm | `wlf osint-perm --help` | 0 | exit 0 | exit 0 | ok |
| cupp | `wlf cupp --help` | 0 | exit 0 | exit 0 | ok |
| pattern-rank | `wlf pattern-rank --help` | 0 | exit 0 | exit 2 | ok |
| scrape-target | `wlf scrape-target --help` | 0 | exit 0 | exit 2 | ok |
| default-creds | `wlf default-creds --help` | 0 | exit 0 | exit 0 | ok |
| isp-keygen | `wlf isp-keygen --help` | 0 | exit 0 | exit 0 | ok |
| sysinfo | `wlf sysinfo --help` | 0 | exit 0 | exit 0 | ok |
| corp-prefixes | `wlf corp-prefixes --help` | 0 | exit 0 | exit 0 | ok |
| train | `wlf train --help` | 0 | exit 0 | exit 0 | ok |
| password-dna | `wlf password-dna --help` | 0 | exit 0 | exit 0 | ok |
| combiner | `wlf combiner --help` | 0 | exit 0 | exit 0 | ok |
| pcfg | `wlf pcfg --help` | 0 | exit 0 | exit 0 | ok |
| markov | `wlf markov --help` | 0 | exit 0 | exit 0 | ok |
| kwalk | `wlf kwalk --help` | 0 | exit 0 | timeout | ok |
| rulegen | `wlf rulegen --help` | 0 | exit 0 | exit 0 | ok |
| benchmark | `wlf benchmark --help` | 0 | exit 0 | exit 2 | ok |
| anomaly-score | `wlf anomaly-score --help` | 0 | exit 0 | exit 2 | ok |
| prince | `wlf prince --help` | 0 | exit 0 | exit 2 | ok |
| br-names | `wlf br-names --help` | 0 | exit 0 | exit 0 | ok |
| iwlgen | `wlf iwlgen --help` | 0 | exit 0 | exit 2 | ok |

Total rows: 45. Help failures: 0.

Nested modes (also `--help` exit 0): `pcfg train`, `pcfg generate`, `markov train`, `markov generate`. Pages: `docs/commands/pcfg-train.md`, `pcfg-generate.md`, `markov-train.md`, `markov-generate.md`.

`--limit` is a **global** flag and must appear before the subcommand (`wlf --limit 5 charset 3 3 ab`).

Per-command pages live in `docs/commands/` (en-US) and `docs/pt-BR/commands/`.


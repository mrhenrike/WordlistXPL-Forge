# WordlistXPL-Forge

<p align="center">
  <img src="https://img.shields.io/github/stars/mrhenrike/WordlistXPL-Forge?style=flat-square" alt="GitHub Stars">
  <img src="https://img.shields.io/github/license/mrhenrike/WordlistXPL-Forge?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/pypi/v/wordlistxpl-forge?style=flat-square&logo=pypi&logoColor=white&color=green" alt="PyPI">
</p>

Wordlist generation toolkit for authorized pentest and red team work. Official member of the **XPL-Forge** suite. CLI: `wlf` / `python wlf.py`.

Author: André Henrique (`mrhenrike`) | União Geek | https://uniaogeek.com.br/

> Full command reference (every subcommand, flag, input and output): [docs/COMMAND-COVERAGE.md](docs/COMMAND-COVERAGE.md) · [Wiki](https://github.com/mrhenrike/WordlistXPL-Forge/wiki)

---

## Disclaimer

This program is for **authorized security testing, lab work, and education only**. The author is **not responsible** for misuse of the code or of any function in this toolkit.

The generator emits **many** password and username patterns (names, dates, brands, leet, years, keyboard walks, grammar models, and similar).

If you, your company, or a user build secrets from **public information**, predictable patterns, or personal data (name, team, pet, date, brand, domain), the chance that this tool emits a wordlist containing a **real** password or username is **extremely high, almost certain**.

That is not a leak and does not prove a prior breach. It is weak or predictable secret choice. Use a password manager and MFA.

This repository **does not** distribute a Brazilian password corpus (`wlist_brasil`). It does ship vendor factory default credentials, username samples, and lab lists.

---

## Install

```bash
pip install wordlistxpl-forge
pip install wordlistxpl-forge[full]
```

```bash
git clone https://github.com/mrhenrike/WordlistXPL-Forge.git
cd WordlistXPL-Forge
pip install -r requirements.txt pyyaml
python wlf.py --help
wlf --help
```

Windows: `.\setup_venv.ps1` then `.\.venv\Scripts\Activate.ps1`. Linux/macOS: `chmod +x setup_venv.sh && ./setup_venv.sh`.

## What is in this tree

- Generator CLI (`wlf.py`, `wfh_modules/`)
- Pattern JSON and ISP word banks
- Vendor default credentials (`data/default_credentials.json`, `passwords/default-creds-combo.lst`)
- Username list (`usernames/username_br.lst`)
- Lab lists (`labs/*.lst`) and discovery paths (`fuzzing/discovery_br.lst`)

Coverage matrix: [docs/COMMAND-COVERAGE.md](docs/COMMAND-COVERAGE.md)

## Quick examples

```bash
python wlf.py charset 8 8 --limit 100 -o charset.lst
python wlf.py pattern -t "{company}{year}!" --vars company=BrandX,CorpX year=2020-2026 -o patterns.lst
python wlf.py default-creds --vendor mikrotik --format combo -o mikrotik_creds.lst
python wlf.py dns -d acme.example --words dev staging api admin portal -o subdomains.lst
python wlf.py profile --name "PessoaX" --nick robotx --birth 15/03/1990 --leet aggressive --limit 50 -o target.lst
```

## License

MIT. See [LICENSE](LICENSE).

[Português (Brasil)](README.pt-BR.md)

# WordlistXPL-Forge wiki

Wordlist generator in the XPL-Forge suite. CLI: `wlf` / `python wlf.py`. Version 1.2.0.

Author: Andre Henrique (mrhenrike) | Uniao Geek | https://uniaogeek.com.br/

Portugues: [Home.pt-BR](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/Home.pt-BR)

## Disclaimer

Authorized testing only. The author is not responsible for misuse.

The tool generates many password and username patterns. If secrets are built from public or predictable data, a generated wordlist containing a real password or username is almost certain. That is weak secrets, not a leak.

This repository does not distribute `wlist_brasil`.

## Install

See the README. After clone: `python wlf.py --help`. Optional neural engine: `pip install wordlistxpl-forge[neural]`.

## Reference

- [Command coverage matrix](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/Command-Coverage)
- [Competitive analysis](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/Competitive-Analysis)

## Commands

### Generation

- [charset](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/charset)
- [pattern](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pattern)
- [profile](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/profile)
- [corp](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/corp)
- [corp-users](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/corp-users)
- [corp-prefixes](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/corp-prefixes)
- [phone](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/phone)
- [mutate](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/mutate)
- [num2text](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/num2text)
- [phrase](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/phrase)
- [leet](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/leet)
- [leet-perm](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/leet-perm)
- [combiner](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/combiner)
- [iwlgen](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/iwlgen)
- [br-names](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/br-names)
- [pharma](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pharma)
- [isp-keygen](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/isp-keygen)
- [dns](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/dns)
- [osint-perm](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/osint-perm)
- [cupp](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/cupp)
- [passphrase](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/passphrase)

### Probabilistic and neural models

- [pcfg](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pcfg)
- [markov](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/markov)
- [prince](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/prince)
- [kwalk](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/kwalk)
- [neural](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/neural)

### OSINT and extraction

- [scrape](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/scrape)
- [scrape-target](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/scrape-target)
- [ocr](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/ocr)
- [extract](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/extract)
- [default-creds](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/default-creds)
- [osint](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/osint)

### Rules and list operations

- [rules](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/rules)
- [rulegen](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/rulegen)
- [mangle](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/mangle)
- [dedup](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/dedup)
- [subtract](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/subtract)
- [split](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/split)
- [keyspace](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/keyspace)
- [merge](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/merge)
- [sanitize](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/sanitize)
- [reverse](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/reverse)
- [improve](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/improve)

### Analysis, strength and evaluation

- [analyze](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/analyze)
- [strength](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/strength)
- [pattern-rank](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pattern-rank)
- [maya-rank](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/maya-rank)
- [anomaly-score](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/anomaly-score)
- [benchmark](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/benchmark)
- [password-dna](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/password-dna)
- [evaluate](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/evaluate)
- [curate](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/curate)

### Hashing and crypto

- [hash-id](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/hash-id)
- [hash-gen](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/hash-gen)
- [hcmask](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/hcmask)
- [xor](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/xor)

### Utility and ML

- [train](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/train)
- [sysinfo](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/sysinfo)

Nested modes: `pcfg train`, `pcfg generate`, `markov train`, `markov generate`, `neural train`, `neural generate`.

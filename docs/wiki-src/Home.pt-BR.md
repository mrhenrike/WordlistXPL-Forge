# Wiki WordlistXPL-Forge (pt-BR)

Gerador de wordlists da suite XPL-Forge. CLI: `wlf`. Versao 1.1.0.

Autor: Andre Henrique (mrhenrike) | Uniao Geek | https://uniaogeek.com.br/

English: [Home](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/Home)

## Aviso

Uso apenas em testes autorizados. O autor nao se responsabiliza por uso indevido.

O programa gera muitos padroes de senha e username. Se os segredos vem de informacao publica ou padroes previsiveis, a chance de a wordlist conter uma senha ou username real e altissima. Isso nao e leak.

Este repositorio nao distribui `wlist_brasil`.

## Instalacao

Veja o README. Apos o clone: `python wlf.py --help`. Motor neural opcional: `pip install wordlistxpl-forge[neural]`.

## Referencia

- [Matriz de cobertura](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/Command-Coverage)
- [Analise competitiva](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/Competitive-Analysis)

## Comandos

### Geracao

- [charset](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/charset)
- [pattern](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/pattern)
- [profile](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/profile)
- [corp](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/corp)
- [corp-users](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/corp-users)
- [corp-prefixes](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/corp-prefixes)
- [phone](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/phone)
- [mutate](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/mutate)
- [num2text](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/num2text)
- [phrase](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/phrase)
- [leet](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/leet)
- [leet-perm](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/leet-perm)
- [combiner](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/combiner)
- [iwlgen](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/iwlgen)
- [br-names](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/br-names)
- [pharma](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/pharma)
- [isp-keygen](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/isp-keygen)
- [dns](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/dns)
- [osint-perm](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/osint-perm)
- [cupp](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/cupp)
- [passphrase](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/passphrase)

### Modelos probabilisticos e neural

- [pcfg](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/pcfg)
- [markov](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/markov)
- [prince](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/prince)
- [kwalk](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/kwalk)
- [neural](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/neural)

### OSINT e extracao

- [scrape](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/scrape)
- [scrape-target](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/scrape-target)
- [ocr](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/ocr)
- [extract](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/extract)
- [default-creds](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/default-creds)
- [osint](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/osint)

### Regras e operacoes de lista

- [rules](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/rules)
- [rulegen](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/rulegen)
- [mangle](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/mangle)
- [dedup](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/dedup)
- [subtract](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/subtract)
- [split](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/split)
- [keyspace](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/keyspace)
- [merge](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/merge)
- [sanitize](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/sanitize)
- [reverse](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/reverse)
- [improve](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/improve)

### Analise, forca e avaliacao

- [analyze](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/analyze)
- [strength](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/strength)
- [pattern-rank](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/pattern-rank)
- [maya-rank](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/maya-rank)
- [anomaly-score](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/anomaly-score)
- [benchmark](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/benchmark)
- [password-dna](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/password-dna)
- [evaluate](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/evaluate)
- [curate](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/curate)

### Hashing e cripto

- [hash-id](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/hash-id)
- [hash-gen](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/hash-gen)
- [hcmask](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/hcmask)
- [xor](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/xor)

### Utilidade e ML

- [train](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/train)
- [sysinfo](https://github.com/mrhenrike/WordlistXPL-Forge/wiki/pt-BR/sysinfo)

Modos aninhados: `pcfg train`, `pcfg generate`, `markov train`, `markov generate`, `neural train`, `neural generate`.

# WordlistXPL-Forge

<p align="center">
  <img src="https://img.shields.io/github/stars/mrhenrike/WordlistXPL-Forge?style=flat-square" alt="GitHub Stars">
  <img src="https://img.shields.io/github/license/mrhenrike/WordlistXPL-Forge?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/version-1.1.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/pypi/v/wordlistxpl-forge?style=flat-square&logo=pypi&logoColor=white&color=green" alt="PyPI">
</p>

<p align="center">
  Toolkit unificado de geração de wordlists para pentest autorizado, red team e treinamentos de segurança: <strong>58 subcomandos em uma única CLI</strong>. Membro oficial da suíte <strong>XPL-Forge</strong>. Geração por charset/máscara, profiling pessoal e corporativo, scraping web (JS/CSS/PDF), OCR, parsing de documentos (PDF/XLSX/DOCX), leet speak, XOR crypto, DNS fuzzing, telefones, enumeração de usuários corporativos, padrões de credenciais para redes varejistas, base de credenciais default (IoT/ICS/SCADA/PLC/HMI), keyspace WiFi ISP, análise comportamental password-DNA, combinador de keywords, word mangling, merge e sanitização, ranking ML com corpus SecLists, análise estatística, gramática probabilística PCFG, geração Markov OMEN-style, keyboard walks, auto-geração de regras hashcat, ataque PRINCE, benchmarking de qualidade, gerador por acróstico de frases, motor de mutação de senha existente, dígito-para-texto (EN/PT/BR/ES), permutação OSINT, profiling estilo CUPP, ranking MAYA, anomaly score, filtros globais de comprimento e verificação de espaço em disco. Também executa e converte regras hashcat/John, operações de lista de alta performance (dedup, subtract, split, keyspace), geração neural opcional (estilo FLA/PassGPT), força e entropia estilo zxcvbn com HIBP, identificação e geração de hashes, exportação hcmask, OSINT avançado (Wayback/GitHub org), passphrases diceware e avaliação e curadoria de motores estilo MAYA.
</p>

CLI: `wlf` / `python wlf.py`.

Autor: André Henrique (`mrhenrike`) | União Geek | https://uniaogeek.com.br/

<p align="center">
  <a href="README.md">English</a> · Português (Brasil)
</p>

> **Documentação completa:** [docs/COMMAND-COVERAGE.md](docs/COMMAND-COVERAGE.md) (cada subcomando, flag, entrada e saída) · [Wiki](https://github.com/mrhenrike/WordlistXPL-Forge/wiki)

---

## Aviso legal

**Este repositório destina-se exclusivamente a testes de segurança autorizados, exercícios de red team, laboratório e educação.** Uso não autorizado contra sistemas que você não possui ou não tem permissão escrita para testar é **ilegal**. O autor não se responsabiliza por uso indevido do código nem das funções.

O gerador emite **muitos** padrões de senha e username (nome, data, marca, leet, ano, teclado, gramática e similares). Se você, sua empresa ou um usuário montam segredos a partir de **informação pública**, padrões previsíveis ou dados pessoais (nome, time, pet, data, marca, domínio), a chance de o programa emitir uma wordlist com uma senha ou username **real** é **altíssima, quase certa**.

Isso não é leak e não prova comprometimento prévio. É senha fraca ou previsível. Use gerenciador de senhas e MFA.

Este tree público entrega o **mesmo gerador**. **Não** distribui o corpus brasileiro de senhas (`wlist_brasil`) e **não** traz wordlists corporativas de OSINT do operador. Distribui credenciais default de fabricantes, amostras de username, listas de lab e paths de discovery. Passe `--vars`, `--domain`, `--brand`, `--name` (e flags equivalentes) com dados do **seu** engajamento autorizado.

---

## Quick Start

### Instalar via pip

```bash
pip install wordlistxpl-forge              # core
pip install wordlistxpl-forge[full]        # todos os extras (OCR, docs, scrape)
pip install wordlistxpl-forge[ocr]         # só OCR
pip install wordlistxpl-forge[docs]        # extração PDF/XLSX/DOCX
pip install wordlistxpl-forge[scrape]      # parsers extras de scrape
```

```bash
wlf --help
pip show wordlistxpl-forge
```

### Ou clonar o repositório

```bash
git clone https://github.com/mrhenrike/WordlistXPL-Forge.git
cd WordlistXPL-Forge

pip install -r requirements.txt pyyaml

# Linux / macOS / Termux
chmod +x setup_venv.sh && ./setup_venv.sh && source .venv/bin/activate

# Windows PowerShell
.\setup_venv.ps1; .\.venv\Scripts\Activate.ps1
```

### Executar

```bash
python wlf.py              # menu interativo
python wlf.py --help       # ajuda completa (58 subcomandos)
wlf --help                 # após pip install
```

Metadados de empacotamento ficam locais (`pyproject.toml` não vai no git). Prefira `pip install wordlistxpl-forge` ou rode `python wlf.py` neste tree.

Páginas por comando: [docs/commands/](docs/commands/) (en-US) e [docs/pt-BR/commands/](docs/pt-BR/commands/).

---

## Subcomandos

| # | Comando | Descrição |
|---|---------|-----------|
| 1 | `charset` | Geração por charset/máscara (estilo crunch + hashcat) |
| 2 | `pattern` | Geração por template com variáveis |
| 3 | `profile` | Profiling pessoal (wizard estilo CUPP) |
| 4 | `corp` | Profiling corporativo |
| 5 | `corp-users` | Geração de users/senhas corporativos (50+ padrões) |
| 6 | `phone` | Wordlists de telefone (BR, US, UK) |
| 7 | `scrape` | Web scraping (estilo CeWL/CeWLeR) com extração JS/CSS/PDF |
| 8 | `ocr` | Extração OCR de imagens |
| 9 | `extract` | Extração de PDF/XLSX/DOCX |
| 10 | `mutate` | Motor de mutação de senha existente (case / leet / prefixo / sufixo) |
| 11 | `num2text` | Dígito-para-texto (EN/PT/BR/ES) |
| 12 | `phrase` | Gerador por acróstico de frase (estilo `@0x90`) |
| 13 | `leet` | Permutações leet speak |
| 14 | `leet-perm` | Permutação leet cartesiana sobre wordlist (estilo elpscrk) |
| 15 | `xor` | XOR encrypt/decrypt/brute-force |
| 16 | `analyze` | Análise estatística (estilo pipal) |
| 17 | `merge` | Merge e deduplicação |
| 18 | `dns` | DNS/subdomain fuzzing (estilo alterx) |
| 19 | `pharma` | Padrões de credenciais varejo/farmácia (marca+id, sistema+CNPJ) |
| 20 | `sanitize` | Limpeza e normalização |
| 21 | `reverse` | Inversão de linhas |
| 22 | `mangle` | Regras de word mangling |
| 23 | `improve` | Enriquece wordlist existente com leet, anos e especiais |
| 24 | `maya-rank` | Ranking por probabilidade MAYA |
| 25 | `osint-perm` | Permutações de senha a partir de perfil OSINT |
| 26 | `cupp` | Geração alvo-específica estilo CUPP |
| 27 | `pattern-rank` | Keyboard walks, meses PT-BR, máscaras Hashcat |
| 28 | `scrape-target` | Crawl leve de URL para extração de palavras |
| 29 | `default-creds` | Consulta base de credenciais default (IoT/routers/impressoras/ICS) |
| 30 | `isp-keygen` | Gerador de keyspace WiFi padrão de ISPs |
| 31 | `sysinfo` | Info de hardware e compute |
| 32 | `corp-prefixes` | Prefixos corporativos (MSP/SOC/DevOps) |
| 33 | `train` | Treinar modelo ML (local + corpus SecLists) |
| 34 | `password-dna` | Análise de padrões e variantes comportamentais |
| 35 | `combiner` | Combinador de keywords |
| 36 | `pcfg` | Gramática probabilística PCFG: treino e geração (Weir et al.) |
| 37 | `markov` | Gerador Markov posicional estilo OMEN |
| 38 | `kwalk` | Keyboard walk (estilo kwprocessor) |
| 39 | `rulegen` | Auto-geração de arquivos `.rule` hashcat |
| 40 | `benchmark` | Benchmarking de qualidade (métricas MAYA) |
| 41 | `anomaly-score` | Ranking por anomalia (mais incomum primeiro) |
| 42 | `prince` | Ataque PRINCE: combinação encadeada |
| 43 | `br-names` | Usernames a partir de nomes brasileiros (listas locais opcionais) |
| 44 | `iwlgen` | Permutação de keywords (intelligence-wordlist-generator) |
| 45 | `rules` | Aplica, converte ou otimiza regras hashcat/John (equivalente a `--stdout -r`) |
| 46 | `dedup` | Deduplicação sem ordenar, preservando ordem (Bloom opcional) |
| 47 | `subtract` | Remove entradas presentes em outros arquivos (estilo rli) |
| 48 | `split` | Particiona por contagem, tamanho ou comprimento (estilo splitlen) |
| 49 | `keyspace` | Estima contagem de candidatos e tempo para exaurir |
| 50 | `neural` | Geração neural em nível de caractere, amostragem guiada e DPG (extra `[neural]`) |
| 51 | `strength` | Força e entropia estilo zxcvbn, crack time, HIBP opcional |
| 52 | `hash-id` | Identifica tipos prováveis de hash |
| 53 | `hash-gen` | Gera hashes para corpora de teste (md5/sha/ntlm/bcrypt/argon2/...) |
| 54 | `hcmask` | Exporta um `.hcmask` do hashcat a partir de uma wordlist |
| 55 | `osint` | OSINT avançado (Wayback, GitHub org, NER, enriquecimento LLM opcional) |
| 56 | `passphrase` | Geração de passphrases diceware/mnemônicas (CSPRNG) |
| 57 | `evaluate` | Compara motores por guess-number e cobertura (estilo MAYA) |
| 58 | `curate` | Ranqueia listas por crack rate e funde as melhores (estilo weakpass) |

Modos aninhados (também documentados): `pcfg train`, `pcfg generate`, `markov train`, `markov generate`, `neural train`, `neural generate`.

> **Sintaxe e exemplos de cada subcomando:** [docs/COMMAND-COVERAGE.md](docs/COMMAND-COVERAGE.md) · [Wiki](https://github.com/mrhenrike/WordlistXPL-Forge/wiki)

### Flags globais

Flags globais vêm **antes** do subcomando.

```bash
python wlf.py --threads 20 --compute cuda --no-ml --min-len 8 --max-len 20 --limit 100000 charset 8 12
```

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--threads N` | `5` | Threads de trabalho (1-300) |
| `--compute MODE` | `auto` | `auto` / `cpu` / `gpu` / `cuda` / `rocm` / `mps` / `hybrid` |
| `--no-ml` | off | Desabilitar ranking ML |
| `--limit N` | `0` | Parar após N entradas (`0` = ilimitado) |
| `--timeout SECS` | `0` | Parar após SECS (`0` = ilimitado) |
| `--min-len N` | `0` | Filtro global de comprimento mínimo |
| `--max-len N` | `0` | Filtro global de comprimento máximo |
| `--lang LOCALE` | `en` | `en` / `pt-br` / `pt-pt` / `es` |
| `-v` | off | Logging detalhado |

`--limit` é global. Exemplo: `wlf --limit 5 charset 3 3 ab`.

---

## Exemplos mais comuns

Os exemplos usam placeholders (`acme`, `xpto`, `brandx`, `corpx`, `pessoax`, `personay`, `robotx`). Troque pelos dados do **seu** engajamento autorizado.

### Pentest corporativo: gerar users + senhas

```bash
python wlf.py corp-users --domain acme.example --file funcionarios.txt --passwords --combo -o acme_combo.lst
```

### Profiling de alvo pessoal

```bash
python wlf.py profile --name "PessoaX" --nick robotx --birth 15/03/1990 --leet aggressive -o alvo.lst
python wlf.py cupp --first-name PessoaX --last-name PersonY --company BrandX -o cupp.lst
python wlf.py osint-perm --first-name PessoaX --last-name PersonY --nick robotx --birth 01/1990 --complexity 2 -o osint.lst
```

### Charset com máscara hashcat

```bash
python wlf.py charset 8 8 --mask "?u?l?l?l?d?d?d?s" -o senhas.lst
```

### Geração por template

```bash
python wlf.py pattern -t "{company}{year}!" --vars company=acme,xpto,brandx year=2020-2026 -o patterns.lst
```

### Fuzzing de subdomínios DNS

```bash
python wlf.py dns -d acme.example --words dev staging api admin portal -o subdomains.lst
```

### Analisar uma wordlist existente

```bash
python wlf.py analyze senhas.lst --top 30 --masks --format json -o analise.json
```

### Consultar credenciais default

```bash
python wlf.py default-creds --list-vendors
python wlf.py default-creds --vendor mikrotik --format combo -o mikrotik_creds.lst
python wlf.py default-creds --protocol snmp --format user -o snmp_users.lst
```

### Geração de keyspace WiFi ISP

```bash
python wlf.py isp-keygen --list
python wlf.py isp-keygen --isp xfinity_comcast --estimate
python wlf.py isp-keygen --isp xfinity_comcast --limit 100000 -o xfinity.lst
```

### Web scraping com JS/CSS/PDF

```bash
python wlf.py scrape https://acme.example --include-js --include-css --include-pdf --lowercase -o palavras.lst
python wlf.py scrape https://acme.example --emails --output-emails emails.txt --output-urls urls.txt
python wlf.py scrape-target --url https://acme.example --depth 2 --max-pages 20 -o crawl.lst
```

### Merge, sanitização, improve

```bash
python wlf.py merge lista1.lst lista2.lst --min-len 6 --sort -o merged.lst
python wlf.py sanitize merged.lst --inplace
python wlf.py improve merged.lst --leet aggressive --year-start 2020 --year-end 2027 -o improved.lst
python wlf.py leet-perm palavras.lst --max-per-word 256 -o leet_words.lst
```

### Permutação de keywords

```bash
python wlf.py combiner --keywords admin,router,brandx -o combo.lst
python wlf.py iwlgen --keywords admin,router,2026 --connectors @. --leet -o iwl.lst
```

> **Matriz de cobertura e páginas por flag:** [docs/COMMAND-COVERAGE.md](docs/COMMAND-COVERAGE.md)

---

## Password DNA

Analise padrões de senhas e gere variantes comportamentais. O subcomando `password-dna` extrai o "DNA" estrutural (posições de maiúsculas, minúsculas, dígitos e símbolos) e produz candidatos que seguem os mesmos padrões.

```bash
python wlf.py password-dna --input senhas_conhecidas.lst --depth 2 -o dna_variantes.lst
python wlf.py password-dna --seed "BrandX2024!" --depth 3 --leet -o seed_variantes.lst
python wlf.py password-dna --input senhas_conhecidas.lst --analyze-only --format json -o dna_relatorio.json
```

---

## Motor PCFG (gramática probabilística)

Treina uma gramática probabilística a partir de corpus de senhas e gera candidatos em **ordem de probabilidade**. Baseado em Weir et al. (IEEE S&P 2009).

```bash
python wlf.py pcfg train --wordlist rockyou.txt
python wlf.py pcfg generate -o candidatos.lst --limit 1000000
python wlf.py pcfg generate --top-structures 50 --top-terminals 100 --min-len 8
```

## Gerador Markov (OMEN-style)

Cadeia de Markov posicional estilo OMEN. Aprende transições por posição e gera em ordem crescente de custo.

```bash
python wlf.py markov train --wordlist leaked.txt --order 3
python wlf.py markov generate --min-len 6 --max-len 12 --max-cost 30 --limit 500000
```

## Gerador de keyboard walk

Senhas por adjacência no teclado físico. Layouts QWERTY, AZERTY, QWERTZ, Dvorak e numpad.

```bash
python wlf.py kwalk --min-len 4 --max-len 10 -o walks.lst
python wlf.py kwalk --layout qwerty,numpad --no-shift --max-changes 2
python wlf.py kwalk --list-layouts
```

## Auto-geração de regras Hashcat

Analisa senhas e gera arquivos `.rule` compatíveis com hashcat.

```bash
python wlf.py rulegen --wordlist leaked.txt -o rules.rule --top-rules 200
python wlf.py rulegen --wordlist passwords.lst --dictionary english.txt -o optimized.rule
```

## Ataque PRINCE

PRINCE (PRobability INfinite Chained Elements) combina múltiplas palavras. Descobre senhas multi-word como `correcthorsebatterystaple`.

```bash
python wlf.py prince --wordlist top1000.txt --min-elem 2 --max-elem 4 -o prince.lst
python wlf.py prince --wordlist words.txt --separator "-" --case-permute --min-len 8
```

## Benchmark de qualidade

Hit rate, eficiência, diversidade, cobertura por comprimento/charset e tempos estimados de crack.

```bash
python wlf.py benchmark --wordlist gerada.lst --reference rockyou_sample.txt
python wlf.py benchmark --wordlist output.lst --reference test_set.txt --json relatorio.json
python wlf.py maya-rank gerada.lst --top 1000 -o ranked.lst
python wlf.py anomaly-score labs/labs_passwords.lst --top 50
python wlf.py pattern-rank senhas.lst --layout qwerty
```

---

## Motor de regras

Executa regras hashcat e John contra uma wordlist (equivalente a `hashcat --stdout -r`), converte entre os dois dialetos e otimiza arquivos de regras.

```bash
python wlf.py rules apply --wordlist base.txt --rules best64.rule -o out.lst
python wlf.py rules apply --wordlist base.txt --rule "c $1;so0;u" --dedupe
python wlf.py rules convert --rules hc.rule --to john -o jtr.rule
python wlf.py rules optimize --rules messy.rule -o clean.rule
```

## Operações de lista de alta performance

Utilitários em streaming para listas muito grandes: dedup preservando ordem (Bloom opcional), subtração, particionamento e estimativa de keyspace.

```bash
python wlf.py dedup huge.txt --bloom --capacity 50000000 -o unique.txt
python wlf.py subtract candidatos.txt --remove cracked.txt -o restante.txt
python wlf.py split big.txt --lines 1000000 -o part
python wlf.py split words.txt --by-length -o bylen
python wlf.py keyspace --mask "?u?l?l?l?d?d?d?d" --pps 5e9
```

## Geração neural (extra opcional `[neural]`)

Geração neural em nível de caractere na tradição FLA e PassGPT. Requer `pip install wordlistxpl-forge[neural]` (torch, e transformers para adapters PassGPT). O core segue funcionando com `pcfg` e `markov` sem este extra.

```bash
python wlf.py neural train --wordlist rockyou.txt --epochs 5
python wlf.py --limit 100000 neural generate --temperature 0.9 -o out.lst
python wlf.py --limit 5000 neural generate --prefix admin --mask "?u?l?l?l?d?d"
python wlf.py --limit 100000 neural generate --adapt cracked.txt   # Dynamic Password Guessing
python wlf.py --limit 5000 neural generate --adapter passgpt --model javirandor/passgpt-10characters
```

## Força e entropia de senha

Pontuação estilo zxcvbn com detecção de padrões (dicionário, l33t, sequências, repetições, teclado, datas), entropia, crack time por cenário e por hash, e checagem HIBP opcional via k-anonymity.

```bash
python wlf.py strength "Verao2024!"
python wlf.py strength "P@ssw0rd" --hibp
python wlf.py strength --wordlist candidatos.txt -o scored.tsv
```

## Hashing e interop de cracking

Identifica hashes, gera digests para corpora de teste e exporta masks do hashcat.

```bash
python wlf.py hash-id 5f4dcc3b5aa765d61d8327deb882cf99
python wlf.py hash-gen --wordlist pw.txt --algo ntlm --format hash:plain -o ntlm.txt
python wlf.py hash-gen --wordlist pw.txt --algo bcrypt --format plain:hash
python wlf.py hcmask --wordlist leaked.txt --top 50 -o masks.hcmask
```

## OSINT avançado e passphrases

Constrói wordlists contextuais a partir de OSINT passivo (Wayback Machine, organizações do GitHub) com NER leve e enriquecimento LLM opcional, e gera passphrases diceware com fonte aleatória segura.

```bash
python wlf.py osint --wayback example.com --github-org acme --enrich -o rich.lst
python wlf.py osint --github-org acme --lowercase -o org.lst
python wlf.py passphrase --words 5 --separator . --capitalize --number
python wlf.py passphrase --wordlist eff_large_wordlist.txt --words 6 --symbol
```

## Avaliação e curadoria de motores

Compara motores por guess-number e cobertura contra um split de teste (estilo MAYA), e ranqueia listas candidatas por crack rate para fundir as melhores (estilo weakpass).

```bash
python wlf.py evaluate --candidates pcfg.lst markov.lst --labels pcfg,markov --reference test.txt
python wlf.py curate --candidates a.txt b.txt c.txt --reference test.txt --top-k 2 -o best.txt
```

Veja a análise competitiva e a paridade de recursos em [docs/pt-BR/COMPETITIVE-ANALYSIS.md](docs/pt-BR/COMPETITIVE-ANALYSIS.md).

---

## Base de credenciais default

Base integrada com **1.506** credenciais de fábrica cobrindo **88 vendors** (mais comunidades SNMP): routers, switches, impressoras, câmeras IP, ICS/SCADA (PLCs, HMIs, RTUs), gateways IoT e mais.

```bash
python wlf.py default-creds --list-vendors
python wlf.py default-creds --vendor siemens --format combo -o siemens_creds.lst
python wlf.py default-creds --protocol modbus --format user -o modbus_users.lst
python wlf.py default-creds --category ics --format combo -o ics_defaults.lst
python wlf.py default-creds --export-all --format json -o all_defaults.json
```

---

## Frase, mutação, varejo, dígito-para-texto

### Acróstico de frase

```bash
python wlf.py phrase "minha frase secreta corporativa" -o frase.lst
python wlf.py phrase "minha frase secreta corporativa" --prefixes _,__ --suffixes @0x90,#0x90 -o frase.lst
```

### Mutação de senha existente

```bash
python wlf.py mutate "Verao2024" -o mutacoes.lst
python wlf.py mutate "admin123" --leet-mode aggressive --min-len 10 --max-len 25 -o mutacoes.lst
```

### Padrões de redes varejistas

`--brand` e `--ids` vêm do **seu** engajamento. Os exemplos abaixo são placeholders.

```bash
python wlf.py pharma --brand BrandX --ids 1200-1210 -o pharma.lst
python wlf.py pharma --brand CorpX --abbrevs CX,COR --cnpj 00000000000000 --mode passwords
python wlf.py pharma --brand BrandX --ids 1000-2000 --domains acme.example --mode usernames
```

### Dígito-para-texto

Números (até 12 dígitos) em texto com variantes de case/leet/separador. EN, PT, BR (formas femininas) e ES.

```bash
python wlf.py num2text --number 123
python wlf.py num2text --number 12 --lang br
python wlf.py num2text --number 123 --lang es
python wlf.py num2text --range 0-9999 --lang pt -o numeros_pt.lst
python wlf.py num2text --range 2000-2030 --lang br -o anos_br.lst
```

| Código | Aceita também | Idioma |
|--------|--------------|--------|
| `en` | `en-us`, `en-gb` | Inglês (padrão) |
| `pt` | `pt-pt` | Português europeu |
| `br` | `pt-br` | Português brasileiro |
| `es` | `es-es`, `es-mx`, `es-la` | Espanhol |

### Filtros globais de comprimento

```bash
python wlf.py --min-len 8 --max-len 20 charset 8 12 -o filtrado.lst
python wlf.py --min-len 10 mutate "admin" -o variantes_longas.lst
```

---

## O que este tree distribui

| Arquivo | Descrição | Entradas |
|---------|-----------|----------|
| `data/default_credentials.json` | Base estruturada (1.506 entradas, 88 vendors, SNMP) | n/a |
| `passwords/default-creds-combo.lst` | Combos `user:password` default (routers, impressoras, ICS/SCADA) | ~3,1K |
| `usernames/username_br.lst` | Usernames brasileiros e globais | ~1,7K |
| `fuzzing/discovery_br.lst` | Paths de descoberta web e API fuzzing | ~900 |
| `labs/*.lst` | Wordlists de workshop e treino | pequenas |
| `data/behavior_patterns.json` | Padrões estruturais de geração (não é lista de empresas) | n/a |
| `data/corp_prefix_patterns.json` | Templates genéricos de prefixo de username | n/a |

**Fora deste tree:** `passwords/wlist_brasil.lst` (corpus brasileiro de senhas) e qualquer wordlist corporativa de OSINT do operador. A CLI **ainda gera** essas famílias de padrão a partir das flags que você passa.

`br-names` pode carregar um diretório BRWordList local com `--brwordlist-path`. Esse corpus não vem empacotado aqui.

---

## Minha senha está nestas listas?

Este repositório não distribui `wlist_brasil`. Dá para checar defaults, labs ou a **sua** saída gerada:

```bash
# Linux/macOS: defaults de fábrica
grep -qxF 'admin:admin' passwords/default-creds-combo.lst && echo "ENCONTRADA" || echo "Não encontrada"

# Sua wordlist gerada
grep -qxF 'SuaSenha' generated/output.lst && echo "ENCONTRADA" || echo "Não encontrada"

# Windows PowerShell
Select-String -Path passwords\default-creds-combo.lst -Pattern '^admin:admin$' -SimpleMatch -Quiet
```

Se um segredo **real** bater com um candidato gerado: troque, habilite MFA e use gerenciador de senhas. Isso é construção previsível, não dump deste repositório.

---

## Modelo ML

Modelo leve que ranqueia candidatos por probabilidade de padrão estrutural. Treine com dados locais ou com o corpus SecLists:

```bash
python wlf.py train --auto
python wlf.py train --seclists
python wlf.py train --auto --seclists
python wlf.py train --seclists /path/to/SecLists --seclists-categories password frequency
```

O modelo armazena **apenas padrões estruturais**: sem PII, senhas ou nomes de empresa.

---

## Disclaimer ético

Se uma senha sua ou da sua organização aparece numa wordlist **gerada** daqui, ela bateu com regras determinísticas da metodologia, não foi extraída de sistema nenhum. Qualquer operador com os mesmos algoritmos publicamente documentados constrói as mesmas entradas.

**Não use padrões desta lista como credenciais reais. Use um gerenciador de senhas.**

---

## Créditos e inspiração

| Projeto | Inspiração |
|---------|------------|
| [CUPP](https://github.com/Mebus/cupp) | Profiling pessoal |
| [Crunch](https://github.com/jim3ma/crunch) | Geração por charset |
| [CeWL](https://github.com/digininja/CeWL) | Web scraping |
| [CeWLeR](https://github.com/roys/cewler) | Web scraping moderno em Python (JS/CSS/PDF) |
| [routersploit](https://github.com/threat9/routersploit) | Credenciais default IoT/routers |
| [alterx](https://github.com/projectdiscovery/alterx) | DNS/subdomain fuzzing |
| [pipal](https://github.com/digininja/pipal) | Análise estatística |
| [SecLists](https://github.com/danielmiessler/SecLists) | Listas curadas |
| [elpscrk](https://github.com/D4Vinci/elpscrk) | Geração por permutação |
| [BEWGor](https://github.com/berzerk0/BEWGor) | Gerador biográfico |
| [pnwgen](https://github.com/toxydose/pnwgen) | Geração de telefones |
| [intelligence-wordlist-generator](https://github.com/MichaelDim02/intelligence-wordlist-generator) | Combinador de keywords |
| [SCaDAPass](https://github.com/scadastrangelove/SCaDAPass) | Credenciais default ICS/SCADA |
| [pcfg_cracker](https://github.com/lakiw/pcfg_cracker) | Gramática probabilística PCFG (Weir et al.) |
| [OMEN](https://github.com/RUB-SysSec/OMEN) | Ordered Markov ENumerator |
| [kwprocessor](https://github.com/hashcat/kwprocessor) | Keyboard walks |
| [PACK](https://github.com/iphelix/pack) | Password Analysis and Cracking Kit (rulegen) |
| [princeprocessor](https://github.com/hashcat/princeprocessor) | Modo de ataque PRINCE |
| [MAYA](https://github.com/williamcorrias/MAYA-Password-Benchmarking) | Framework de benchmarking de wordlists |
| [hashcat](https://github.com/hashcat/hashcat) | Sintaxe do motor de regras e tokens de mask |
| [hashcat-utils](https://github.com/hashcat/hashcat-utils) | Operações de lista (splitlen, rli, rules_optimize) |
| [rling](https://github.com/Cynosureprime/rling) / [duplicut](https://github.com/nil0x42/duplicut) | Dedup e subtração de alta performance |
| [John the Ripper](https://github.com/openwall/john) | Dialeto de regras para conversão |
| [zxcvbn](https://github.com/dropbox/zxcvbn) / [zxcvbn-ts](https://github.com/zxcvbn-ts/zxcvbn) | Estimativa de força e entropia |
| [Have I Been Pwned](https://haveibeenpwned.com/Passwords) | Checagem de vazamento por k-anonymity |
| [PassGPT](https://github.com/javirandor/passgpt) | Modelagem de senha por transformer (adapter) |
| [FLA](https://github.com/cupslab/neural_network_cracking) | Adivinhação de senha neural (LSTM) |
| [name-that-hash](https://github.com/HashPals/Name-That-Hash) | Identificação de hash |
| [CeWLeR / cewlai](https://github.com/chocapikk/cewlai) | Wordlists OSINT assistidas por IA |
| [WordForge](https://pypi.org/project/wordforge/) | Coletores OSINT (Wayback, GitHub org, NER) |
| [EFF Diceware](https://www.eff.org/dice) | Geração de passphrases |
| [weakpass](https://weakpass.com/) | Ranqueamento por crack-rate e curadoria |

---

## Contato

- **Suporte / dúvidas gerais:** [suporte@uniaogeek.com.br](mailto:suporte@uniaogeek.com.br)
- **Segurança:** [SECURITY.md](SECURITY.md)
- **Organização:** [União Geek](https://github.com/Uniao-Geek)

## Licença

[MIT License](LICENSE) - Copyright (c) 2026 André Henrique ([@mrhenrike](https://github.com/mrhenrike))

---

<p align="center">
  <strong>Autor:</strong> André Henrique (<a href="https://github.com/mrhenrike">@mrhenrike</a>) | <a href="https://github.com/Uniao-Geek">União Geek</a><br>
  <a href="mailto:suporte@uniaogeek.com.br">suporte@uniaogeek.com.br</a>
</p>

<p align="center">
  <a href="README.md">English version</a> · <a href="docs/COMMAND-COVERAGE.md">Cobertura de comandos</a> · <a href="https://github.com/mrhenrike/WordlistXPL-Forge/wiki">Wiki</a>
</p>

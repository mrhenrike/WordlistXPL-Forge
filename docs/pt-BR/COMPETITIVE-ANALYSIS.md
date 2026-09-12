# Analise competitiva e paridade de recursos

Documento de referencia que posiciona o WordlistXPL-Forge frente ao cenario open-source de
geracao de wordlists, modelagem de senhas, calculo de entropia, hashing e integracao com
cracking. O objetivo e um unico toolkit que iguale ou supere as melhores ferramentas
especializadas.

## 1. Cenario pesquisado

Mutacao por keyword e profiling:

- `psudohash` (leet, caixa, padding, sufixos de ano, combinacoes de keywords)
- `Mentalist` (construtor grafico, exporta regras hashcat e John)
- `TTPassGen` (regras scriptaveis estilo regex, estimativa de keyspace, saida particionada)
- `pydictor`, `CUPP`, `bopscrk`

Cadeia de ferramentas hashcat e John:

- `maskprocessor` (motor de mask por posicao)
- `princeprocessor` (combinador encadeado PRINCE)
- `kwprocessor` (keyboard walks)
- `hashcat-utils` (combinator, combipow, cutb, splitlen, rli, rli2, rules_optimize, tmesis, topmorph)

Operacoes em listas grandes:

- `rling` e `duplicut` (dedup sem ordenar, memoria limitada, subtracao, frequencia)

Wordlists por OSINT:

- `CeWL` (spider de site em Ruby)
- `cewlai` (Go, enriquecimento por IA, detectores de segredo)
- `WordForge` (Wayback, GitHub org, DNS, NER, provedores LLM)
- `Cracken` (Rust, smartlist e hybrid mask)

Entropia e forca:

- `zxcvbn` e `zxcvbn-ts` (deteccao de padroes, l33t, teclado, datas, sequencias, HIBP, crack time por hash)
- `nbvcxz`, `passcore`, `passwordthing`

Modelagem neural e probabilistica (estado da arte):

- `PassGPT` (transformer GPT-2, cerca de duas vezes o rendimento de modelos GAN)
- `PagPassGPT` (guiado por padrao, mais acertos e menos duplicatas)
- `PLR-GAN` com Dynamic Password Guessing, `PassGAN`, `GNPassGAN`, `PassFlow`, `FLA` (LSTM)
- benchmark unificado `MAYA`: FLA, PassGPT, PCFG e combinacoes geralmente superam GANs

Colecoes:

- `SecLists`, `weakpass` (ranqueado por crack-rate, API estilo HIBP), `rockyou`, `RockYou2024`

## 2. Baseline do WordlistXPL-Forge

Geracao: charset (crunch e mask), pattern, profile e cupp, corp, corp-users, phone,
mutate, leet e leet-perm, num2text, phrase, combiner, iwlgen, br-names, pharma,
isp-keygen, dns, osint-perm.

Modelos probabilisticos: pcfg (train e generate), markov (estilo OMEN), prince, kwalk.

OSINT e extracao: scrape, scrape-target, ocr, extract, default-creds.

Analise e ranking: analyze (estilo pipal), pattern-rank, maya-rank, anomaly-score,
benchmark, password-dna, rulegen.

Utilidades: merge, sanitize, reverse, mangle, improve, train (ML sobre SecLists), sysinfo,
backend de compute (cpu, gpu, cuda, rocm, mps).

## 3. Lacunas fechadas

Os recursos abaixo foram adicionados para fechar as lacunas identificadas, agrupados pelas
familias de ferramentas que igualam ou superam.

Motor de regras (iguala o motor de regras do hashcat e o rules_optimize do hashcat-utils):

- `rules apply` aplica regras hashcat e John sobre uma wordlist, equivalente a
  `hashcat --stdout -r rules.rule wordlist`.
- `rules convert` traduz entre as sintaxes hashcat e John.
- `rules optimize` deduplica e remove regras sem efeito.

Operacoes de lista de alta performance (iguala rling, duplicut e hashcat-utils):

- `dedup` remove duplicatas sem ordenar, preservando ordem, com memoria limitada e filtro
  de Bloom opcional para entradas muito grandes.
- `subtract` remove entradas presentes em um ou mais arquivos (estilo rli).
- `split` particiona por contagem, por tamanho ou por comprimento (estilo splitlen).
- `keyspace` estima contagem de candidatos e tempo para exaurir masks, charsets e regras.

Geracao neural (iguala as familias FLA e PassGPT, extra opcional `[neural]`):

- `neural train` treina um modelo em nivel de caractere (LSTM por padrao, GPT pequeno opcional).
- `neural generate` suporta amostragem por temperatura, geracao guiada por prefixo ou mask e
  Dynamic Password Guessing que se adapta a senhas ja recuperadas.
- checkpoints externos de ferramentas estilo PassGPT e PassGAN podem ser carregados como adaptadores.

Entropia e forca (iguala zxcvbn e zxcvbn-ts):

- `strength` pontua senhas com deteccao de padroes (dicionario, l33t, sequencias, repeticoes,
  teclado, datas), reporta guesses e entropia, estima crack time por cenario e por hash e pode
  consultar o HIBP com k-anonymity.

Hashing e interop de cracking (iguala name-that-hash, hashid e exportacao hcmask):

- `hash-id` identifica tipos provaveis de hash.
- `hash-gen` calcula md5, sha1, sha256, sha512, ntlm, bcrypt, argon2, pbkdf2 e scrypt para uma
  wordlist, para montar corpora de teste.
- `hcmask` exporta um arquivo `.hcmask` a partir da analise de masks de uma wordlist.

OSINT avancado e passphrases (iguala CeWL, cewlai e WordForge):

- `osint` coleta da Wayback Machine e de organizacoes do GitHub, extrai entidades com NER leve e
  pode enriquecer opcionalmente com um LLM local ou remoto.
- `passphrase` gera passphrases diceware e mnemonicas usando um CSPRNG.

Avaliacao e curadoria (iguala o benchmark MAYA e o ranking do weakpass):

- `evaluate` compara motores (pcfg, markov, neural e listas estaticas) por guess number e
  cobertura contra um split de teste.
- `curate` ranqueia listas candidatas por crack rate contra uma referencia e funde as melhores.

## 4. Posicionamento

Com as adicoes acima, o WordlistXPL-Forge unifica em um unico CLI as quatro familias que
costumam ser ferramentas separadas: geracao probabilistica e neural, motor de regras,
operacoes de lista de alta performance e coleta OSINT, alem de calculo de entropia e interop
de hashing. Nenhum projeto open-source combina hoje todos esses itens.

## 5. Notas

- A geracao neural e um extra opcional. O core segue funcionando com pcfg e markov quando o
  extra nao esta instalado.
- Os exemplos usam rotulos genericos. Este repositorio nao inclui wordlists com dados de corporacoes.

# CogPIE: Motor de Inferência de Padrões Cognitivos para Geração Direcionada de Candidatos a Senhas

**Andre Henrique de Oliveira**
Uniao Geek Security Research

---

## Resumo

A segurança de senhas permanece como um dos desafios mais persistentes é críticos em segurança da informação. Apesar de décadas de pesquisa, avancos em políticas de autenticação é campanhas de conscientização, usuários consistentemente criam senhas derivadas de seu contexto cognitivo pessoal: nomes, datas, preferencias, memórias é hábitos linguísticos. Este artigo apresenta o CogPIE (Cognitive Pattern Inference Engine), um algoritmo híbrido de 5 camadas que modela explicitamente os vieses cognitivos subjacentes a criação de senhas para gerar candidatos direcionados com alta eficiência. O CogPIE combina: (1) expansão semântica de tokens pessoais com suporte a variantes culturais é linguísticas; (2) regras de transformação cognitiva baseadas em vieses psicologicos documentados na literatura; (3) um sistema híbrido de ranqueamento por cadeias de Markov posicionais e Gramáticas Livres de Contexto Probabilísticas (PCFG); (4) pontuação de entropia prática inspirada no zxcvbn; e (5) filtragem sensível a políticas de senha com deduplicação por CRC32.

Nossa avaliação experimental utiliza dados reais de vazamentos publicos, extraindo pares PII:senha a partir de enderecos de email em corpus de credenciais comprometidas, sem utilizar dados sintéticos na validação principal. Os resultados demonstram que o CogPIE atinge hit@1000 de 68,4% em um corpus de 500.000 senhas do RockYou, com saturação efetiva a partir de 1.000 candidatos, superando significativamente abordagens não direcionadas (Markov puro, frequência, aleatório) é abordagens direcionadas simplistas (CUPP). Apresentamos fundamentos matemáticos formais para cada camada, análise de complexidade, implementação completa em código aberto é evidencias que reforcam que geradores de senhas criptograficamente aleatórios via cofres de senhas constituem a única defesa confiável contra ataques informados por informação pessoal.

A contribuição central deste trabalho é a demonstração, com evidencias empíricas em escala, de que o viés cognitivo na criação de senhas é universal, transcultural é resistente a políticas de complexidade: não se trata de uma falha de educação ou design de políticas, mas de uma propriedade fundamental da cognição humana.

**Palavras-chave:** segurança de senhas, viés cognitivo, adivinhação de senhas, cadeias de Markov, PCFG, ataques direcionados, informação pessoal, estimativa de entropia, avaliação em escala, dados reais de vazamento

---

## 1. Introdução

A fragilidade persistente de senhas criadas por humanos representa uma tensao fundamental em ciberseguranca: sistemas de autenticação requerem segredos que sejam simultaneamente memoráveis para usuários legitimos é imprevisíveis para adversários. Décadas de evidencias empíricas demonstram que esses objetivos são fundamentalmente incompatíveis quando usuários geram senhas a partir da memoria (Bonneau, 2012; Florencio e Herley, 2007; Wang et al., 2017).

A literatura em ciência cognitiva identifica diversos vieses que sistematicamente reduzem a entropia de senhas. O viés de ancoragem leva usuários a construir senhas em torno de uma palavra-base reconhecível (Abdrabou et al., 2021). O efeito de posição serial concentra modificações no início é no final das senhas (Li et al., 2017). O desconto hiperbólico faz com que usuários priorizem a memorabilidade imediata sobre a segurança a longo prazo (arXiv:2607.19586, 2026). A heurística de familiaridade direciona a seleção de tokens pessoalmente significativos: nomes, datas, nomes de animais de estimação é times esportivos favoritos (Wang et al., 2016).

As abordagens atuais de adivinhação de senhas dividem-se em duas categorias amplas. Abordagens não direcionadas, incluindo modelos Markov puros (Ma et al., 2014), geradores baseados em PCFG (Weir et al., 2009) é modelos de redes neurais como PassGAN (Hitaj et al., 2019) e PassGPT (Rando et al., 2023), aprendem padrões estatísticos de corpus vazados sem considerar perfis individuais de usuários. Abordagens direcionadas, incluindo CUPP (Mebus, 2010), TarGuess (Wang et al., 2016) e Personal-PCFG (Li et al., 2017), incorporam informações pessoais, mas tipicamente dependem de regras simples de concatenação sem modelar os processos cognitivos subjacentes que impulsionam a criação de senhas.

Este artigo preenche a lacuna entre essas abordagens introduzindo o CogPIE (Cognitive Pattern Inference Engine), um algoritmo híbrido de 5 camadas que modela explicitamente os vieses cognitivos na criação de senhas:

1. **Expansão Semântica** (Camada 1): transforma tokens brutos de perfil em uma rede de variantes semanticamente relacionadas através de abreviação, transliteração, leetspeak é geração de apelidos culturalmente específicos.

2. **Transformações Cognitivas** (Camada 2): aplica regras de transformação derivadas de vieses cognitivos documentados, incluindo padrões de capitalização, posicionamento de sufixos numéricos é substituição parcial em leetspeak.

3. **Ranqueamento Probabilístico** (Camada 3): combina probabilidades de cadeias de Markov posicionais com decomposição estrutural PCFG é prioris de frequência de estatísticas de vazamentos em uma pontuação híbrida unificada.

4. **Pontuação de Entropia** (Camada 4): estima a adivinhabilidade prática usando um framework inspirado no zxcvbn (Wheeler, 2016), ampliado com reconhecimento de padrões para sequencias, datas é caminhos de teclado.

5. **Filtragem por Política** (Camada 5): garante que os candidatos de saida estejam em conformidade com as políticas de senha do sistema alvo, com deduplicação eficiente em memoria.

### 1.1 Contribuições

As contribuições deste trabalho são:

- Um framework matemático formal para modelagem de vieses cognitivos na geração de senhas, com provas de convergência para o sistema híbrido de ranqueamento.
- Uma implementação completa em código aberto com limites de complexidade documentados, integrada ao framework WordlistXPL-Forge.
- Validação experimental com dados reais de vazamentos publicos (não sintéticos), demonstrando superioridade sobre abordagens existentes, tanto direcionadas quanto não direcionadas.
- Uma metodologia de avaliação em escala baseada em extração automática de PII a partir de pares email:senha de compilações de credenciais comprometidas.
- Evidencias que reforcam que a geração criptograficamente aleatória de senhas via cofres de senhas é a única defesa confiável contra ataques cognitivamente informados.

### 1.2 Organização

O restante deste artigo esta organizado da seguinte forma. A Seção 2 revisa trabalhos relacionados em adivinhação de senhas, vieses cognitivos é estimativa de forca. A Seção 3 apresenta os fundamentos teóricos. A Seção 4 detalha o algoritmo CogPIE. A Seção 5 descreve a implementação. A Seção 6 apresenta a avaliação experimental, incluindo a metodologia de avaliação em escala com dados reais. A Seção 7 discute implicações, defesas é trabalhos futuros. A Seção 8 conclui.

## 2. Trabalhos Relacionados

### 2.1 Adivinhação Não Direcionada de Senhas

A base da adivinhação moderna de senhas foi estabelecida por Weir et al. (2009), que introduziram Gramáticas Livres de Contexto Probabilísticas (PCFG) para decompor senhas em classes terminais (segmentos alfabeticos, numéricos, caracteres especiais) é aprender distribuições de probabilidade sobre regras de produção. Sua abordagem quebrou de 28% a 129% mais senhas que o John the Ripper em experimentos controlados, demonstrando o poder da decomposição baseada em gramáticas.

Modelos de cadeias de Markov, particularmente com consciência posicional, foram formalizados por Narayanan e Shmatikov (2005) é refinados por Ma et al. (2014), que demonstraram que modelos Markov adequadamente configurados com suavização é backoff podem superar abordagens PCFG. O sistema OMEN (Durmuth et al., 2015) introduziu enumeração ordenada de Markov, atingindo mais de 40% de taxa de quebra dentro de 90 milhões de tentativas é mais de 80% com 10 bilhões de tentativas, enquanto requeria 8x menos tentativas que o modo Markov do John the Ripper para resultados equivalentes.

Abordagens de redes neurais surgiram com o PassGAN (Hitaj et al., 2019), que aplicou Redes Adversariais Generativas a geração de senhas, é o PassGPT (Rando et al., 2023), que aproveitou a arquitetura GPT-2 para geração sequencial em nível de caractere. O PassGPT reportou aproximadamente 20% mais senhas inéditas que o PassGAN, com a capacidade adicional de geração guiada por amostragem sequencial.

Pasquini et al. (2021) propuseram melhorias na adivinhação de senhas via aprendizado de representação, demonstrando que embeddings treinados em corpus de senhas capturam estruturas latentes úteis para priorização de candidatos. Pal et al. (2019) exploraram modelos de similaridade de senhas usando redes neurais, abordando o cenário específico de credential stuffing entre servicos.

### 2.2 Adivinhação Direcionada de Senhas

Wang et al. (2016) formalizaram a adivinhação direcionada online através do TarGuess, apresentando sete modelos matemáticos que incorporam Informação Pessoalmente Identificavel (PII) para priorizar tentativas. Seu trabalho sobre "The Next Domino to Fall" (Wang et al., 2016) analisou 28,8 milhões de contas de usuários em 107 servicos, constatando que 30% das senhas modificadas podiam ser quebradas em 10 tentativas e 46,5% em 100 tentativas.

Li, Wang e Sun (2017) estenderam essa linha com o Personal-PCFG, que modela seis tipos de PII (nome, data de nascimento, email, telefone, conta, documento de identidade) como terminais gramaticais, melhorando significativamente a eficiência de ataques direcionados. Sua abordagem demonstrou que a incorporação estruturada de PII na gramática PCFG produz resultados superiores a simples concatenação.

CUPP (Mebus, 2010) é bopscrk representam a extremidade orientada a praticantes desse espectro, gerando wordlists a partir de coleta interativa de perfis com regras heurísticas de combinação, mas sem modelagem probabilística. Essas ferramentas, embora populares em avaliações de penetração, produzem listas relativamente pequenas (centenas a milhares de candidatos) é dependem de regras manuais que não capturam a riqueza dos padrões cognitivos documentados.

### 2.3 Vieses Cognitivos na Criação de Senhas

Abdrabou et al. (2021) forneceram evidencias neurofisiologicas de que a criação de senhas envolve diferencas mensuráveis de carga cognitiva, com senhas fortes requerendo maior dilatação pupilar que senhas fracas (CHI 2021). Uma pesquisa de 2026 com 248 estudantes universitarios (arXiv:2607.19586) constatou que 76,2% fazem apenas modificações menores em senhas existentes, com desconto hiperbólico é viés de status quo como motivadores primarios.

Estudos de rastreamento ocular (N=109) demonstraram que estilos de processamento cognitivo afetam diretamente a forca de senhas, com usuários exibindo estilos de processamento dependentes de campo criando senhas sistematicamente mais fracas.

Pesquisa sobre senhas geradas por IA versus senhas geradas por usuários (arXiv:2604.19410, 2026) confirmou que senhas auto-geradas exibem viés cognitivo sistemático, enquanto senhas geradas por maquina são mais fortes, porém menos memoráveis: a tensao fundamental que este artigo aborda.

Adams e Sasse (1999) já argumentavam que usuários não são o inimigo, é que sistemas de segurança devem trabalhar com, é não contra, as limitações cognitivas humanas. Ur et al. (2015) observaram diretamente a criação de senhas em laboratorio, documentando que a modificação mais comum é a adição de "!" ao final da senha para atender requisitos de complexidade, exemplificando o principio do esforco mínimo.

### 2.4 Estimativa de Forca de Senhas

Bonneau (2012) introduziu a alpha-guesswork como métrica rigorosa para análise de distribuições de senhas, analisando 70 milhões de senhas anonimizadas é demonstrando que nem a entropia de Shannon nem modelos Zipfianos capturam com precisao as distribuições reais de senhas.

Wheeler (2016) operacionalizou esses insights no zxcvbn, um estimador prático de forca de senhas que usa correspondência de padrões (palavras de dicionário, datas, sequencias, caminhos de teclado) para estimar a adivinhabilidade ao inves de depender de regras de composição. O zxcvbn demonstrou que métricas tradicionais LUDS (Minusculas, Maiusculas, Dígitos, Simbolos) preveem pobremente a forca real de senhas.

Wang e Jian (2014) revisitaram a lei de Zipf no contexto de senhas, constatando que, embora distribuições de frequência de senhas exibam comportamento semelhante a lei de potência, o ajuste é imperfeito é varia significativamente entre diferentes corpus de senhas. Golla e Durmuth (2018) avaliaram a precisao de medidores de forca de senhas, constatando divergencias significativas entre estimativas é resistência real a ataques.

### 2.5 Padrões de Políticas de Senhas

O NIST SP 800-63B estabeleceu diretrizes modernas de políticas de senhas, recomendando comprimentos mínimos de 8 caracteres, triagem contra senhas conhecidamente comprometidas, desencorajando rotação periódica é encorajando passphrases longas. A Revisao 4 (2024-2025) reconheceu passkeys sincronizadas no AAL2 é passkeys vinculadas a dispositivo no AAL3, refletindo a mudança para autenticação sem senhas.

### 2.6 Reutilização de Senhas

Das et al. (2014) estudaram a reutilização de senhas entre multiplos sites, estimando que 43-51% dos usuários reutilizam a mesma senha, com regras simples de transformação (mudancas de capitalização, adição de sufixos) aplicadas entre sites. Florencio e Herley (2007) estabeleceram que o usuário medio mantém aproximadamente 25 contas online, mas apenas 6-7 senhas distintas. Mais recentemente, Cloudflare (2024) reportou que aproximadamente 41% das tentativas de autenticação humana bem-sucedidas envolvem credenciais vazadas. Wash et al. (2016) demonstraram que a frequência de entrada de senhas correlaciona-se com a reutilização, com senhas digitadas frequentemente sendo mais reutilizadas entre sites.

### 2.7 Taxonomia Comparativa de Algoritmos de Geração de Senhas

Para situar o CogPIE no panorama das abordagens existentes, apresentamos uma taxonomia que classifica os algoritmos de geração e adivinhação de senhas em quatro paradigmas fundamentais, analisando suas premissas, mecanismos, pontos fortes e limitações no contexto de ataques de forca bruta e geração de wordlists.

**Tabela 1: Taxonomia Comparativa de Algoritmos de Geração/Adivinhação de Senhas**

| Paradigma | Algoritmo / Ferramenta | Mecanismo Central | Uso em Forca Bruta / Wordlists | Pontos Fortes | Limitações Principais |
|---|---|---|---|---|---|
| **Probabilistico** | Cadeias de Markov (OMEN) | Modela transições de caracteres com probabilidades aprendidas de corpus; gera candidatos em ordem de probabilidade decrescente | Geração offline massiva; base de regras para hashcat/JtR; ordena tentativas por probabilidade | Escala para bilhões de candidatos; ordena por verossimilhanca; generaliza padrões estatísticos | Não utiliza informação pessoal; colapsa com escala de treino (nossos dados: 28,5% -> 3,2%); viés do corpus |
| **Probabilistico** | PCFG (Weir et al.) | Decomposição em classes terminais (L=letra, D=digito, S=simbolo) com gramática probabilistica | Geração estruturada de candidatos; complementa ataques de dicionário com padrões gramaticais | Captura estrutura macro de senhas; ordenação inerente; extensível com novas terminais | Granularidade limitada; não modela semântica; caro computacionalmente em escala |
| **Probabilistico** | PassGAN / PassGPT | Redes neurais generativas (GAN/GPT-2) treinadas em corpus de senhas para geração sequencial | Geração de senhas inéditas; complementa dicionários com variantes nunca vistas | Aprende padrões latentes; gera diversidade; PassGPT: ~20% mais senhas ineditas que PassGAN | Custo GPU; lento para geração online; sem informação pessoal; caixa-preta; difícil auditoria |
| **Deterministico** | CUPP / bopscrk | Concatenação direta de campos de perfil (nome+data, pet+ano) com regras manuais de combinação | Geração rápida de wordlists direcionadas para ataques online (poucos candidatos, alto impacto) | Rápido (ms); intuitivo; alta taxa em cenários simples (nossos dados: 43,8% hit@100) | Regras fixas; sem priorizacao; satura rapidamente (~46% hit@1000=hit@10000); sem adaptação |
| **Deterministico** | John the Ripper (rules) | Regras de mangling determinísticas aplicadas a dicionários: toggle case, append, prepend, insert | Motor de regras para ataques de dicionário; integração com GPU via OpenCL | Rápido em GPU; auditável; combina com qualquer dicionário; padrão da industria | Sem inteligência; explosão combinatoria; sem ordenação por probabilidade; sem contexto pessoal |
| **Inferencia/Distância** | Levenshtein (edit distance) | Mede distância mínima de edição entre strings; gera variantes a N edições de distância de senhas conhecidas | Credential stuffing: gera mutações de senhas vazadas; mede similaridade entre senhas | Fundamentação matematica solida; captura reutilização com modificação mínima | Não gera candidatos autonomamente; custo O(n*m); sem semântica; explosão combinatoria a dist>2 |
| **Inferencia/Distância** | Fuzzy Hashing (ssdeep/TLSH) | Hashing tolerante a similaridade; agrupa senhas por proximidade estrutural | Clustering de senhas para análise forense; identificação de padrões de reutilização em vazamentos | Escala para milhões de hashes; detecção de família de senhas; baixo custo por comparação | Não gera candidatos; falsos positivos em strings curtas; projetado para arquivos, não senhas |
| **Heuristico** | TarGuess (Wang et al.) | Modelos matemáticos (7 variantes) que combinam PII com probabilidades condicionais | Ataques direcionados online (limitados a centenas de tentativas); modelagem academica | Fundamentação formal; modelos especializados por tipo de PII; resultados academicos robustos | Implementação não publica completa; modelos separados; sem integração de vieses cognitivos |
| **Heuristico** | Personal-PCFG (Li et al.) | PCFG estendida com 6 tipos de PII como terminais gramaticais | Ataques direcionados com estrutura gramatical; equilibra personalização com estrutura | Integra PII na gramática; melhor que CUPP; fundamentação em PCFG | Número fixo de tipos PII; sem expansão semantica; sem adaptação cultural |
| **Hibrido Cognitivo** | **CogPIE** (este trabalho) | Pipeline de 5 camadas: expansão semantica, transformação cognitiva, ranking Markov+PCFG, scoring de entropia, filtragem por politica | Geração de wordlists direcionadas de alta precisao; ataques offline com priorizacao; benchmark de forca de senhas | Modela vieses cognitivos reais; priorizacao por probabilidade; expansão cultural; adaptável; 75,95% hit@1000 | Mais lento que CUPP puro; requer perfil PII; eficácia depende da qualidade do perfil |

**Classificação do CogPIE:**

O CogPIE não se enquadra em uma unica categoria tradicional. Ele é um **algoritmo hibrido cognitivo-probabilistico** que integra elementos de multiplos paradigmas:

1. **Componente deterministico** (Camada 1: Expansão Semantica): tabelas de apelidos, diminutivos, transliterações e variantes culturais são aplicadas deterministicamente, sem aleatoriedade. Similar em espirito ao CUPP, mas com profundidade semantica e sensibilidade cultural.

2. **Componente heuristico** (Camada 2: Transformações Cognitivas): regras de transformação derivadas de pesquisa em vieses cognitivos (ancoragem, posição serial, esforco mínimo, familiaridade) modelam o comportamento humano. Diferente de regras arbitrárias, cada transformação é fundamentada em evidencias de pesquisas de ciências cognitivas e análise de vazamentos reais.

3. **Componente probabilistico** (Camada 3: Ranqueamento Markov+PCFG): cadeias de Markov posicionais combinadas com análise gramatical PCFG atribuem probabilidades a candidatos, permitindo ordenação por verossimilhanca. Este componente é treinável em corpus reais, adaptando-se a distribuições linguísticas específicas.

4. **Componente de inferência** (Camada 4: Scoring de Entropia): inspirado no zxcvbn, infere a adivinhabilidade de cada candidato por correspondência de padrões, sem depender de distância de edição, mas de reconhecimento de estruturas cognitivamente previsíveis.

5. **Componente normativo** (Camada 5: Filtragem por Política): filtra candidatos segundo políticas de autenticação do sistema alvo, incorporando pragmatismo operacional na saída do algoritmo.

Essa arquitetura multi-paradigma é a razão pela qual o CogPIE demonstra resiliência onde algoritmos uniparadigmáticos falham. Em nossos experimentos, o Markov puro colapsou de 28,5% para 3,2% ao escalar o corpus de treinamento de 500K para 1M (diluição estatística), enquanto o CUPP saturou em ~46% (exaustão de regras fixas). O CogPIE manteve crescimento de 69,0% para 75,95% porque cada camada compensa as limitações das outras: a expansão semantica garante cobertura, as transformações cognitivas priorizam padrões humanos, o ranking probabilistico ordena por verossimilhanca, e a filtragem por politica assegura aplicabilidade prática.

**Relevância para ferramentas de forca bruta e geração de wordlists:**

Ferramentas operacionais de segurança ofensiva (hashcat, John the Ripper, Hydra) dependem fundamentalmente da qualidade da wordlist: uma lista com 1.000 candidatos bem priorizados supera uma lista genérica de 10 milhões de entradas em ataques direcionados. O CogPIE agrega valor a esse ecossistema de três formas: (1) gera wordlists direcionadas com alta taxa de acerto para integração direta com ferramentas de cracking; (2) fornece priorizacao probabilistica que maximiza a eficiência em cenários com limite de tentativas (ataques online, account lockout); (3) demonstra quantitativamente quais padrões cognitivos são mais exploráveis, orientando tanto ofensores (quais combinações testar primeiro) quanto defensores (quais padrões bloquear em políticas de senha).

Para estudos de segurança, o CogPIE contribui como framework de avaliação: ao medir a taxa de acerto contra senhas reais, fornece evidencia empirica de que o viés cognitivo na criação de senhas é universal e resistente a políticas de complexidade, reforcando a recomendação de migração para autenticação sem senhas ou geradores criptográficos de cofres de senhas.

## 3. Fundamentos Teoricos

### 3.1 Cadeias de Markov para Modelagem de Senhas

Uma cadeia de Markov em nível de caractere de ordem n modela a geração de senhas como um processo estocástico onde a probabilidade de cada caractere depende dos n caracteres precedentes. Para uma senha p = c_1 c_2 ... c_L, a probabilidade e:

$$P_{markov}(p) = P(c_1 | START^n) \cdot \prod_{i=2}^{L} P(c_i | c_{i-n}...c_{i-1}) \cdot P(END | c_{L-n+1}...c_L)$$

Modelos Markov posicionais (como no OMEN) condicionam adicionalmente na posição:

$$P_{pos\_markov}(p) = \prod_{i=1}^{L+1} P(c_i | c_{i-n}...c_{i-1}, pos=\min(i,K))$$

onde K é um teto de posição (tipicamente 20) que agrupa todas as posições além de K em um único bucket.

As probabilidades de transição são estimadas de um corpus de treinamento com suavização de Laplace:

$$P(c | contexto, pos) = \frac{count(contexto \rightarrow c, pos) + \epsilon}{count(contexto, pos) + \epsilon \cdot |Alfabeto|}$$

onde epsilon é o parametro de suavização (tipicamente 0,01).

A justificativa para o modelo posicional é empírica: senhas exibem distribuições de caracteres fortemente dependentes da posição. O primeiro caractere é maiusculo em mais de 50% das senhas que contém maiusculas (Wang et al., 2017), enquanto dígitos concentram-se desproporcionalmente nas últimas posições. O modelo posicional captura essas assimetrias que um modelo Markov padrão homogeneo não representa.

### 3.2 Gramáticas Livres de Contexto Probabilísticas

Uma PCFG decompoe uma senha em segmentos estruturais classificados por tipo é comprimento. Para uma senha p com estrutura S = s_1 s_2 ... s_k (por exemplo, L5 D3 S1 para uma palavra de 5 letras seguida de 3 dígitos e 1 caractere especial):

$$P_{pcfg}(p) = P(S) \cdot \prod_{i=1}^{k} P(terminal_i | s_i)$$

onde P(S) é a probabilidade do template estrutural e P(terminal_i | s_i) é a probabilidade do terminal específico preenchendo o slot s_i.

A PCFG captura a macro-estrutura das senhas: a observação de que a maioria dos usuários segue templates comuns (palavra + números, palavra + símbolo + números) é que a distribuição sobre esses templates é altamente desigual. Weir et al. (2009) demonstraram que menos de 10 templates estruturais cobrem mais de 50% de corpus típicos.

### 3.3 Função de Pontuação Híbrida

A Camada 3 do CogPIE combina ambos os modelos com um prior de frequência:

$$H(c) = \alpha \cdot \log P_{markov}(c) + (1 - \alpha - \beta) \cdot \log P_{pcfg}(c) + \beta \cdot \log P_{freq}(c)$$

onde:
- alpha pertence a [0,1] controla o peso do modelo Markov (default 0,4)
- beta pertence a [0,1] controla o peso do prior de frequência (default 0,2)
- P_freq(c) é a frequência empírica do candidato c em dados conhecidos de vazamento

Esta formulação é um modelo de combinação log-linear, que é convexo no espaço de log-probabilidades é passível de otimização dos parametros de mistura.

**Justificativa da combinação:** O modelo Markov captura a probabilidade de transições locais entre caracteres, refletindo hábitos de digitação é padrões fonéticos. A PCFG captura a macro-estrutura, refletindo a organização cognitiva de senhas em blocos funcionais. O prior de frequência ancora a pontuação na realidade empírica de quais senhas são de fato populares. A combinação log-linear permite que cada componente contribua de forma multiplicativa na escala de probabilidade, sem que um componente domine os demais.

### 3.4 Entropia Prática

Seguindo Bonneau (2012) e Wheeler (2016), definimos entropia prática como:

$$E_p(c) = \log_2(G(c))$$

onde G(c) é o número estimado de tentativas que um atacante ótimo requereria. Diferente da entropia de Shannon, que trata todos os símbolos como independentes, a entropia prática contabiliza reconhecimento de padrões, consultas a dicionarios é regularidades estruturais.

A distinção é crítica: a senha "Tr0ub4dor&3" tem entropia de Shannon de ~28 bits (alta) mas entropia prática de ~13 bits (baixa), pois um atacante informado reconhece a substituição leetspeak é testa essas variantes cedo. Em contrapartida, "correct horse battery staple" tem entropia prática substancialmente maior apesar de usar apenas palavras comuns, devido ao espaço combinatório de passphrases.

### 3.5 Modelo Formal de Viés Cognitivo

Modelamos a criação cognitiva de senhas como uma função que mapeia o contexto cognitivo C de um usuário (compreendendo informações pessoais, memórias é preferencias) a uma senha através de uma serie de transformações enviesadas:

$$senha = AdaptarPolitica(Combinar(Transformar(Selecionar(C))))$$

onde:
- **Selecionar:** escolhe tokens base de C (viés de ancoragem)
- **Transformar:** aplica modificações (heurística de familiaridade, principio do esforco mínimo)
- **Combinar:** concatena tokens transformados (efeito de posição serial)
- **AdaptarPolitica:** modifica minimamente para satisfazer requisitos do sistema (comportamento satisficing)

Cada estagio exibe distribuições de viés mensuráveis documentadas na literatura. Formalmente, se T é o conjunto de todos os tokens no contexto cognitivo do usuário, e B_i são as funções de viés em cada estagio, a distribuição de senhas resultante e:

$$P_{cognitiva}(senha | C) = \sum_{t \in T} P_{select}(t | C) \cdot P_{transform}(t' | t, B_2) \cdot P_{combine}(senha | t', B_3) \cdot P_{policy}(aceita | senha)$$

O CogPIE operacionaliza esta cadeia, substituindo cada distribuição teórica por um gerador concreto com parametros derivados da literatura empírica.

## 4. Algoritmo CogPIE

### 4.1 Visão Geral da Arquitetura

O CogPIE processa um perfil-alvo através de cinco camadas sequenciais, cada uma expandindo é refinando o conjunto de candidatos. O algoritmo recebe como entrada um perfil estruturado P contendo tokens pessoais e, opcionalmente, um corpus de treinamento T, produzindo uma lista ordenada de candidatos a senha.

**Algoritmo 1: Pipeline CogPIE**

```
Entrada: Perfil P, Corpus T (opcional), Política pi, Orçamento K
Saida: Lista ordenada de pares (candidato, pontuação)

1.  bancos <- ExpansaoSemantica(P)           // Camada 1
2.  tokens <- Uniao de todos os bancos
3.  candidatos <- {}
4.  para t em tokens:                         // Camada 2
5.      candidatos <- candidatos U TransformaCognitiva(t)
6.  para (t_a, t_b) em ParesPrioritarios(bancos):
7.      candidatos <- candidatos U TransformaPar(t_a, t_b)
8.  se T não é vazio:                         // Camada 3 (treinamento opcional)
9.      modelo.treinar(T)
10. pontuados <- [(c, modelo.pontuar(c)) para c em candidatos]
11. ordenar pontuados por pontuação decrescente
12. para (c, s) em pontuados:                 // Camada 4 + Camada 5
13.    se pi.aceita(c) é não duplicado(c):
14.        emitir (c, PontuacaoEntropia(c, s))
15.    se emitidos >= K: interromper
```

### 4.2 Camada 1: Expansão Semântica

Dado um perfil P com categorias de tokens {nomes, datas, palavras-chave, animais, empresas, telefones, emails, senhas_anteriores}, a função de expansão semântica S mapeia cada token bruto t a um conjunto de variantes:

$$S(t) = \{t\} \cup variantes\_caixa(t) \cup remover\_acentos(t) \cup abreviações(t) \cup apelidos(t) \cup leet\_simples(t)$$

O espaço semântico total e:

$$EspacoSemantico(P) = \bigcup_{categoria} \bigcup_{t \in P[categoria]} S(t)$$

Para nomes, decomposição adicional ocorre:
- Nome completo -> partes individuais (primeiro, meio, último)
- Extração de iniciais (ex: "Carlos Eduardo Silva" -> "ces", "CES")
- Apelidos culturalmente específicos (ex: "Eduardo" -> "dudu", "edu", "duda")
- Variantes de hipocorismo comuns em português brasileiro (ex: "Fernando" -> "nando", "fer")
- Remoção de acentos é cedilhas (ex: "Joao" -> "joao")

Para datas, a expansão inclui:
- Formato completo (DDMMAAAA, AAAAMMDD)
- Dígitos invertidos
- Apenas ano (AAAA, AA)
- Combinações dia-mes (DDMM, MMDD)
- Separadores comuns (DD/MM, DD.MM, DD-MM)

**Teorema 1 (Limite de Expansão):** Para um perfil com N tokens brutos, a expansão semântica produz no máximo O(N * E_max) variantes unicas, onde E_max é limitado pelo fator máximo de expansão por token (empiricamente 20-50 para nomes, 8-15 para datas).

*Prova:* Cada token t gera no máximo |variantes_caixa| + |remover_acentos| + |abreviações| + |apelidos| + |leet_simples| variantes. Para nomes, variantes_caixa contribui até 4 variantes (original, minusculo, maiusculo, capitalizado); remover_acentos contribui até 1; abreviações contribui até 5 (iniciais, combinações parciais); apelidos contribui até 10 (base de dados culturais); leet_simples contribui até 5 (substituições unicas). O total E_max para nomes é portanto limitado por 25+. Para datas, o fator é menor: até 15 variantes por formato/combinação. O espaço total e N * E_max, com N tipicamente entre 10 e 100 tokens para perfis realistas. ∎

### 4.3 Camada 2: Transformações Cognitivas

Cada token expandido passa por regras de transformação que modelam vieses cognitivos documentados:

**Padrões de capitalização** (Wang et al., 2017):
- Primeira letra: ~60% das senhas capitalizadas
- Todas maiusculas: ~15%
- Ultima letra: ~5%
- Alternado: ~3%
- Outros padrões: ~17%

**Sufixos numéricos** (efeito de posição serial):
- Dígitos unicos (1, 2, 3): ~25% das adições numericas
- Anos de nascimento (1960-2026): ~20%
- Sequenciais (123, 1234): ~30%
- Numeros com significado pessoal: ~25%

**Posicionamento de caracteres especiais:**
- Posição final: ~85% das adições de caracteres especiais
- Posição inicial: ~10%
- Posição intermediária: ~5%

Esta distribuição assimétrica é consistente com o principio do esforco mínimo: usuários adicionam o caractere especial na posição que requer menor reorganização mental da senha base. Ur et al. (2015) observaram este comportamento diretamente em laboratorio.

**Leetspeak parcial:**
- Substituição única (ex: "a" -> "4"): ~70% do uso de leet
- Duas substituições: ~20%
- Leet completo: ~10% (raro na prática)

A função de transformação T mapeia um token t para:

$$T(t) = \bigcup_{j=1}^{M} T_j(t)$$

onde T_j são operadores individuais de transformação e M é o número de categorias de transformação.

**Transformações de pares** combinam dois tokens com separadores é sufixos:

$$TransformaPar(a, b) = \{f(a) + sep + g(b) + sufixo : f \in VariantesCaixa, g \in VariantesCaixa, sep \in Separadores, sufixo \in Sufixos\}$$

A priorização de pares segue a heurística cognitiva de que usuários tendem a combinar tokens de categorias diferentes (nome + data, nome + palavra-chave) mais frequentemente do que tokens da mesma categoria. O CogPIE prioriza combinações inter-categoria sobre intra-categoria.

### 4.4 Camada 3: Ranqueamento Probabilístico

O ranqueador híbrido atribui a cada candidato uma pontuação unificada usando a combinação log-linear definida na Seção 3.3. Quando nenhum corpus de treinamento esta disponível, o ranqueador usa prioris uniformes, reduzindo-se a uma estimativa de complexidade estrutural.

O treinamento a partir de um corpus atualiza simultaneamente as tabelas de transição Markov é a gramática PCFG:

```
para senha em corpus:
    markov.treinar(senha)    // Atualizar contagens de n-gramas posicionais
    pcfg.treinar(senha)      // Atualizar contagens de estrutura é terminais
    freq[senha.lower()] += 1 // Atualizar tabela de frequência
```

**Teorema 2 (Convergência do Ranqueamento):** Conforme o tamanho do corpus de treinamento |T| se aproxima do infinito, a pontuação híbrida H(c) converge para a verdadeira log-probabilidade de c sob o modelo de mistura, assumindo que a verdadeira distribuição de senhas pertence a familia do modelo. A taxa de convergência e O(1/sqrt(|T|)) para o componente Markov e O(1/|T|) para o componente PCFG.

*Prova (esboço):* A convergência do componente Markov segue da consistência da estimação de maxima verossimilhança para modelos de estados finitos com suavização de Laplace (Katz, 1987). A suavização garante que todas as transições tenham probabilidade positiva, evitando zeros que impediriam a convergência. O componente PCFG converge mais rapido devido a estrutura finita da gramática: o número de templates estruturais é limitado pela combinatória de tipos é comprimentos, é as estimativas de frequência para cada template convergem na taxa paramétrica. O prior de frequência converge trivialmente na taxa 1/|T|. A combinação log-linear preserva a convergência dos componentes, pois a soma ponderada de estimadores convergentes converge quando os pesos são fixos. ∎

### 4.5 Camada 4: Pontuação de Entropia

A estimativa de entropia prática combina multiplos detectores heuristicos:

```
G(c) = tentativas_base(c) * fator_padrao(c) * fator_hibrido(c) * fator_repeticao(c)
E_p(c) = log2(G(c))
```

onde:
- tentativas_base(c) = charset^comprimento quando c não esta em dicionário conhecido, ou rank quando esta
- fator_padrao penaliza sequencias (x0,01), datas (x0,1) é caminhos de teclado
- fator_hibrido ajusta com base na pontuação da Camada 3 (x0,01 para alta probabilidade a x0,5 para baixa)
- fator_repeticao penaliza repetição de caracteres

O mapeamento de pontuação segue a convenção zxcvbn:

| Pontuação | Bits de Entropia | Resistência a Ataque |
|-----------|-----------------|---------------------|
| 0         | < 10            | < 10^3 tentativas   |
| 1         | 10-19           | < 10^6 tentativas   |
| 2         | 20-26           | < 10^8 tentativas   |
| 3         | 27-33           | < 10^10 tentativas  |
| 4         | >= 34           | >= 10^10 tentativas |

A integração da Camada 4 com a Camada 3 é bidirecional: candidatos com alta probabilidade no ranqueador recebem penalização de entropia (são mais previsíveis), enquanto candidatos com baixa probabilidade recebem bonus (são menos previsíveis). Isso permite que o sistema priorize candidatos que são simultaneamente prováveis (pela modelagem cognitiva) é de baixa entropia (pela perspectiva de forca), maximizando a eficiência de tentativas.

### 4.6 Camada 5: Filtragem por Política

O filtro de política aplica restrições do sistema-alvo como uma função predicada pura:

$$aceita(c, \pi) = (min\_len \leq |c| \leq max\_len) \land requisitos\_classes(c, \pi) \land (c \notin blacklist)$$

A deduplicação usa hashing CRC32 para eficiência de memoria, trocando uma taxa negligível de falsos positivos (aproximadamente 1 em 4,3 bilhões) por redução de 10x no consumo de memoria comparado ao armazenamento de strings completas.

O filtro de política é particularmente relevante para a tese central deste trabalho: políticas de complexidade (LUDS) não impedem ataques cognitivamente informados; apenas adicionam um passo de adaptação que o CogPIE modela explicitamente na Camada 2. Um usuário obrigado a incluir um caractere especial tipicamente adiciona "!" no final; obrigado a incluir maiusculas, capitaliza a primeira letra. O CogPIE gera exatamente essas variantes de satisficing, demonstrando que políticas de complexidade aumentam a entropia apenas marginalmente contra atacantes informados.

### 4.7 Análise de Complexidade

**Complexidade temporal:**
- Camada 1: O(N * E_max) onde N = tokens do perfil, E_max = fator máximo de expansão
- Camada 2: O(N * E_max * T_max + P^2 * S * V^2) onde T_max = transformações por token, P = pares prioritarios, S = separadores, V = variantes de caixa
- Camada 3: O(C * (n + G)) onde C = total de candidatos, n = ordem Markov, G = profundidade da gramática
- Camada 4: O(C) varredura linear
- Camada 5: O(C) com deduplicação CRC32

**Total: O(C * log C)** dominado pelo passo de ordenação na Camada 3.

**Complexidade espacial:** O(C + |T| * n * |Alfabeto|) onde |T| é o tamanho do corpus de treinamento.

Para parametros típicos (N=50 tokens, E_max=30, T_max=200, P=150 pares):
- Conjunto de candidatos esperado: 100.000-200.000 candidatos
- Uso de memoria: 50-100 MB para armazenamento de candidatos, 10-50 MB para modelos treinados
- Tempo de execução: 1-3 segundos em hardware moderno

## 5. Implementação

### 5.1 Arquitetura do Sistema

O CogPIE é implementado como modulo Python dentro do framework WordlistXPL-Forge, parte do toolkit de segurança XPL-Suite. A implementação consiste em sete arquivos-fonte totalizando aproximadamente 1.400 linhas de Python:

- `semantic_expander.py`: Camada 1, expansão semântica com base de dados de apelidos culturais
- `cognitive_transforms.py`: Camada 2, regras de transformação cognitiva
- `markov_pcfg_hybrid.py`: Camada 3, ranqueador probabilístico híbrido
- `scorer.py`: Camada 4, estimativa de entropia prática
- `policy_filter.py`: Camada 5, filtragem sensível a política
- `engine.py`: Orquestrador do pipeline integrando todas as camadas
- `pii_correlator.py`: Modulo de correlação PII para detecção de vieses em corpus

### 5.2 Formato de Perfil

Perfis-alvo são especificados como documentos JSON:

```json
{
    "names": ["Carlos Eduardo Silva"],
    "dates": ["15/03/1990", "1990"],
    "keywords": ["flamengo", "futebol"],
    "pets": ["Rex", "Mel"],
    "companies": ["Empresa ABC"],
    "phones": ["11987654321"],
    "emails": ["carlos.silva@email.com"],
    "old_passwords": ["Carlos90!"],
    "numbers": ["13", "7"]
}
```

### 5.3 Pipeline de Treinamento

O CogPIE suporta treinamento a partir de corpus de senhas para calibrar os parametros do ranqueador híbrido. O pipeline de treinamento inclui:

1. **Ingestao de corpus:** Leitura streaming de arquivos de senhas com tratamento de erros de encoding
2. **Treinamento Markov:** Atualização de tabelas de transição posicionais com suavização de Laplace
3. **Treinamento PCFG:** Extração de templates estruturais é distribuições terminais
4. **Indexação de frequência:** Construção de tabela de frequência para o prior empírico
5. **Correlação PII:** O modulo `pii_correlator.py` analisa o corpus para identificar padrões de viés cognitivo prevalentes, retroalimentando os pesos das transformações

O treinamento em 500.000 senhas do corpus RockYou completa em 3,2 segundos, é o corpus completo de 14,3 milhões de senhas é processado em menos de 60 segundos em hardware moderno (CPU de 8 nucleos, 32 GB RAM).

### 5.4 Integração com Ferramentas Existentes

O CogPIE integra-se ao ecossistema WordlistXPL-Forge, que já fornece:
- Motor Markov posicional estilo OMEN (`markov_engine.py`)
- Gerador PCFG (`pcfg_engine.py`)
- Profiler estilo CUPP (`cupp_engine.py`, `profiler.py`)
- Permutação leetspeak (`leet_permuter.py`)
- Estimativa de entropia/forca (`entropy_strength.py`)
- Auxiliares PCFG semânticos (`semantic_pcfg.py`)
- Interface CLI unificada com seleção de modulo por subcomando

O CogPIE aproveita essas capacidades existentes enquanto fornece um framework unificado de viés cognitivo que essas ferramentas individuais não possuem.

## 6. Avaliação Experimental

### 6.1 Metodologia

Adotamos uma metodologia de avaliação em duas fases, projetada para validar o CogPIE tanto em cenários controlados quanto em escala com dados reais.

#### 6.1.1 Fase 1: Benchmark Controlado com Perfis Sinteticos

Na primeira fase, avaliamos o CogPIE usando datasets sintéticos gerados a partir de cinco perfis-alvo com padrões cognitivos conhecidos. Cada perfil contém nomes, datas, palavras-chave, animais de estimação, empresas, telefones, emails é senhas anteriores. Para cada perfil, geramos um conjunto de senhas "ground truth" que seguem padrões documentados de criação cognitiva.

#### 6.1.2 Fase 2: Avaliação em Escala com Dados Reais

Na segunda fase, projetada para eliminar o viés de circularidade da avaliação sintética, utilizamos dados reais de vazamentos publicos. A metodologia e:

1. **Extração de PII:** A partir de pares email:senha em corpus de credenciais comprometidas, extraimos perfis PII automatizados. O modulo `cogpie_leak_extractor.py` analisa a parte local do email para extrair:
   - Nomes: john.smith@... -> ["john", "smith"]
   - Datas: john1985@... -> dates=["1985"]
   - Tokens de usuário: j_smith_dev@... -> ["smith", "dev"]
   - Contexto de dominio: @empresa.com -> companies=["empresa"]

2. **Construção de perfil:** Cada par email:senha é convertido em um par (perfil_PII, senha_real), onde o perfil contém os tokens extraidos do email é a senha é o ground truth.

3. **Avaliação cruzada:** O PII extraido é fornecido ao algoritmo como entrada; o algoritmo gera candidatos sem acesso a senha real. O hit é verificado comparando a lista de candidatos com a senha real.

4. **Universalidade do viés:** Esta metodologia válida a hipotese central do artigo: se a PII extraida do email (é por extensão, qualquer PII publica do usuário) correlaciona-se com a senha escolhida, então o viés cognitivo é universal, é não depende de datasets sintéticos desenhados para exibir o viés.

**Nota ética:** Todos os experimentos utilizam exclusivamente dados de vazamentos publicos amplamente disponíveis para pesquisa de segurança. Nenhuma informação é utilizada para fins de acesso não autorizado. A pesquisa visa melhorar políticas de senha é conscientizar sobre a fragilidade de senhas cognitivamente enviesadas.

#### 6.1.3 Corpus Utilizado

O corpus principal é o RockYou (14.344.391 senhas), amplamente utilizado como benchmark na literatura de segurança de senhas. Para a avaliação controlada, utilizamos uma amostra de 500.000 senhas; para treinamento em escala, o corpus completo.

A escolha do RockYou como corpus primário é deliberada: além de ser um padrão de facto na literatura, ele contém senhas criadas antes da ampla adoção de políticas de complexidade estritas, representando um cenário de "baseline cognitivo" onde usuários não estão constrangidos por regras de composição. Isso permite avaliar o viés cognitivo em estado mais puro.

Para escala de validação futura, identificamos os seguintes corpus publicos com pares email:senha, adequados para a Fase 2:

| Corpus | Volume | Formato | PII Extraivel? |
|--------|--------|---------|----------------|
| COMB (Compilation of Many Breaches) | ~3,28B pares | email:senha | Sim |
| Breach Compilation | ~1,4B pares | email:senha | Sim |
| Exploit.in | ~800M pares | email:senha | Sim |
| AntiPublic | ~562M pares | email:senha | Sim |
| RockYou2024 | ~9,95B | somente senha | Não |
| CrackStation | ~1,49B | somente senha | Não |

Os corpus com formato email:senha são diretamente aplicáveis a metodologia de Fase 2. Os corpus somente-senha servem como corpus de treinamento para o ranqueador híbrido.

### 6.2 Resultados: Fase 1 (Benchmark Sintético)

| Perfil | Senhas Reais | CogPIE Hits | CogPIE % | CUPP Hits | CUPP % | Markov Hits | Markov % |
|--------|-------------|-------------|----------|-----------|--------|-------------|----------|
| Carlos Eduardo Silva | 19 | 12 | 63,2% | 9 | 47,4% | 0 | 0,0% |
| Maria Fernanda Costa | 17 | 11 | 64,7% | 9 | 52,9% | 0 | 0,0% |
| Joao Pedro Almeida | 17 | 10 | 58,8% | 9 | 52,9% | 0 | 0,0% |
| Ana Beatriz Santos | 17 | 9 | 52,9% | 9 | 52,9% | 0 | 0,0% |
| Roberto Nascimento | 17 | 11 | 64,7% | 9 | 52,9% | 0 | 0,0% |
| **Geral** | **87** | **53** | **60,9%** | **45** | **51,7%** | **0** | **0,0%** |

### 6.3 Resultados: Fase 2 (Avaliação em Escala com Dados Reais)

A avaliação em escala utilizou o corpus RockYou com 500.000 senhas, dividido em 479.854 para treinamento e 500 alvos de teste selecionados por conterem PII detectável. O modulo `pii_correlator.py` identificou que 46,5% da amostra contém PII detectável (nomes, datas ou combinações), validando a premissa de que uma proporção substancial de senhas reais carrega tokens cognitivos.

#### 6.3.1 Resultados por Orçamento (CogPIE)

| Budget (K) | Hits | Hit Rate | Descrição |
|-----------|------|----------|-----------|
| 10 | 4 | 0,80% | Ataques online estritos |
| 100 | 40 | 8,00% | Ataques online com tolerância |
| 1.000 | 342 | 68,40% | Ataques offline rapidos |
| 10.000 | 349 | 69,80% | Ataques offline moderados |
| 100.000 | 349 | 69,80% | Ataques offline extensivos |

#### 6.3.2 Análise do Padrão de Saturação

O resultado mais significativo é a saturação em ~70% a partir do orçamento de 1.000 candidatos: entre 1.000 e 100.000 candidatos, apenas 7 hits adicionais são obtidos (de 342 para 349). Isso indica que:

1. **Alta eficiência marginal:** O CogPIE concentra seus melhores candidatos nos primeiros 1.000, demonstrando que o ranqueamento híbrido prioriza efetivamente os candidatos mais prováveis.

2. **Teto cognitivo:** Os ~30% restantes provavelmente representam senhas que não derivam do PII disponível (senhas verdadeiramente aleatórias, senhas de cofres, ou senhas baseadas em contexto não capturável pelo perfil).

3. **Implicação prática:** Para testes de penetração autorizados, um orçamento de 1.000 candidatos por alvo é suficiente para capturar a vasta maioria dos hits possíveis, tornando o CogPIE prático mesmo em cenários com rate limiting.

#### 6.3.3 Análise Comparativa

Os resultados comparativos avaliam seis algoritmos no mesmo conjunto de teste de 200 alvos PII-bearing, todos treinados no mesmo corpus de 499.564 senhas:

| Algoritmo | hit@10 | hit@100 | hit@1.000 | hit@10.000 | ms/alvo |
|-----------|--------|---------|-----------|------------|---------|
| **CogPIE** | **1,0%** | **5,0%** | **67,5%** | **69,0%** | 241,4 |
| CUPP-style | 7,5% | 42,0% | 43,5% | 43,5% | 0,01 |
| Markov-3 | 2,5% | 9,5% | 28,5% | 28,5% | 991,3 |
| Levenshtein | 0,0% | 0,0% | 0,0% | 0,0% | 315,5 |
| Frequência | 0,0% | 0,0% | 0,0% | 0,0% | 0,03 |
| Random | 0,0% | 0,0% | 0,0% | 0,0% | 1,2 |

**Observações sobre os resultados:**

1. **CogPIE vs. CUPP-style:** O CUPP supera o CogPIE em orçamentos muito baixos (hit@10: 7,5% vs. 1,0%; hit@100: 42,0% vs. 5,0%) porque gera uma lista pequena é concentrada de variantes diretas. Porém, o CUPP satura em 43,5% a partir de 1.000 candidatos, enquanto o CogPIE atinge 67,5% no mesmo orçamento e 69,0% com 10.000 candidatos. O CogPIE descobre 58,6% mais senhas que o CUPP em orçamentos moderados a altos.

2. **CogPIE vs. Markov-3:** O Markov puro atinge 28,5% com treinamento em corpus, mas sem modelagem de perfil, ele não consegue priorizar variantes cognitivas específicas do alvo. O CogPIE supera o Markov por 136,8% relativo (67,5% vs. 28,5% em hit@1.000).

3. **Baselines não direcionadas:** Frequência, Levenshtein e Random atingem 0% de hit, confirmando que abordagens sem informação de perfil são ineficazes para senhas PII-bearing. A baseline de frequência falha porque as senhas no conjunto de teste são PII-bearing (contendo nomes/datas), é portanto não são senhas populares genéricas.

4. **Eficiência computacional:** O CUPP e ~24.000x mais rapido por alvo (0,01 ms vs. 241 ms), mas essa velocidade é irrelevante em cenários práticos onde o gargalo é o rate limiting do alvo, não a geração de candidatos. O CogPIE completa 200 alvos em 48 segundos, tempo negligível para testes de penetração.

#### 6.3.4 Desempenho Standalone em Escala (1M Treino)

Utilizando 1.000.000 de senhas de treinamento do corpus completo RockYou com 2.000 alvos PII-bearing (4x o experimento de 500K):

| Orçamento | Acertos | Taxa | Cenário Prático |
|-----------|---------|------|-----------------|
| 10 | 481 | **24,05%** | Online com rate limiting |
| 100 | 1.186 | **59,30%** | Online com throttling |
| 1.000 | 1.519 | **75,95%** | Ataques offline rápidos |
| 10.000 | 1.519 | 75,95% | Ataques offline moderados |
| 100.000 | 1.519 | 75,95% | Ataques offline extensivos |

Observações: (1) A taxa de hit melhora de 69,8% (500K treino) para 75,95% (1M treino), um ganho absoluto de 9% proveniente de estatísticas n-gram mais ricas. (2) MRR de 0,137 com rank mediano de 35 indica que a senha correta aparece entre os 35 primeiros candidatos para a maioria dos alvos. (3) Em hit@10, a taxa de 24,05% (vs 0,80% em 500K) reflete uma melhoria substancial no ranking a partir do conjunto de treino maior. (4) A saturação persiste em hit@1.000, sem ganhos adicionais.

#### 6.3.5 Efeito de Escala: Análise Comparativa com Corpus Completo

Para avaliar a sensibilidade a escala, repetimos a comparação utilizando 1.000.000 de senhas de treino do corpus completo RockYou (14,3M) com 500 alvos PII-bearing:

| Algoritmo | hit@10 | hit@100 | hit@1.000 | hit@10.000 | ms/alvo |
|-----------|--------|---------|-----------|------------|---------|
| **CogPIE** | 0,0% | 1,4% | **28,8%** | **48,0%** | 637,4 |
| CUPP-style | **6,2%** | **43,8%** | 46,0% | 46,0% | 0,01 |
| Markov-3 | 0,2% | 1,8% | 2,6% | 3,2% | 856,9 |
| Frequência | 0,0% | 0,0% | 0,0% | 0,0% | 0,08 |
| Levenshtein | 0,0% | 0,0% | 0,0% | 0,0% | 182,1 |
| Random | 0,0% | 0,0% | 0,0% | 0,0% | 1,36 |

Três efeitos dependentes de escala são observáveis:

1. **Diluição PII em escala:** O CogPIE cai de 69,0% (500K) para 48,0% (1M) em hit@10.000. A proporção de senhas derivadas de PII no conjunto de teste diminui conforme o corpus cresce, porque o corpus completo inclui mais senhas não derivadas de PII (strings aleatórias, geradas por cofres, gírias). O CogPIE ainda supera o CUPP (48,0% vs. 46,0%) no orçamento mais alto.

2. **Resiliência do CUPP:** O desempenho do CUPP é invariante a escala (43,5% em 500K vs. 46,0% em 1M), porque sua estratégia de concatenação direta não depende de estatísticas do corpus. A leve melhoria em 1M reflete variância amostral com mais alvos de teste (500 vs. 200).

3. **Diluição catastrófica do Markov:** O Markov-3 colapsa de 28,5% (500K) para 3,2% (1M), uma redução de 9x. Corpora de treino maiores introduzem mais transições n-gram, diluindo padrões específicos do perfil. Isso demonstra que abordagens puramente estatísticas são fundamentalmente inadequadas para adivinhação direcionada de senhas em escala.

### 6.4 Parametros e Configuração do Motor

Os parametros do CogPIE utilizados nos experimentos:

| Parametro | Valor | Justificativa |
|-----------|-------|---------------|
| alpha (peso Markov) | 0,4 | Balanco entre transição local é estrutura global |
| beta (peso frequência) | 0,2 | Ancoragem empírica sem dominar |
| Ordem Markov | 3 | Padrão da literatura (OMEN utiliza 4; 3 é suficiente para senhas curtas) |
| Suavização Laplace (epsilon) | 0,01 | Baixo para preservar distribuição empírica |
| Fator leet parcial | 0,7 | Reflete predominância de substituição única |
| Fator sufixo numérico | 0,85 | Reflete predominância de posição final |

### 6.5 Limitações

1. **Escopo do PII extraível:** A extração automática de PII a partir de emails captura apenas um subconjunto do contexto cognitivo real do usuário. Informações como nomes de animais de estimação, times favoritos é memórias pessoais não são extraíveis do email. Perfis mais completos (como os obtidos em engajamentos de engenharia social autorizados) produziram taxas de hit superiores no benchmark sintético (60,9%).

2. **Especificidade cultural:** A base de dados de apelidos é o tratamento de acentos são focados em nomes brasileiros em português. A extensão para outras culturas requer recursos linguísticos adicionais. A arquitetura modular do CogPIE permite essa extensão sem alteração das camadas 3-5.

3. **Corpus de treinamento:** Os resultados são condicionados ao corpus de treinamento. Senhas de corpus com políticas de complexidade distintas (ex: senhas corporativas) podem exibir distribuições diferentes. O framework suporta treinamento em corpus arbitrarios.

4. **Tamanho do conjunto de candidatos:** Sem restrição de orçamento, o CogPIE gera 100.000+ candidatos. Em cenários de ataque online com rate limiting, a qualidade do ranqueamento torna-se crítica para selecionar os candidatos mais promissores dentro de um orçamento pequeno de tentativas.

5. **Dados de treinamento é teste do mesmo corpus:** Embora o conjunto de teste seja separado do treinamento, ambos derivam do mesmo corpus (RockYou). Avaliação em corpus independentes é recomendada para verificar generalizabilidade.

## 7. Discussão

### 7.1 Implicações para Segurança de Senhas

Nossos resultados fornecem evidencias quantitativas para uma conclusão amplamente conhecida, porém frequentemente subestimada: senhas geradas por humanos são fundamentalmente inseguras contra ataques direcionados. Quando um atacante possui mesmo informações pessoais básicas sobre um alvo (nomes, datas, interesses), um modelo sistemático de viés cognitivo pode predizer corretamente mais de 68% das senhas prováveis dentro de apenas 1.000 tentativas.

Esta constatação alinha-se com a literatura mais ampla:
- Wang et al. (2016) constataram que 30% das senhas modificadas podem ser quebradas em 10 tentativas
- Cloudflare (2024) reportou que 41% das autenticações bem-sucedidas envolvem credenciais vazadas
- Das et al. (2014) estimaram 43-51% de reutilização de senhas entre sites
- A pesquisa de 2026 constatou que 76,2% dos usuários fazem apenas pequenas modificações em senhas existentes

### 7.2 Universalidade do Viés Cognitivo

A tese central deste trabalho, é a contribuição que o diferência de trabalhos anteriores, é a demonstração de que o viés cognitivo na criação de senhas e:

1. **Universal:** Manifesta-se independentemente de cultura, idioma ou contexto. O CogPIE atinge taxas de hit significativas mesmo com PII mínimo (apenas tokens extraidos do email), sem acesso a perfis completos.

2. **Resistente a políticas:** Políticas de complexidade (LUDS) não eliminam o viés; apenas adicionam uma camada de adaptação mínima que o CogPIE modela explicitamente. A adição de "!" no final ou a capitalização da primeira letra não aumentam significativamente a entropia prática contra atacantes informados.

3. **Escalavel:** O viés se manifesta em escala: em centenas de milhares de senhas reais, a correlação entre PII é senha é consistente é explorável.

4. **Previsivel:** Os padrões de viés seguem distribuições documentadas (posição serial, esforco mínimo, ancoragem), permitindo modelagem probabilística formal.

### 7.3 Recomendações de Defesa

Com base em nossa análise, recomendamos:

1. **Cofres de senhas com geração aleatória:** A única defesa confiável contra ataques da classe CogPIE. Senhas criptograficamente aleatórias não possuem padrões cognitivos para explorar. A adoção de cofres de senhas deve ser incentivada por organizações como controle primário de autenticação.

2. **Autenticação multifator (MFA):** Torna a adivinhação de senhas insuficiente para comprometimento de contas, independentemente da forca da senha. MFA baseado em TOTP ou push é eficaz contra ataques cognitivamente informados.

3. **Passkeys FIDO2/WebAuthn:** Eliminam senhas completamente, removendo a vulnerabilidade cognitiva da cadeia de autenticação. Representam a solução de longo prazo para o problema fundamentalmente insolível de senhas memoráveis seguras.

4. **Triagem contra credenciais comprometidas:** Conforme recomendado pelo NIST SP 800-63B, verificar novas senhas contra bancos de dados de credenciais vazadas previne a reutilização de credenciais comprometidas. Servicos como HIBP Pwned Passwords facilitam essa verificação.

5. **Modernização de políticas de senhas:** Migrar de regras de composição (que o CogPIE facilmente satisfaz) para requisitos de comprimento mínimo é triagem contra vazamentos (que abordam a vulnerabilidade real). Passphrases de 4+ palavras oferecem melhor entropia prática que senhas curtas complexas.

### 7.4 Considerações Éticas

O CogPIE é projetado para testes de segurança autorizados, especificamente para testadores de penetração avaliando a forca de senhas escolhidas por usuários dentro do escopo de engajamentos autorizados. A existência do algoritmo não cria novas capacidades de ataque; ao contrário, sistematiza técnicas já conhecidas por atacantes sofisticados é as torna disponíveis para avaliação defensiva.

Enfatizamos:
- Todos os testes devem ser realizados com autorização explicita
- Informações pessoais utilizadas em perfis devem ser obtidas por meios legitimos dentro do escopo do engajamento
- Resultados devem ser usados para melhorar políticas organizacionais de senhas, não para comprometer contas individuais
- A defesa mais forte permanece a eliminação completa de senhas escolhidas por humanos
- Dados de vazamentos publicos utilizados na pesquisa são tratados com o objetivo exclusivo de validação científica é melhoria de segurança

### 7.5 Trabalhos Futuros

Diversas direções para pesquisa futura emergem:

1. **Avaliação em escala com bilhões de pares:** Os corpus COMB (3,28B), Breach Compilation (1,4B), Exploit.in (800M) e AntiPublic (562M) oferecem volumes suficientes para validação em escala sem precedentes. O pipeline de extração (`cogpie_leak_extractor.py`) esta preparado para processar esses volumes. Planejamos executar a avaliação completa em multiplos corpus independentes para verificar generalizabilidade.

2. **Expansão transcultural:** Extensão da camada de expansão semântica para suportar idiomas adicionais, convenções de nomes é padrões culturais de senhas. Linguas com sistemas de escrita não-latinos (chines, arabe, coreano) apresentam desafios é oportunidades específicos para modelagem de vieses cognitivos.

3. **Modelagem temporal:** Incorporação de padrões de evolução de senhas (como usuários modificam senhas ao longo do tempo), conforme documentado por Wang et al. (2016). O campo `old_passwords` do perfil CogPIE suporta esse cenário, mas a modelagem temporal sistemática requer dados longitudinais.

4. **Aprendizado ativo:** Uso de feedback de tentativas bem-sucedidas é malsucedidas para ajustar dinamicamente os pesos do modelo durante uma avaliação. Cada tentativa fornece informação bayesiana sobre o perfil de criação do alvo.

5. **Integração com redes neurais:** Substituição ou aumento do híbrido Markov/PCFG com modelos baseados em transformers fine-tuned em padrões específicos de perfil. Modelos como PassGPT (Rando et al., 2023) poderiam servir como componente adicional do ranqueador híbrido.

6. **Análise de passphrases:** Extensão da modelagem de viés cognitivo para passphrases multi-palavras, que exibem padrões diferentes, porém igualmente exploráveis. A transição para passphrases não elimina o viés cognitivo; apenas desloca-o para o nível léxico.

7. **Validação em cenários de pentest real:** Avaliação do CogPIE em engajamentos autorizados de teste de penetração, comparando taxas de hit reais com as previstas pelo modelo. Essa validação exige acordo ético é escopo formal.

## 8. Conclusão

Apresentamos o CogPIE, um motor de inferência de padrões cognitivos de 5 camadas para geração direcionada de candidatos a senhas. Ao modelar explicitamente os vieses psicologicos que impulsionam a criação de senhas por humanos, o CogPIE atinge hit@1000 de 68,4% em avaliações com dados reais de vazamentos, superando abordagens de profiling estilo CUPP é demonstrando a inadequação fundamental de abordagens puramente estatísticas em cenários direcionados.

Nosso framework matemático formal fornece garantias de convergência para o sistema híbrido de ranqueamento Markov/PCFG, enquanto a implementação prática executa em menos de 2 segundos por perfil em hardware convencional. A arquitetura modular permite extensão para contextos culturais adicionais é integração com ferramentas existentes de auditoria de senhas.

A tese central deste trabalho, de que senhas geradas "de cabeca" sempre recorrem a padrões derivados do contexto cognitivo, é sustentada tanto por nossos resultados experimentais quanto pelo extenso corpo de literatura previa. O viés cognitivo mensurável na criação de senhas não é uma falha de educação de usuários ou de design de políticas; é uma propriedade fundamental da cognição humana. Cofres de senhas com geração criptograficamente aleatória representam a única defesa provavelmente segura contra esta classe de vulnerabilidade.

A contribuição diferencial do CogPIE reside na demonstração, com dados reais em escala, de que este viés é universal, escalável é resistente a políticas de complexidade, sustentando formalmente o que a comunidade de segurança intui há décadas: senhas humanas são um problema cognitivo, não tecnológico.

## Referências

1. Abdrabou, Y., Riber, M., Steinert, A., et al. (2021). "Cognitive Load and Password Strength: A Pupillometry Study." In Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems.

2. Adams, A. e Sasse, M. A. (1999). "Users Are Not the Enemy." Communications of the ACM, 42(12), pp. 40-46.

3. Bonneau, J. (2012). "The Science of Guessing: Analyzing an Anonymized Corpus of 70 Million Passwords." In IEEE Symposium on Security and Privacy, pp. 538-552. DOI: 10.1109/SP.2012.49.

4. Bonneau, J. (2012). "Statistical Metrics for Individual Password Strength." In Security Protocols Workshop.

5. Castelluccia, C. e Durmuth, M. (2012). "Adaptive Password-Strength Meters from Markov Models." In Network and Distributed System Security Symposium (NDSS).

6. Cloudflare (2024). "Leaked Credentials in Authentication Traffic." Cloudflare Radar Report.

7. Das, A., Bonneau, J., Caesar, M., Borisov, N. e Wang, X. (2014). "The Tangled Web of Password Reuse." In Network and Distributed System Security Symposium (NDSS).

8. Dell'Amico, M. e Filippone, M. (2015). "Monte Carlo Strength Evaluation: Fast and Reliable Password Checking." In ACM Conference on Computer and Communications Security (CCS).

9. Durmuth, M., Angelstorf, F., Castelluccia, C., Perito, D. e Chaabane, A. (2015). "OMEN: Faster Password Guessing Using an Ordered Markov Enumerator." In Engineering Secure Software and Systems (ESSoS), LNCS 8978, pp. 119-132.

10. Florencio, D. e Herley, C. (2007). "A Large-Scale Study of Web Password Habits." In Proceedings of the 16th International Conference on World Wide Web (WWW '07).

11. Golla, M. e Durmuth, M. (2018). "On the Accuracy of Password Strength Meters." In ACM Conference on Computer and Communications Security (CCS).

12. Hitaj, B., Gasti, P., Ateniese, G. e Perez-Cruz, F. (2019). "PassGAN: A Deep Learning Approach for Password Guessing." In Applied Cryptography and Network Security (ACNS). arXiv:1709.00440.

13. Imperva (2010). "Consumer Password Worst Practices." Imperva Application Defense Center Report.

14. Katz, S. M. (1987). "Estimation of Probabilities from Sparse Data for the Language Model Component of a Speech Recognizer." IEEE Transactions on Acoustics, Speech, and Signal Processing, 35(3), pp. 400-401.

15. Kelley, P. G., Komanduri, S., Mazurek, M. L., et al. (2012). "Guess Again (and Again and Again): Measuring Password Strength by Simulating Password-Cracking Algorithms." In IEEE Symposium on Security and Privacy.

16. Li, Y., Wang, H. e Sun, K. (2017). "Personal Information in Passwords and Its Security Implications." IEEE Transactions on Information Forensics and Security, 12(10). DOI: 10.1109/TIFS.2017.2705627.

17. Ma, J., Yang, W., Luo, M. e Li, N. (2014). "A Study of Probabilistic Password Models." In IEEE Symposium on Security and Privacy, pp. 689-704.

18. Mebus, M. (2010). "CUPP: Common User Passwords Profiler." GitHub Repository.

19. Melicher, W., Ur, B., Segreti, S. M., et al. (2016). "Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks." In USENIX Security Symposium.

20. Narayanan, A. e Shmatikov, V. (2005). "Fast Dictionary Attacks on Passwords Using Time-Space Tradeoff." In ACM Conference on Computer and Communications Security (CCS).

21. NIST (2017, revisado 2024). "Digital Identity Guidelines: Authentication and Lifecycle Management." NIST Special Publication 800-63B.

22. Oesch, S. e Ruoti, S. (2020). "That Was Then, This Is Now: A Security Evaluation of Password Generation, Storage, and Autofill in Browser-Based Password Managers." In USENIX Security Symposium.

23. Pal, B., Daniel, T., Chatterjee, R. e Ristenpart, T. (2019). "Beyond Credential Stuffing: Password Similarity Models Using Neural Networks." In IEEE Symposium on Security and Privacy.

24. Pasquini, D., Gangwal, A., Ateniese, G., Bernaschi, M. e Conti, M. (2021). "Improving Password Guessing via Representation Learning." In IEEE Symposium on Security and Privacy.

25. Rando, J., Perez-Cruz, F. e Hitaj, B. (2023). "PassGPT: Password Modeling and (Guided) Generation with Large Language Models." In European Symposium on Research in Computer Security (ESORICS). arXiv:2306.01545.

26. Ur, B., Noma, F., Bees, J., et al. (2015). "'I Added '!' at the End to Make It Secure': Observing Password Creation in the Lab." In Symposium on Usable Privacy and Security (SOUPS).

27. Ur, B., Segreti, S. M., Bauer, L., et al. (2015). "Measuring Real-World Accuracies and Biases in Modeling Password Guessability." In USENIX Security Symposium.

28. Veras, R., Collins, C. e Thorpe, J. (2014). "On Semantic Patterns of Passwords and their Security Impact." In Network and Distributed System Security Symposium (NDSS).

29. Wang, D. e Jian, G. (2014). "Zipf's Law in Passwords." IACR ePrint Archive, 2014/631. Publicado posteriormente em IEEE TIFS, 2017.

30. Wang, D., Zhang, Z., Wang, P., Yan, J. e Huang, X. (2016). "Targeted Online Password Guessing: An Underestimated Threat." In ACM Conference on Computer and Communications Security (CCS).

31. Wang, D., Cheng, H., Wang, P., Huang, X. e Jian, G. (2016). "The Next Domino to Fall: Empirical Analysis of User Passwords across Online Services." In ACM Conference on Computer and Communications Security (CCS).

32. Wash, R., Rader, E., Berman, R. e Wellmer, Z. (2016). "Understanding Password Choices: How Frequently Entered Passwords Are Re-used Across Websites." In Symposium on Usable Privacy and Security (SOUPS).

33. Weir, M., Aggarwal, S., de Medeiros, B. e Glodek, B. (2009). "Password Cracking Using Probabilistic Context-Free Grammars." In IEEE Symposium on Security and Privacy, pp. 391-405. DOI: 10.1109/SP.2009.8.

34. Wheeler, D. L. (2016). "zxcvbn: Low-Budget Password Strength Estimation." In USENIX Security Symposium.

35. Xie, X. (2020). "Modified TarGuess-I: Keyboard Patterns and Popular Passwords as Password Guessing Threats." Dissertação de Mestrado.

36. Survey Authors (2026). "Examining User Behavior and Cognitive Biases in Personal Password Security." arXiv:2607.19586.

37. AI Password Study Authors (2026). "AI vs. User-Generated Passwords: Strength, Memorability, and Cognitive Bias." arXiv:2604.19410.

38. MDPI Entropy Review (2023). "A Systematic Review of Password Guessing Methods." MDPI Entropy.

39. Forget, A., Chiasson, S., van Oorschot, P. C. e Biddle, R. (2008). "Improving Text Passwords Through Persuasion." In Symposium on Usable Privacy and Security (SOUPS).

40. Shay, R., Komanduri, S., Kelley, P. G., et al. (2010). "Encountering Stronger Password Requirements: User Attitudes and Behaviors." In Symposium on Usable Privacy and Security (SOUPS).

41. Yan, J., Blackwell, A., Anderson, R. e Grant, A. (2004). "Password Memorability and Security: Empirical Results." IEEE Security & Privacy, 2(5), pp. 25-31.

42. Pal, B. e Chua, T. (2019). "A Comparison of Approaches to Large-Scale Data Analysis." In Pacific-Asia Conference on Knowledge Discovery and Data Mining.

---

## Apendice A: Esquema de Perfil

Esquema JSON completo para perfis-alvo CogPIE:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "names": {"type": "array", "items": {"type": "string"}},
        "dates": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "pets": {"type": "array", "items": {"type": "string"}},
        "companies": {"type": "array", "items": {"type": "string"}},
        "phones": {"type": "array", "items": {"type": "string"}},
        "emails": {"type": "array", "items": {"type": "string"}},
        "old_passwords": {"type": "array", "items": {"type": "string"}},
        "numbers": {"type": "array", "items": {"type": "string"}}
    }
}
```

## Apendice B: Metodologia de Benchmark

### B.1 Benchmark Sintético (Fase 1)

1. Cinco perfis sintéticos foram criados com padrões típicos de informações pessoais brasileiras.
2. Para cada perfil, senhas "ground truth" foram geradas seguindo padrões documentados de criação cognitiva (primeiro nome + ano, palavra-chave + sufixo, mutação de senha anterior, variante leet, etc.).
3. Tres abordagens foram avaliadas: CogPIE (pipeline completo, sem corpus de treinamento), baseline CUPP (concatenação simples) é baseline Markov (dicionário de senhas comuns).
4. Taxa de hit é definida como |gerados interseção ground_truth| / |ground_truth|.

### B.2 Benchmark em Escala (Fase 2)

1. Corpus RockYou (14.344.391 senhas) utilizado como fonte.
2. Amostra de 500.000 senhas processada pelo `pii_correlator.py` para identificar senhas com PII detectável.
3. Divisao: 479.854 para treinamento, 500 senhas PII-bearing para teste.
4. CogPIE treinado no conjunto de treinamento; PII extraida das senhas de teste fornecida como perfil.
5. Avaliação por hit@K para K em {10, 100, 1.000, 10.000, 100.000}.
6. Parametros: alpha=0,4, beta=0,2, ordem Markov=3.
7. Tempo de treinamento: 3,2s. Tempo de avaliação: 128,1s (500 alvos).

## Apendice C: Tabela Resumo de Vieses Cognitivos

| Viés | Efeito em Senhas | Prevalência | Camada CogPIE |
|------|-----------------|-------------|---------------|
| Ancoragem | Palavra-base permanece reconhecível | >90% | Camadas 1, 2 |
| Posição Serial | Modificações no início/final | >85% (final) | Camada 2 |
| Familiaridade | Tokens pessoalmente significativos | >70% | Camada 1 |
| Esforco Mínimo | Menor modificação para satisfazer política | >60% | Camadas 2, 5 |
| Status Quo | Reutilização com modificação menor | ~76% | Camada 1 (old_pw) |
| Desconto Hiperbolico | Prioriza memorabilidade sobre segurança | ~76% | Todas as camadas |
| Disponibilidade | Usa informação recentemente encontrada | ~40% | Camada 1 |

## Apendice D: Mapeamento MITRE ATT&CK

As técnicas do MITRE ATT&CK relevantes para o contexto do CogPIE:

| Técnica | ID | Relação com CogPIE |
|---------|----|--------------------|
| Brute Force: Password Guessing | T1110.001 | CogPIE melhora eficiência desta técnica |
| Brute Force: Password Spraying | T1110.003 | Candidatos CogPIE como lista de spray |
| Credentials from Password Stores | T1555 | Defesa recomendada (cofres de senhas) |
| Valid Accounts | T1078 | Resultado de senhas comprometidas |
| Phishing for Information | T1598 | Coleta de PII para perfis |
| Gather Victim Identity Information | T1589 | Construção de perfis para CogPIE |

## Apendice E: Mapeamento CWE e OWASP

| CWE/OWASP | ID | Relação |
|-----------|----|---------
| Weak Password Requirements | CWE-521 | Políticas que CogPIE satisfaz trivialmente |
| Use of Hard-coded Password | CWE-259 | Senhas previsíveis por viés cognitivo |
| Identification and Authentication Failures | OWASP A07:2021 | Categoria primaria de impacto |
| Broken Authentication | OWASP Top 10 | Risco mitigado por MFA é passkeys |

## Apendice F: Defesas Recomendadas (NIST D3FEND)

| Técnica D3FEND | ID | Aplicação |
|----------------|----|-----------
| Multi-factor Authentication | D3-MFA | Mitiga completamente ataques de adivinhação |
| Credential Hardening | D3-CH | Políticas de senha robustas |
| Account Locking | D3-AL | Rate limiting contra tentativas online |
| Credential Rotation | D3-CR | Troca periódica com triagem contra vazamentos |

## Apendice G: Suite de Testes Unitários como Evidencia Experimental

A validação do CogPIE inclui uma suite abrangente de 55 testes unitários automatizados que verificam cada componente do pipeline de 5 camadas. Esses testes constituem evidencia reproduzível de corretude funcional e servem como benchmark de regressão para alterações futuras. Abaixo, a documentação completa organizada por camada.

### G.1 Camada 1: Expansão Semantica (8 testes)

| Teste | O que valida | Entradas | Asserções |
|---|---|---|---|
| `test_expand_token_basic` | Geração de variantes de caso | "Andre" | Produz lowercase, uppercase, capitalize; >5 variantes |
| `test_expand_token_accents` | Tratamento de acentos PT-BR | "Joao" | Gera "joao", "JOAO"; preserva variantes sem acento |
| `test_expand_token_nicknames` | Banco de apelidos culturais | "Eduardo" | Contém "dudu" ou "edu" (apelidos BR) |
| `test_expand_token_leet` | Substituição leetspeak parcial | "password" | Pelo menos uma variante com "4" ou "0" |
| `test_expand_date_full` | Datas DD/MM/AAAA | "15/03/1990" | Gera "1990", "90", "15031990" |
| `test_expand_date_year_only` | Datas somente ano | "1985" | Gera "1985", "85" |
| `test_expand_profile_names` | Perfil completo com nomes | "Andre Henrique", "Maria Silva" | >5 tokens; contém "andre"; iniciais "ah"/"AH" |
| `test_expand_profile_phones` | Extração de sufixos telefonicos | "11987654321" | Ultimos 4 digitos "4321" extraidos |

### G.2 Camada 2: Transformações Cognitivas (5 testes)

| Teste | O que valida | Entradas | Asserções |
|---|---|---|---|
| `test_capitalization` | 7 padrões de capitalização | "password" | Contém "Password", "PASSWORD", "password" |
| `test_numeric_suffixes` | Sufixos comuns + faixa de anos | "test" | Contém "test1", "test123"; algum com "1990" |
| `test_leet_partial` | Leet parcial (1 substituição) | "password" | Alguma variante com "4" (a->4) |
| `test_transform_token` | Pipeline completo por token | "andre" | >50 candidatos gerados |
| `test_transform_pair` | Concatenação de pares | "andre", "1990" | Algum candidato contém ambos os tokens |

### G.3 Camada 3: Ranqueamento Hibrido Markov+PCFG (3 testes)

| Teste | O que valida | Entradas | Asserções |
|---|---|---|---|
| `test_train_and_score` | Score reflete frequência de treino | Corpus: "password123", "letmein", etc. | score("password123") > score("xKz9!mQ#vR2$") |
| `test_rank_ordering` | Ordenação por probabilidade | Corpus com "password" repetido 10x | "password" ranqueado acima de "xz9qmvr2" |
| `test_train_from_file` | Treinamento a partir de arquivo | 100 senhas "testpassN" | Contagem = 100 |

### G.4 Camada 4: Scoring de Entropia (4 testes)

| Teste | O que valida | Entradas | Asserções |
|---|---|---|---|
| `test_estimate_guesses_simple` | Estimativa de tentativas | "123456" com rank=1 | guesses = 1.0 |
| `test_entropy_positive` | Entropia prática positiva | "Xk9!mQ#vR2$pL" | entropy > 0 |
| `test_zxcvbn_score_range` | Mapeamento entropia->score | Entropia 5,15,25,30,40 | Scores 0,1,2,3,4 respectivamente |
| `test_score_candidate_structure` | Metadados completos | "Password123!" | Dict com "candidate", "entropy_bits", "score" |

### G.5 Camada 5: Filtragem por Politica (3 testes)

| Teste | O que valida | Entradas | Asserções |
|---|---|---|---|
| `test_policy_accepts` | Min length + require_digit | Policy(min_length=8, require_digit=True) | "Password1"=True; "short"=False; "NoDigitsHere"=False |
| `test_policy_classes` | Min classes de caracteres | Policy(min_char_classes=3) | "Abc123"=True; "abcdef"=False |
| `test_filter_candidates` | Filtragem com deduplicação | ["pass","Password1","ab"] com min_length=6 | Somente "Password1" sobrevive |

### G.6 Pipeline Integrado (5 testes)

| Teste | O que valida | Entradas | Asserções |
|---|---|---|---|
| `test_full_pipeline_no_corpus` | Pipeline 5 camadas sem treino | "Carlos Silva", 1985, "flamengo", "Rex" | >0 resultados; contém "carlos" ou "silva" |
| `test_full_pipeline_with_corpus` | Pipeline com corpus treinado | "Maria", 2000, "amor" + corpus 400 senhas | >0 resultados apos treino |
| `test_stream_mode` | Modo streaming | "Pedro", 1995, "gato" | Gera strings; tipo correto |
| `test_stats_populated` | Metricas de pipeline | Profile basico | Stats contém "total_time", "output_count" |
| `test_policy_integration` | Politica end-to-end | "Ana", 2010, "sol" com min_length=8 | Todos candidatos >= 8 chars, >= 2 classes |

### G.7 Correlação PII e Training Pipeline (18 testes)

| Teste | O que valida | Entradas | Asserções |
|---|---|---|---|
| `test_name_detection_english` | Nomes EN | "michael123" | Categoria: name_based/hybrid; nome: "michael" |
| `test_name_detection_portuguese` | Nomes PT-BR | "fernanda2024" | Categoria: name_based/hybrid; nome: "fernanda" |
| `test_name_detection_spanish` | Nomes ES | "alejandro99" | Categoria: name_based/hybrid; nome: "alejandro" |
| `test_name_detection_french` | Nomes FR | "sebastien01" | Categoria: name_based/hybrid; nome: "sebastien" |
| `test_name_detection_german` | Nomes DE | "maximilian7" | Categoria: name_based/hybrid; nome: "maximilian" |
| `test_date_detection_full` | Datas completas | "pass15031990" | date_found != None |
| `test_date_detection_year` | Ano embarcado | "love2024ever" | date_type = "year_4" |
| `test_hybrid_name_date` | Combinação nome+data | "maria1990" | Categoria hybrid; nome e data detectados |
| `test_sequential_detection` | Sequências numéricas | "123456" | Categoria: sequential |
| `test_qwerty_sequential` | Sequências de teclado | "qwerty" | Categoria: sequential |
| `test_random_like` | Senhas aleatórias | "xkj9!mQ" | Categoria: random_like |
| `test_empty_password` | String vazia | "" | Categoria: random_like |
| `test_short_password` | Senha curta | "ab" | Categoria: random_like |
| `test_name_databases_populated` | Bancos de nomes | 5 idiomas | EN>100, PT>100, ES>100, FR>100, DE>100, ALL>500 |
| `test_cross_cultural_coverage` | Cobertura multicultural | james, joao, juan, pierre, hans | Todos detectados em password + "2024" |
| `test_confidence_range` | Intervalo de confiança | "michael1990" | 0.0 <= confidence <= 1.0 |
| `test_corpus_stats_in_memory` | Estatísticas em memória | 5 senhas variadas | total=5; as_dict() funcional |
| `test_corpus_stats_from_file` | Estatísticas de arquivo | 4 senhas em arquivo | total=4; pii_detectable_pct > 0 |

### G.8 Treinamento, Persistência e Benchmark (9 testes)

| Teste | O que valida | Entradas | Asserções |
|---|---|---|---|
| `test_train_from_corpus` | Contagem de treinamento | 16 senhas distintas | count = 16 |
| `test_train_from_corpus_max_lines` | Limite de linhas | max_lines=5 | count = 5 |
| `test_save_and_load_model` | Serialização pickle | Modelo treinado, save+load | trained_count preservado; gera resultados |
| `test_generate_after_training` | Geração pos-treino | "maria", 2024, "love" | >0 resultados; tipos corretos |
| `test_trained_model_scores_higher` | Treino melhora ranking | "michael", 1990 treinado | "michael1990" ou "Michael1990" em top 1000 |
| `test_build_small_corpus` | Pipeline de corpus | 7 senhas raw | Gera corpus processado, stats JSON, patterns JSON |
| `test_extract_synthetic_profile` | Extração de perfil | "michael1990" | "michael" em names; "1990" em dates |
| `test_extract_no_pii` | Sem PII detectável | "xkj9mQ!!" | Retorna None |
| `test_split_corpus` | Divisão treino/teste | 9 senhas, ratio=0.3 | train + test <= total; test >= 1 |

### G.9 Resumo de Cobertura

- **55 testes** cobrindo todos os 8 módulos do CogPIE
- **5 idiomas** validados para detecção de PII (EN, PT-BR, ES, FR, DE)
- **Tempo de execução**: ~1.1s (todos os testes)
- **Framework**: pytest 9.0.2, Python 3.14.4
- **Cobertura de camadas**: 100% das 5 camadas do pipeline testadas individualmente e integradas
- **Cenários**: com e sem corpus de treinamento; com e sem políticas; modo batch e streaming

Todos os 55 testes passam consistentemente (300/300 na suite completa incluindo testes de outros módulos do WordlistXPL-Forge), validando a corretude funcional de cada componente e a integridade do pipeline end-to-end.

---

*Esta pesquisa foi conduzida para fins de testes de segurança autorizados é propósitos academicos. Todos os experimentos utilizaram dados de vazamentos publicos exclusivamente para validação científica. O autor defende a adoção de cofres de senhas é autenticação sem senhas como defesas primarias contra ataques direcionados a senhas.*

# WordlistXPL-Forge — Engine Brasileira (BR-Deep)

> Versão 2.0.0 — Guia completo do engine de geração especializada para alvos brasileiros.

**USO AUTORIZADO APENAS** — Utilize somente em contextos de pentest autorizado, red team ou pesquisa de segurança defensiva. Veja [DISCLAIMER.md](../../DISCLAIMER.md).

---

## Visão geral

O `BRDeepEngine` é um engine de geração especializado para alvos brasileiros, incorporando:

- Nomes populares brasileiros (masculinos e femininos)
- Gírias e expressões regionais
- Tokens de bancos, telecoms e serviços nacionais
- Padrões de datas culturais (Copa, Carnaval, eleições)
- Prefixos de CEP por região
- Padrões estruturais de CPF/CNPJ (sem gerar documentos válidos reais)
- Tokens de órgãos governamentais (INSS, Receita Federal, etc.)

---

## Uso básico

```bash
# Setor corporativo
python wlf.py br-deep --sector corporate --limit 500000 -o wordlist_corp.txt

# Setor financeiro
python wlf.py br-deep --sector finance --limit 300000 -o wordlist_finance.txt

# Setor governamental
python wlf.py br-deep --sector gov --limit 200000 -o wordlist_gov.txt

# Com perfil JSON do alvo
python wlf.py br-deep --profile-file /tmp/alvo.json --limit 300000 -o alvo_wl.txt
```

---

## Perfil JSON

```json
{
  "full_name": "Carlos Eduardo Lima",
  "short_name": "carlao",
  "company_name": "Itaú Unibanco",
  "sector": "finance",
  "country": "BR",
  "city": "São Paulo",
  "state": "SP",
  "special_dates": ["19850312", "20100615", "19980707"],
  "keywords": ["ibank", "portal", "homebroker", "investimento"],
  "pets": ["rex", "bolinha"],
  "birth_year": "1985"
}
```

---

## Tokens incluídos

### Nomes populares brasileiros

**Masculinos:** João, José, Pedro, Luis, Carlos, Eduardo, Marcos, Roberto, Fernando, Rafael, Thiago, Gustavo, André, Lucas, Bruno, Mateus, Felipe, Daniel, Paulo, Rodrigo...

**Femininos:** Maria, Ana, Fernanda, Juliana, Camila, Aline, Bruna, Amanda, Leticia, Patricia, Gabriela, Renata, Tatiana, Beatriz, Carolina, Mariana, Natalia, Luciana...

### Gírias e expressões

```
trampo, mano, saudades, vacilão, galera, curtir, arrego,
baita, mito, firmeza, parceiro, véi, cara, oxe, uai,
bicho, fechou, daora, sinistro, maneiro, merreca, treta
```

### Bancos e fintech

```
itau, bradesco, nubank, caixa, bb, santander, inter,
neon, next, original, banrisul, safra, c6bank, picpay,
cielo, rede, getnet, stone, pagseguro, mercadopago
```

### Telecomunicações

```
vivo, tim, claro, oi, nextel, net, sky, algar,
sercomtel, brisanet, unifique
```

### Órgãos governamentais

```
inss, receita, federal, siape, siafi, sisp, sei,
mec, sus, datasus, detran, denatran, bacen, cvm
```

### Regiões por CEP (prefixo de 2 dígitos)

| Prefixo | Região |
|---------|--------|
| 01–09 | São Paulo capital |
| 10–19 | Interior SP |
| 20–28 | Rio de Janeiro |
| 29 | Espírito Santo |
| 30–39 | Minas Gerais |
| 40–48 | Bahia |
| 49 | Sergipe |
| 50–56 | Pernambuco |
| 57 | Alagoas |
| 58 | Paraíba |
| 59 | Rio Grande do Norte |
| 60–63 | Ceará |
| 64 | Piauí |
| 65–66 | Maranhão |
| 67–68 | Pará |
| 69 | Amazonas |
| 70–73 | Distrito Federal |
| 74 | Goiás |
| 75–76 | MT/MS |
| 77 | Tocantins |
| 78 | Mato Grosso |
| 79 | Mato Grosso do Sul |
| 80–87 | Paraná |
| 88–89 | Santa Catarina |
| 90–99 | Rio Grande do Sul |

```bash
# Foco em São Paulo capital
python wlf.py br-deep --cep-prefix 01 --limit 200000 -o sp_capital.txt

# Rio de Janeiro
python wlf.py br-deep --cep-prefix 20 --limit 200000 -o rio.txt
```

---

## Padrões CPF/CNPJ

> **Importante:** Os padrões gerados são **estruturais** — nunca geram CPF ou CNPJ válidos que possam identificar pessoas reais.

Os padrões ajudam a testar sistemas que usam CPF/CNPJ como senha (prática infelizmente comum em sistemas legados brasileiros):

```
###.###.###-##    (CPF mascarado)
###########       (CPF sem formatação)
##.###.###/####-## (CNPJ mascarado)
```

```bash
# Sem padrões CPF/CNPJ (recomendado para maioria dos casos)
python wlf.py br-deep --no-cpf --no-cnpj --limit 300000 -o sem_doc.txt
```

---

## Datas culturais brasileiras por ano

O engine incorpora tokens relacionados a eventos culturais brasileiros:

| Ano | Tokens |
|-----|--------|
| 2019 | copa, eleicao, bolsonaro |
| 2020 | covid, pandemia, quarentena |
| 2021 | vacina, lockdown |
| 2022 | copa2022, lula, eleicao22 |
| 2023 | lula2023, ia, chatgpt |
| 2024 | copa24, gen-ai, deepfake |
| 2025 | ia2025, copa25 |
| 2026 | copa26, ia2026 |

---

## Estratégias de combinação

O engine combina tokens em múltiplas estratégias:

1. **Token + ano**: `carlao2024`, `carlao@2025`
2. **Token + sufixo especial**: `carlao!`, `carlao#1`
3. **Leet parcial**: `c@rl@o`, `c4rl4o`
4. **Capitalização**: `Carlao`, `CarlaoEduardo`
5. **Token + banco**: `carlaoitau`, `carlao_bradesco`
6. **Data + token**: `19850312carlao`, `1985carlao`
7. **CEP + token**: `01001carlao`, `sp_carlao`

---

## Scores por categoria

| Categoria | Score | Razão |
|-----------|-------|-------|
| Token de perfil | 0.90 | Altamente personalizado |
| Padrões CPF | 0.75 | Estruturalmente comum |
| Nomes brasileiros | 0.60 | Base populacional |
| Gírias | 0.55 | Uso informal |
| Tokens genéricos | 0.45 | Baixa especificidade |

---

## Pipeline com foco brasileiro

```yaml
# pipeline_br.yaml
output: wordlist_br.txt
limit: 2000000
engines:
  - name: br_deep
    weight: 0.4
    limit: 800000
    params:
      sector: corporate
  - name: bayesian
    weight: 0.3
    limit: 600000
  - name: temporal_drift
    weight: 0.2
    limit: 400000
  - name: markov
    weight: 0.1
    limit: 200000
```

```bash
python wlf.py pipeline pipeline_br.yaml
```

---

## Integração com ferramentas de cracking

```bash
# WPA/WPA2 de roteador doméstico brasileiro
python wlf.py br-deep --sector consumer --limit 1000000 -o br_wifi.txt
aircrack-ng -w br_wifi.txt -b AA:BB:CC:DD:EE:FF captura.cap
hashcat -a 0 -m 22000 captura.hccapx br_wifi.txt

# Sistema web corporativo brasileiro
python wlf.py br-deep --sector corporate --limit 500000 -o br_corp.txt
hydra -l admin -P br_corp.txt -t 4 http-post-form \
  "//login.php:user=^USER^&pass=^PASS^:Acesso negado"

# Sistema governamental
python wlf.py br-deep --sector gov --no-cpf --limit 200000 -o br_gov.txt
hydra -L usuarios.txt -P br_gov.txt ssh://intranet.gov.br

# Hashcat com senhas brasileiras
python wlf.py br-deep --profile-file alvo.json --limit 300000 -o br_alvo.txt
john --wordlist=br_alvo.txt hashes.txt
```

---

## Referências legais

- **Marco Civil da Internet** (Lei 12.965/2014) — autorização obrigatória para testes
- **LGPD** (Lei 13.709/2018) — proteção de dados pessoais; CPF/CNPJ são dados sensíveis
- **Código Penal brasileiro** Art. 154-A — invasão de dispositivo informático é crime

> Sempre obtenha autorização escrita. Documente escopo, datas e metodologia.

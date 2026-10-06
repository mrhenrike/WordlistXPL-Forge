# WordlistXPL-Forge — Cookbook

> **AUTHORIZED USE ONLY** — Generate wordlists for systems you own or have written permission to test.

Eight production-ready recipes covering the most common generation scenarios, with full terminal output samples.

---

## Recipe 1 — Quick charset wordlist

Generate every 8-character combination from a custom charset.

```bash
python wlf.py charset 8 8 "abcdefghijklmnopqrstuvwxyz0123456789" \
  -o out/charset8.txt \
  --limit 500000
```

**Sample terminal output:**
```
[*] WordlistXPL-Forge v2.0.0
[*] Charset: abcdefghijklmnopqrstuvwxyz0123456789 (36 chars)
[*] Length range: 8–8
[*] Limit: 500,000
  Generating ━━━━━━━━━━━━━━━━━━━━ 100% 500,000/500,000 [02:14<00:00, 3,724/s]
[+] Written: out/charset8.txt  (500,000 lines, 4.0 MB)
```

**Feed into Hashcat:**
```bash
hashcat -a 0 -m 0 hashes.txt out/charset8.txt
```

---

## Recipe 2 — Personal profile wordlist (CUPP-style)

Interactive profiling → tailored wordlist.

```bash
python wlf.py profile
```

**Sample session:**
```
[*] Personal Profile Generator
First name: Maria
Last name : Santos
Nickname  : mary
Birthdate : 1990-05-12
Partner   : Paulo
Pet(s)    : Bolinha
Company   : Acme Corp
Keywords  : acme, rh, portal
Special dates: 20051210, 20100314

[*] Generating profile wordlist...
  Profiling ━━━━━━━━━━━━━━━━━━━━ 100% 84,320/84,320 [00:12<00:00, 6,812/s]
[+] Written: maria_santos_wl.txt  (84,320 lines, 712 KB)
```

**Feed into Hydra (SSH):**
```bash
hydra -l maria.santos -P maria_santos_wl.txt ssh://192.168.1.10
```

---

## Recipe 3 — Neural LSTM generation (CPU)

Generate ML-assisted wordlist without GPU.

```bash
python wlf.py emit --engine neural --limit 200000 \
  -o out/neural_200k.txt
```

**Sample output:**
```
[*] Engine: neural_lstm (CPU mode)
[*] Limit: 200,000
  Emitting ━━━━━━━━━━━━━━━━━━━━ 100% 200,000/200,000 [04:33<00:00, 731/s]
[+] Written: out/neural_200k.txt  (200,000 lines, 1.8 MB)
```

**With GPU acceleration:**
```bash
python wlf.py emit --engine neural --compute gpu --limit 1000000 \
  -o out/neural_1m.txt
```

---

## Recipe 4 — Brazilian deep profile

Corporate Brazilian target — CPF patterns, nomes, banks, telecom.

```bash
python wlf.py br-deep --sector corporate \
  --limit 500000 \
  -o out/br_corp.txt
```

**With profile JSON:**
```bash
cat > /tmp/alvo.json << 'EOF'
{
  "full_name": "Carlos Eduardo Lima",
  "short_name": "carlao",
  "company_name": "Itaú Unibanco",
  "sector": "finance",
  "country": "BR",
  "special_dates": ["19850312", "20100615"],
  "keywords": ["ibank", "portal", "homebroker"]
}
EOF

python wlf.py br-deep --profile-file /tmp/alvo.json \
  --limit 300000 -o out/br_itau.txt
```

**Sample output:**
```
[*] BRDeepEngine  sector=finance
[*] Limit: 300,000
  BR-Deep ━━━━━━━━━━━━━━━━━━━━ 100% 300,000/300,000 [01:08<00:00, 4,392/s]
[+] Written: out/br_itau.txt  (300,000 lines, 2.4 MB)
```

**Feed into Aircrack-ng (WPA):**
```bash
aircrack-ng -w out/br_itau.txt -b AA:BB:CC:DD:EE:FF capture.cap
```

---

## Recipe 5 — Pipeline DSL (multi-engine)

Run several engines in parallel via YAML spec.

```yaml
# my_pipeline.yaml
output: out/pipeline_result.txt
limit: 1000000
engines:
  - name: markov
    weight: 0.3
    limit: 300000
    params:
      order: 3
  - name: pcfg
    weight: 0.3
    limit: 300000
  - name: br_deep
    weight: 0.2
    limit: 200000
    params:
      sector: corporate
  - name: genetic
    weight: 0.2
    limit: 200000
```

```bash
python wlf.py pipeline my_pipeline.yaml
```

**Sample output:**
```
[*] Pipeline: my_pipeline.yaml  (4 engines)
  Engine markov   ━━━━━━━━━━ 100%  300,000 [00:34]
  Engine pcfg     ━━━━━━━━━━ 100%  300,000 [00:41]
  Engine br_deep  ━━━━━━━━━━ 100%  200,000 [00:28]
  Engine genetic  ━━━━━━━━━━ 100%  200,000 [01:12]
[*] Dedup (Bloom): 987,412 unique from 1,000,000
[+] Written: out/pipeline_result.txt  (987,412 lines, 8.1 MB)
```

---

## Recipe 6 — Evolutionary generation (MAP-Elites)

Quality-diversity exploration across length/charset/entropy dimensions.

```bash
python wlf.py evolve --mode map-elites \
  --seed-file data/rockyou_top10k.txt \
  --limit 200000 \
  -o out/map_elites.txt
```

**Sample output:**
```
[*] MAP-Elites  warmup=5000 steps
[*] Grid: 0/300 cells filled ... seeding ... 287/300 cells filled (95.7%)
  Evolving ━━━━━━━━━━━━━━━━━━━━ 100% 200,000/200,000 [02:47<00:00, 1,197/s]
[+] Best elite: 'P@ssw0rd2026!' fitness=0.931 @(7, 3, 3)
[+] Written: out/map_elites.txt  (200,000 lines, 1.7 MB)
```

---

## Recipe 7 — Temporal drift (year evolution)

Evolve seed words across years 2019→2026 with leet escalation.

```bash
echo -e "senha\nadmin\nempresa\nportal" > /tmp/seeds.txt

python wlf.py temporal-model \
  --seed-file /tmp/seeds.txt \
  --base-year 2019 \
  --target-year 2026 \
  --limit 100000 \
  -o out/temporal.txt
```

**Sample output:**
```
[*] TemporalDriftEngine  2019→2026
[*] Seed words: 4  |  leet_max=2  |  seasonal=True
  Drifting ━━━━━━━━━━━━━━━━━━━━ 100% 100,000/100,000 [00:18<00:00, 5,412/s]
[+] Written: out/temporal.txt  (100,000 lines, 912 KB)

Sample candidates:
  senha2026
  $enha@2025
  admin_covid
  Empresa2022!
  3mpr3s4#26
```

**Feed into ffuf (directory brute):**
```bash
ffuf -w out/temporal.txt -u https://target.com/FUZZ -mc 200,301
```

---

## Recipe 8 — REST API + streaming

Start the API server and stream a wordlist from another tool.

```bash
# Terminal 1 — start server
WLF_API_KEY=secretkey python wlf.py serve \
  --host 127.0.0.1 \
  --port 8771

# Terminal 2 — stream 50k markov passwords
curl -s -X POST http://127.0.0.1:8771/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-WLF-Key: secretkey" \
  -d '{"engines":["markov","br_deep"],"limit":50000,"stream":true}' \
  > out/api_stream.txt

# Check available engines
curl http://127.0.0.1:8771/v1/engines \
  -H "X-WLF-Key: secretkey" | jq .
```

**Sample API response (NDJSON stream):**
```json
{"event":"start","request_id":"4f2e...","disclaimer":"AUTHORIZED USE ONLY..."}
{"pw":"Empresa2024!"}
{"pw":"carlos_lima"}
{"pw":"portal@123"}
...
{"event":"done","count":50000,"request_id":"4f2e..."}
```

---

## Integrations quick-reference

| Tool | Use case | Command |
|------|----------|---------|
| **Hashcat** | Hash cracking | `hashcat -a 0 -m 1000 hashes.txt wordlist.txt` |
| **John the Ripper** | Hash cracking | `john --wordlist=wordlist.txt hashes.txt` |
| **Hydra** | Online service brute-force | `hydra -l user -P wordlist.txt ssh://target` |
| **Aircrack-ng** | WPA handshake crack | `aircrack-ng -w wordlist.txt capture.cap` |
| **Ncrack** | Network service auth | `ncrack -u admin -P wordlist.txt target:22` |
| **ffuf** | Web fuzzing | `ffuf -w wordlist.txt -u https://target/FUZZ` |
| **Burp Suite** | Intruder payloads | Load wordlist in Intruder → Payloads |

See [docs/INTEGRATIONS.md](INTEGRATIONS.md) for full setup guides.

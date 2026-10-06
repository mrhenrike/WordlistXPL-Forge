# WordlistXPL-Forge — Integration Guide

> **AUTHORIZED USE ONLY** — Use only on systems you own or have explicit written permission to test.

WordlistXPL-Forge **generates** wordlists. The tools below **consume** those wordlists to perform actual credential testing. Keep them separate.

---

## Hashcat

The most powerful offline hash cracker — GPU-accelerated, 400+ hash modes.

### Install

```bash
# Arch / Manjaro
sudo pacman -S hashcat

# Ubuntu / Debian
sudo apt install hashcat

# Check GPU support
hashcat -I
```

### Use WLF output

```bash
# Dictionary attack (mode -a 0)
hashcat -a 0 -m 1000 ntlm_hashes.txt wordlist.txt

# Dictionary + rules
hashcat -a 0 -m 1800 sha512_hashes.txt wordlist.txt -r rules/best64.rule

# Multiple wordlists
hashcat -a 1 -m 0 md5_hashes.txt wordlist1.txt wordlist2.txt

# WPA/WPA2 handshake
hashcat -a 0 -m 22000 capture.hccapx wordlist.txt

# Show cracked
hashcat -m 1000 ntlm_hashes.txt --show
```

### Pipe WLF directly (no temp file)

```bash
python wlf.py emit --engine markov --limit 1000000 | \
  hashcat -a 0 -m 0 md5.txt -
```

---

## John the Ripper (JtR)

Classic offline cracker with excellent automatic hash detection.

### Install

```bash
sudo apt install john           # community edition
# or Jumbo (with GPU + more formats):
git clone https://github.com/openwall/john
cd john/src && ./configure && make -s clean && make -sj4
```

### Use WLF output

```bash
# Wordlist attack
john --wordlist=wordlist.txt hashes.txt

# Auto-detect format
john --wordlist=wordlist.txt --format=auto hashes.txt

# With rules
john --wordlist=wordlist.txt --rules=best64 hashes.txt

# Show cracked
john --show hashes.txt

# Linux /etc/shadow
sudo unshadow /etc/passwd /etc/shadow > shadow.db
john --wordlist=wordlist.txt shadow.db
```

---

## Hydra

Fast, parallelized online brute-force across 50+ protocols.

### Install

```bash
sudo apt install hydra
# or from source: https://github.com/vanhauser-thc/thc-hydra
```

### Use WLF output

```bash
# SSH
hydra -l admin -P wordlist.txt ssh://192.168.1.10

# HTTP POST login form
hydra -l admin -P wordlist.txt \
  192.168.1.10 http-post-form \
  "/login:user=^USER^&pass=^PASS^:Invalid credentials"

# FTP
hydra -l ftp_user -P wordlist.txt ftp://192.168.1.10

# Multiple users
hydra -L users.txt -P wordlist.txt ssh://192.168.1.10

# RDP
hydra -l administrator -P wordlist.txt rdp://192.168.1.10

# Rate limit (avoid lockout)
hydra -l admin -P wordlist.txt -t 4 -W 3 ssh://192.168.1.10
```

---

## Aircrack-ng

WPA/WPA2 and WEP WiFi cracking suite.

### Install

```bash
sudo apt install aircrack-ng
```

### Capture + crack workflow

```bash
# Put interface in monitor mode
sudo airmon-ng start wlan0

# Capture handshake
sudo airodump-ng --bssid AA:BB:CC:DD:EE:FF -c 6 -w capture wlan0mon

# Optional: deauth to force handshake
sudo aireplay-ng --deauth 5 -a AA:BB:CC:DD:EE:FF wlan0mon

# Crack with WLF wordlist
aircrack-ng -w wordlist.txt -b AA:BB:CC:DD:EE:FF capture-01.cap

# Brazilian household profile for home routers
python wlf.py br-deep --sector consumer --limit 500000 -o br_wifi.txt
aircrack-ng -w br_wifi.txt -b AA:BB:CC:DD:EE:FF capture.cap
```

---

## Ncrack

Modular network authentication cracker (OpenSSL-based).

### Install

```bash
sudo apt install ncrack
# or from: https://nmap.org/ncrack/
```

### Use WLF output

```bash
# SSH
ncrack -u admin -P wordlist.txt ssh://192.168.1.10

# RDP
ncrack -u administrator -P wordlist.txt rdp://192.168.1.10

# Multiple services
ncrack -u root -P wordlist.txt \
  ssh://192.168.1.10 ftp://192.168.1.20

# With rate control
ncrack --connection-limit 5 -u admin -P wordlist.txt ssh://192.168.1.10
```

---

## ffuf (web fuzzing)

Extremely fast web fuzzer — directories, parameters, headers, virtual hosts.

### Install

```bash
# Go required
go install github.com/ffuf/ffuf/v2@latest

# or download binary from GitHub releases
```

### Use WLF output

```bash
# Directory fuzzing
ffuf -w wordlist.txt -u https://target.com/FUZZ -mc 200,301,302

# Parameter fuzzing
ffuf -w wordlist.txt -u "https://target.com/login?user=FUZZ" -mc 200

# Password spraying (POST)
ffuf -w wordlist.txt \
  -u https://target.com/api/login \
  -X POST \
  -d '{"username":"admin","password":"FUZZ"}' \
  -H "Content-Type: application/json" \
  -mc 200

# Virtual host discovery
ffuf -w wordlist.txt \
  -u https://target.com \
  -H "Host: FUZZ.target.com" \
  -fc 404

# Generate directory wordlist with temporal drift
python wlf.py temporal-model \
  --seed-file common_dirs.txt \
  --limit 50000 \
  -o dirs_drift.txt
ffuf -w dirs_drift.txt -u https://target.com/FUZZ
```

---

## Burp Suite

Industry-standard web application security testing proxy.

### Integration

1. **Intruder** → **Payloads** → Payload type: **Simple list** → **Load...** → select WLF output
2. **Cluster bomb** for username + password pairs:
   - Position §user§: load `users.txt`
   - Position §pass§: load WLF wordlist
3. **Extensions** → BurpBounty or TurboIntruder for high-speed delivery

```bash
# Generate targeted web app wordlist
python wlf.py scrape https://target.com --with-numbers --with-spaces \
  -o target_words.txt

# Then enhance with profile
python wlf.py profile  # generates profile_wl.txt

# Merge + dedup
python wlf.py merge target_words.txt profile_wl.txt \
  --sort frequency \
  -o combined.txt
```

---

## Medusa

Parallel network login brute-forcer.

```bash
sudo apt install medusa

# SSH
medusa -h 192.168.1.10 -u admin -P wordlist.txt -M ssh

# HTTP form
medusa -h target.com -u admin -P wordlist.txt \
  -M http -m "FORM:/login:user=^USER^&pass=^PASS^:Incorrect"
```

---

## Choosing the right tool

| Scenario | Recommended |
|----------|------------|
| Offline hash (MD5/NTLM/SHA) | Hashcat (GPU) |
| Offline hash (slow, CPU) | John the Ripper |
| WPA/WPA2 WiFi | Aircrack-ng + Hashcat |
| SSH / FTP / RDP brute | Hydra or Ncrack |
| Web application login | Hydra, Hydra or Burp Intruder |
| Directory discovery | ffuf |
| General web proxy testing | Burp Suite |

> All tools require explicit authorization. Never test systems you do not own or have written permission to test.

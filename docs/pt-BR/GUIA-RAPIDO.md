# WordlistXPL-Forge — Guia Rápido (PT-BR)

> Versão 2.0.0 — Gerador de wordlists para pentest e red team autorizados.

**USO AUTORIZADO APENAS** — Utilize somente em sistemas que você possui ou para os quais tem permissão escrita para testar. Veja [DISCLAIMER.md](../../DISCLAIMER.md) para os termos completos.

---

## Instalação rápida

```bash
# Clonar repositório
git clone https://github.com/mrhenrike/WordlistXPL-Forge.git
cd WordlistXPL-Forge

# Instalar dependências básicas
pip install -r requirements.txt

# Instalar com GPU/Neural (opcional)
pip install -r requirements-gpu.txt
# ou
pip install wordlistxpl-forge[neural]

# Verificar instalação
python wlf.py --version
```

---

## Uso básico

```bash
# Menu interativo
python wlf.py

# Ajuda geral
python wlf.py --help

# Ajuda de um comando específico
python wlf.py profile --help
python wlf.py br-deep --help
```

---

## Geração por charset

```bash
# Todas as combinações de 8 caracteres alfanuméricos
python wlf.py charset 8 8 "abcdefghijklmnopqrstuvwxyz0123456789" \
  --limit 1000000 -o alfanumerico.txt

# Comprimentos variados (6 a 10)
python wlf.py charset 6 10 "abc123!@" --limit 500000 -o variado.txt
```

---

## Perfil pessoal (estilo CUPP)

```bash
# Modo interativo — preenche dados do alvo
python wlf.py profile

# Com parâmetros diretos
python wlf.py profile \
  --name "Ana Silva" \
  --birthdate 19920315 \
  --company "Banco Itaú" \
  --pets cachorro,bolinha \
  --depth 4 \
  -o ana_silva.txt
```

---

## Perfil brasileiro profundo

Geração especializada para alvos brasileiros:

```bash
# Setor corporativo
python wlf.py br-deep --sector corporate --limit 500000 -o br_corp.txt

# Setor financeiro com perfil JSON
cat > /tmp/alvo.json << 'EOF'
{
  "full_name": "Carlos Eduardo Lima",
  "short_name": "carlao",
  "company_name": "Bradesco",
  "sector": "finance",
  "country": "BR",
  "special_dates": ["19870805", "20100301"],
  "keywords": ["bradesco", "homebanking", "app"]
}
EOF

python wlf.py br-deep --profile-file /tmp/alvo.json \
  --limit 300000 -o br_bradesco.txt

# Sem padrões de CPF
python wlf.py br-deep --sector gov --no-cpf --limit 200000 -o br_gov.txt
```

Tokens incluídos:
- **Nomes populares BR**: Ana, Carlos, Eduardo, Fernanda, João...
- **Gírias**: trampo, saudades, mano, vacilão, galera...
- **Bancos**: itau, bradesco, nubank, caixa, bb, santander...
- **Telecoms**: vivo, tim, claro, oi...
- **Gov**: inss, receita, cpf, cnpj, pix, siape...
- **Regiões CEP**: 01xxx (SP-capital), 20xxx (RJ), 40xxx (BA)...

---

## Pipeline multi-engine (YAML)

```yaml
# meu_pipeline.yaml
output: resultado.txt
limit: 1000000
engines:
  - name: markov
    weight: 0.3
    limit: 300000
  - name: pcfg
    weight: 0.2
    limit: 200000
  - name: br_deep
    weight: 0.3
    limit: 300000
    params:
      sector: corporate
  - name: genetic
    weight: 0.2
    limit: 200000
```

```bash
python wlf.py pipeline meu_pipeline.yaml
```

---

## Geração evolutiva

```bash
# Algoritmo genético (GA)
python wlf.py evolve --mode genetic \
  --seed-file dados/senhas_referencia.txt \
  --limit 200000 -o genetico.txt

# MAP-Elites (diversidade estrutural)
python wlf.py evolve --mode map-elites \
  --seed-file dados/senhas_referencia.txt \
  --limit 200000 -o map_elites.txt
```

---

## Derivação temporal (evolução por anos)

```bash
echo -e "senha\nempresa\nportal\nadmin" > sementes.txt

python wlf.py temporal-model \
  --seed-file sementes.txt \
  --base-year 2019 \
  --target-year 2026 \
  --limit 100000 \
  -o temporal.txt
```

Exemplos de candidatos gerados:
```
senha2026
$enha@2025
empresa_covid
Portal2022!
3mpr3s@#26
```

---

## Engines neurais (requer PyTorch)

```bash
# Instalar suporte neural
pip install wordlistxpl-forge[neural]

# GAN
python wlf.py neural gan --limit 200000 --compute gpu -o gan.txt

# Transformer (similar ao PassGPT)
python wlf.py neural transformer --prefix "Admin" --limit 100000 -o transformer.txt

# VAE com âncora
python wlf.py neural vae --anchor "Admin2024!" --limit 50000 -o vae.txt

# Masked LM — preencher template
python wlf.py neural masked-lm fill "Admin????@2025!" --limit 50000 -o mlm.txt
```

---

## API REST

```bash
# Iniciar servidor (somente localhost por padrão)
WLF_API_KEY=minhaChave python wlf.py serve

# Gerar wordlist via API (stream NDJSON)
curl -s -X POST http://127.0.0.1:8771/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-WLF-Key: minhaChave" \
  -d '{"engines":["markov","br_deep"],"limit":10000}' \
  > wordlist_api.txt

# Listar engines disponíveis
curl http://127.0.0.1:8771/v1/engines \
  -H "X-WLF-Key: minhaChave" | python3 -m json.tool
```

---

## Integração com ferramentas de cracking

WordlistXPL-Forge **gera** — outras ferramentas **usam**:

```bash
# Hashcat (hash MD5)
python wlf.py emit --engine markov --limit 1000000 | \
  hashcat -a 0 -m 0 hashes_md5.txt -

# Hashcat (WPA handshake)
python wlf.py br-deep --sector consumer --limit 500000 -o wifi_br.txt
hashcat -a 0 -m 22000 captura.hccapx wifi_br.txt

# John the Ripper
python wlf.py profile --name "Alvo" --depth 4 -o perfil.txt
john --wordlist=perfil.txt hashes.txt

# Hydra (SSH)
python wlf.py br-deep --sector corporate --limit 100000 -o wordlist.txt
hydra -l admin -P wordlist.txt ssh://192.168.1.10

# Aircrack-ng
python wlf.py br-deep --sector consumer --limit 500000 -o wifi.txt
aircrack-ng -w wifi.txt -b AA:BB:CC:DD:EE:FF captura.cap

# ffuf (web fuzzing)
python wlf.py temporal-model --seed-file seeds.txt -o dirs.txt
ffuf -w dirs.txt -u https://alvo.com/FUZZ -mc 200,301
```

Ver guia completo: [docs/INTEGRATIONS.md](../INTEGRATIONS.md)

---

## Sessões (pause / resume)

```bash
# Listar sessões salvas
python wlf.py session list

# Continuar sessão interrompida
python wlf.py session resume abc123def456
```

---

## Opções globais importantes

```
--limit N           Número máximo de linhas (0 = ilimitado)
--timeout SECONDS   Parar após N segundos
--threads N         Threads de trabalho
--compute auto      Backend: auto, cpu, gpu
--ram-budget-pct %  Limite de RAM (default: 50%)
--min-len N         Comprimento mínimo
--max-len N         Comprimento máximo
-o FILE             Arquivo de saída
```

---

## Dicas de segurança

1. **Nunca** use em sistemas sem autorização escrita
2. Guarde evidência da autorização (e-mail, contrato, escopo de pentest)
3. Limite o rate de tentativas para não causar lockout de contas
4. Documente tudo no relatório de pentest
5. Descarte wordlists contendo dados pessoais após o engajamento

Ver guia completo em PT-BR: [docs/pt-br/BR-DEEP.md](BR-DEEP.md)

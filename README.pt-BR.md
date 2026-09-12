# WordlistXPL-Forge

<p align="center">
  <img src="https://img.shields.io/github/stars/mrhenrike/WordlistXPL-Forge?style=flat-square" alt="GitHub Stars">
  <img src="https://img.shields.io/github/license/mrhenrike/WordlistXPL-Forge?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+">
</p>

Toolkit de geração de wordlists para pentest e red team autorizados. Membro oficial da suíte **XPL-Forge**. CLI: `wlf` / `python wlf.py`.

Autor: André Henrique (`mrhenrike`) | União Geek | https://uniaogeek.com.br/

> Referência completa de cada subcomando, flag, entrada e saída: [docs/COMMAND-COVERAGE.md](docs/COMMAND-COVERAGE.md) · [Wiki](https://github.com/mrhenrike/WordlistXPL-Forge/wiki)

---

## Aviso

Este programa é só para **testes de segurança autorizados, laboratório e educação**. O autor **não se responsabiliza** por uso indevido do código nem das funções.

O gerador emite **muitos** padrões de senha e username (nome, data, marca, leet, ano, teclado, gramática e similares).

Se você, sua empresa ou um usuário montam segredos a partir de **informação pública**, padrões previsíveis ou dados pessoais (nome, time, pet, data, marca, domínio), a chance de o programa emitir uma wordlist com uma senha ou username **real** é **altíssima, quase certa**.

Isso não é leak e não prova comprometimento prévio. É senha fraca ou previsível. Use gerenciador de senhas e MFA.

Este repositório **não** distribui o corpus brasileiro de senhas (`wlist_brasil`). Distribui credenciais default de fabricantes, amostras de username e listas de lab.

---

## Instalação

```bash
pip install wordlistxpl-forge
pip install wordlistxpl-forge[full]
```

```bash
git clone https://github.com/mrhenrike/WordlistXPL-Forge.git
cd WordlistXPL-Forge
pip install -r requirements.txt pyyaml
python wlf.py --help
```

Cobertura de comandos: [docs/COMMAND-COVERAGE.md](docs/COMMAND-COVERAGE.md)

## Licença

MIT. Ver [LICENSE](LICENSE).

[English](README.md)

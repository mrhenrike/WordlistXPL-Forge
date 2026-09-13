# `affix`

Camada de mutacao de afixos compostos: encadeia data e especiais sobre uma wordlist inteira em uma unica passada.

Gera, para cada palavra base, a data sozinha, especial+data, data+especial e especial+data+especial (ex.: `0724`, `@0724`, `0724!`, `@0724!`). Isso garante o encadeamento de dois afixos que um unico `combiner --tails` ou um `mutate --suffixes` simples nao produzem automaticamente. Tambem pode emitir um ruleset hashcat para usar com `rules apply`.

## Fluxo recomendado (combiner -> affix)

Use o `combiner` (que conhece os componentes e gera CamelCase e compostos com palavras de ligacao) seguido do `affix` (que encadeia os afixos compostos de data/especial):

```text
wlf.py combiner nerd trilha ariane --titlecase --link-lang pt --assume-yes --connectors 'EMPTY,_,.,na,no,da' -o bases.lst
wlf.py affix bases.lst --dates '0724' --specials '!,@,#' -o final.lst
```

Isso reproduz padroes como `NerdTrilha@0724!`, `nerdnatrilha0724!` e `ariane@0724!` numa unica execucao.

## Ruleset para hashcat / John

Em vez de expandir, o `affix` pode emitir um ruleset hashcat (regras de append) para usar com `rules apply`, hashcat `-r` ou John:

```text
wlf.py affix --dates '0724,1988' --specials '!,@,#' --emit-ruleset affix.rule
wlf.py rules apply --wordlist bases.lst --rules affix.rule -o final.lst
```

Cada afixo composto vira uma cadeia de funcoes `$x`, por exemplo o afixo `@0724!` vira `$@ $0 $7 $2 $4 $!`.

## Principais flags

- `--dates LIST` (obrigatorio): nucleos numericos (datas/anos), ex.: `0724,1988`.
- `--specials LIST`: especiais em volta dos nucleos (padrao: `!,@,#`).
- `--positions {suffix,prefix,both}`: onde os especiais aparecem (padrao: both).
- `--titlecase`: adiciona variante CamelCase por token de cada base.
- `--case`: adiciona variantes de caixa (minuscula/MAIUSCULA/Titulo).
- `--emit-ruleset FILE`: grava o ruleset hashcat em vez de expandir.

Sintaxe e flags completas: ver a pagina em ingles correspondente. CLI em ingles.

Smoke valid: exit 0
Smoke invalid: exit 0

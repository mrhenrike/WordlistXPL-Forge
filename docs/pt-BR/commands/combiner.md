# `combiner`

Combina palavras-chave em permutacoes com conectores.

Recursos adicionais (ver detalhes na pagina em ingles):

- `--titlecase`: capitaliza cada componente, gerando compostos CamelCase (ex.: `nerd trilha` -> `NerdTrilha`). A deduplicacao passou a ser sensivel a maiusculas/minusculas, entao `nerdtrilha`, `NerdTrilha` e `NERDTRILHA` sao candidatos distintos.
- `--affix-specials`: envolve caracteres especiais em volta de sufixos numericos, gerando afixos compostos (ex.: `--tails '0724' --affix-specials '!,@,#'` produz `word@0724`, `word0724!`, `word@0724!`).
- `--link-lang` / `--link-words`: adiciona palavras de ligacao (artigos, preposicoes, conjuncoes) como conectores entre componentes, ex.: `nerd na trilha` -> `nerdnatrilha`. Idiomas: pt, en, es, fr, it, de, ou `all`.
- `--assume-yes`: pula a pergunta de confirmacao das palavras de ligacao (para automacao).

As palavras de ligacao so entram quando voce pede um idioma e, em sessao interativa, apenas apos confirmar a pergunta. Responda `n` para gerar sem elas.

Exemplo que reproduz padroes como `NerdTrilha@0724!` e `nerdnatrilha0724!`:

```text
wlf.py combiner nerd trilha ariane --titlecase --affix-specials '!,@,#' --link-lang pt --tails '0724' --connectors 'EMPTY,_,.,#,@'
```

Sintaxe e flags completas: ver a pagina em ingles correspondente. CLI em ingles.

Smoke valid: exit 0
Smoke invalid: exit 0


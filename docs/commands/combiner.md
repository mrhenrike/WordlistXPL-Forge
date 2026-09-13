# `combiner`

Generate wordlists from keyword permutations with connectors.

## Syntax

```text
__          _______ _    _         
 \ \        / /  ____| |  | |        
  \ \  /\  / /| |__  | |__| |       
   \ \/  \/ / |  __| |  __  |       
    \  /\  /  | |    | |  | |       
     \/  \/   |_|    |_|  |_|       

  WordlistXPL-Forge  v1.2.0
  Author: André Henrique (@mrhenrike)
  Unified wordlist generation for pentest & red team

usage: wlf.py combiner [-h] [--keywords-file FILE] [--connectors LIST]
                       [--tails LIST] [--depth DEPTH] [--abbreviation]
                       [--reverse] [--leet] [--lowercase] [--titlecase]
                       [--affix-specials LIST] [--link-lang LANGS]
                       [--link-words LIST] [--assume-yes] [--min-len MIN_LEN]
                       [--max-len MAX_LEN] [-o OUTPUT]
                       [keywords ...]

Generate wordlists from keyword permutations with connectors.

Examples:
  wlf.py combiner admin password secret
  wlf.py combiner admin test --connectors ',-,_,.,EMPTY' --leet --reverse
  wlf.py combiner --keywords-file keywords.txt --depth 3 --abbreviation
  wlf.py combiner brandx corp 2026 --tails '!,@,#,123' -o wordlist.lst
  wlf.py combiner nerd trilha --titlecase --tails '0724' --affix-specials '!,@,#'
  wlf.py combiner nerd trilha --link-lang pt --tails '0724!'

positional arguments:
  keywords              Keywords to combine

options:
  -h, --help            show this help message and exit
  --keywords-file FILE  File with one keyword per line
  --connectors LIST     Comma-separated connectors (use EMPTY for no
                        separator, default: EMPTY,-,_,.,@,#)
  --tails LIST          Comma-separated numeric/special tails to append
  --depth DEPTH         Max permutation depth (0 = all, default: 0)
  --abbreviation        Generate abbreviation variants
  --reverse             Generate reversed variants
  --leet                Generate leet speak variants
  --lowercase           Add lowercase duplicates
  --titlecase           Capitalize each component before joining (CamelCase,
                        e.g. NerdTrilha)
  --affix-specials LIST
                        Special chars wrapped around numeric tails for
                        composite affixes (e.g. '!,@,#' yields word@0724,
                        word0724!, word@0724!)
  --link-lang LANGS     Add linguistic linking words as connectors for the
                        given languages (comma-separated codes/aliases or
                        'all': pt,en,es,fr,it,de). Prompts for confirmation
  --link-words LIST     Explicit extra linking words to use as connectors
                        (comma-separated)
  --assume-yes          Skip the linking-words confirmation prompt (for
                        automation)
  --min-len MIN_LEN     Minimum output length (default: 1)
  --max-len MAX_LEN     Maximum output length (default: 64)
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `keywords` | - | no | Keywords to combine |
| `--keywords-file` | - | no | File with one keyword per line |
| `--connectors` | - | no | Comma-separated connectors (use EMPTY for no separator, default: EMPTY,-,_,.,@,#) |
| `--tails` | - | no | Comma-separated numeric/special tails to append |
| `--depth` | 0 | no | Max permutation depth (0 = all, default: 0) |
| `--abbreviation` | False | no | Generate abbreviation variants |
| `--reverse` | False | no | Generate reversed variants |
| `--leet` | False | no | Generate leet speak variants |
| `--lowercase` | False | no | Add lowercase duplicates |
| `--titlecase` | False | no | Capitalize each component before joining (CamelCase, e.g. `NerdTrilha`) |
| `--affix-specials` | - | no | Special chars wrapped around numeric tails for composite affixes (e.g. `!,@,#` yields `word@0724`, `word0724!`, `word@0724!`) |
| `--link-lang` | - | no | Add linguistic linking words as connectors for the given languages (comma-separated codes/aliases or `all`: pt,en,es,fr,it,de). Prompts for confirmation |
| `--link-words` | - | no | Explicit extra linking words to use as connectors (comma-separated) |
| `--assume-yes` | False | no | Skip the linking-words confirmation prompt (for automation) |
| `--min-len` | 1 | no | Minimum output length (default: 1) |
| `--max-len` | 64 | no | Maximum output length (default: 64) |
| `-o, --output` | - | no | Output file |

## Composite affixes and casing

Real-world passwords often chain two affixes and mix casing. Three flags cover
these human patterns:

- `--titlecase` capitalizes each component, producing CamelCase compounds such
  as `NerdTrilha` from `nerd trilha`. Deduplication is case-sensitive, so
  `nerdtrilha`, `NerdTrilha` and `NERDTRILHA` are all kept as distinct
  candidates.
- `--affix-specials` wraps a leading and/or trailing special around numeric
  tails, so `--tails '0724' --affix-specials '!,@,#'` yields `word0724`,
  `word@0724`, `word0724!`, `word@0724!`, and every other combination.
- `--link-lang` / `--link-words` add short function words (articles,
  prepositions, conjunctions) as connectors between components, for example the
  Portuguese `nerd na trilha -> nerdnatrilha`. See the section below.

Combining them reproduces patterns like `NerdTrilha@0724!`, `nerdtrilha#0724!`
and `nerdnatrilha0724!` in a single run:

```text
wlf.py combiner nerd trilha ariane \
  --titlecase --affix-specials '!,@,#' --link-lang pt \
  --tails '0724' --connectors 'EMPTY,_,.,#,@'
```

## Linguistic linking words

`--link-lang` pulls short connecting words from a curated per-language
dictionary (`pt`, `en`, `es`, `fr`, `it`, `de`, or `all`). These are added to
the connector set only when you request a language, and, in an interactive
session, only after you confirm the prompt:

```text
  Include 20 linguistic linking words (de, da, do, das, dos, na, no, ...) as connectors? [Y/n]:
```

Answer `n` to generate without them. Use `--assume-yes` to skip the prompt in
scripts and pipelines. `--link-words` lets you pass your own linkers directly
(comma-separated) without a language dictionary.

Because linkers are function words, they only make sense between real tokens
(compound expressions or phrases); they are never appended as blind tails.

## Input combinations

- Minimum: `wlf combiner --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 0

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.


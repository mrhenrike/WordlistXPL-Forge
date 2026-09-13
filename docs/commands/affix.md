# `affix`

Composite-affix mutation layer: chain date and special affixes over a wordlist in a single pass.

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

usage: wlf.py affix [-h] [--wordlist FILE] --dates LIST [--specials LIST]
                    [--positions {suffix,prefix,both}] [--titlecase] [--case]
                    [--bare-specials] [--no-base] [--no-dedupe]
                    [--emit-ruleset FILE] [-o OUTPUT]
                    [keywords ...]

Append composite affixes to a wordlist in a single pass: the core
alone, special+core, core+special, and special+core+special (e.g.
0724, @0724, 0724!, @0724!). Guarantees two-affix chaining that a
single combiner --tails or plain mutate --suffixes does not produce.
Can also emit a hashcat rule set for use with 'rules apply'.

Examples:
  wlf.py combiner nerd trilha --titlecase | wlf.py affix - --dates '0724,1988'
  wlf.py affix base.lst --dates '0724,2806' --specials '!,@,#' -o out.lst
  wlf.py affix base.lst --dates '0724' --case -o out.lst
  wlf.py affix nerdtrilha --dates '0724' --titlecase
  wlf.py affix --dates '0724,1988' --specials '!,@,#' --emit-ruleset affix.rule
  wlf.py rules apply --wordlist base.lst --rules affix.rule -o out.lst

positional arguments:
  keywords              Inline base words (or use WORDLIST / '-' for stdin)

options:
  -h, --help            show this help message and exit
  --wordlist FILE       Input wordlist file, or '-' for stdin
  --dates LIST          Comma-separated numeric cores (dates/years), e.g. '0724,1988'
  --specials LIST       Comma-separated special chars to wrap around cores (default: !,@,#)
  --positions {suffix,prefix,both}
                        Where specials may appear relative to the core (default: both)
  --titlecase           Also emit a per-token CamelCase variant of each base word
  --case                Also emit lower/UPPER/Title case variants of each base word
  --bare-specials       Also append lone specials (e.g. word!) independent of cores
  --no-base             Do not emit the untouched base words
  --no-dedupe           Allow duplicate outputs
  --emit-ruleset FILE   Write a hashcat rule set for these affixes instead of expanding
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `keywords` | - | no | Inline base words (or use a WORDLIST path / `-` for stdin). A single existing-file token is treated as the wordlist |
| `--wordlist` | - | no | Input wordlist file, or `-` for stdin |
| `--dates` | - | yes | Comma-separated numeric cores (dates/years), e.g. `0724,1988` |
| `--specials` | `!,@,#` | no | Comma-separated special chars to wrap around cores |
| `--positions` | both | no | Where specials may appear relative to the core (`suffix`, `prefix`, `both`) |
| `--titlecase` | False | no | Also emit a per-token CamelCase variant of each base word |
| `--case` | False | no | Also emit lower/UPPER/Title case variants of each base word |
| `--bare-specials` | False | no | Also append lone specials (e.g. `word!`) independent of cores |
| `--no-base` | False | no | Do not emit the untouched base words |
| `--no-dedupe` | False | no | Allow duplicate outputs |
| `--emit-ruleset` | - | no | Write a hashcat rule set for these affixes instead of expanding |
| `-o, --output` | - | no | Output file |

## Why this exists

Real passwords frequently chain two affixes: a date plus a trailing special, or
a leading special plus a date plus a trailing special (`nerdtrilha0724!`,
`nerdtrilha@0724!`, `@0724!`). A single `combiner --tails` pass appends one tail,
and a plain `mutate --suffixes` requires you to enumerate every composite by
hand. `affix` produces the full core/special matrix in one pass:

```text
word0724   word@0724   word0724!   word@0724!   word#0724@   ...
```

## Pipeline with combiner

The intended workflow is `combiner` (which knows the components and can produce
CamelCase and linking-word compounds) followed by `affix` (which chains the
composite date/special affixes):

```text
wlf.py combiner nerd trilha ariane \
  --titlecase --link-lang pt --assume-yes \
  --connectors 'EMPTY,_,.,na,no,da' -o bases.lst

wlf.py affix bases.lst --dates '0724' --specials '!,@,#' -o final.lst
```

This reproduces patterns such as `NerdTrilha@0724!`, `nerdnatrilha0724!` and
`ariane@0724!` in a single run.

## Ruleset export for hashcat / John

Instead of expanding, `affix` can emit a hashcat rule set (append rules), which
you can feed to `rules apply`, hashcat `-r`, or John:

```text
wlf.py affix --dates '0724,1988' --specials '!,@,#' --emit-ruleset affix.rule
wlf.py rules apply --wordlist bases.lst --rules affix.rule -o final.lst
```

Each composite affix becomes a chain of `$x` append functions, for example the
affix `@0724!` becomes `$@ $0 $7 $2 $4 $!`.

## Output

Stdout and/or `-o` / `--output`. When `--emit-ruleset` is given, the rule set is
written to that file and no candidates are generated. Exit 0 on success.

## Notes

Use the combiner `--titlecase` option when you need CamelCase on concatenated
components (for example `NerdTrilha` from `nerd` + `trilha`); the `affix`
`--titlecase` can only raise the first letter of a fully concatenated token
because word boundaries are unknown there.

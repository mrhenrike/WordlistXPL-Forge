# `pcfg train`

Nested mode of `pcfg`.

## Syntax

```text
__          _______ _    _         
 \ \        / /  ____| |  | |        
  \ \  /\  / /| |__  | |__| |       
   \ \/  \/ / |  __| |  __  |       
    \  /\  /  | |    | |  | |       
     \/  \/   |_|    |_|  |_|       

  WordlistXPL-Forge  v1.0.0
  Author: Andr├® Henrique (@mrhenrike)
  Unified wordlist generation for pentest & red team

usage: wlf.py pcfg [-h] [--wordlist FILE [FILE ...]] [--model FILE]
                   [--model-output FILE] [--max-lines MAX_LINES]
                   [--top-structures TOP_STRUCTURES]
                   [--top-terminals TOP_TERMINALS] [--min-len MIN_LEN]
                   [--max-len MAX_LEN] [--limit LIMIT] [-o OUTPUT]
                   [{train,generate}]

Probabilistic Context-Free Grammar engine (Weir et al.).
Train a grammar from password corpora, then generate candidates
in approximate probability order (most likely first).

Examples:
  wlf.py pcfg train --wordlist rockyou.txt
  wlf.py pcfg generate -o candidates.lst
  wlf.py pcfg generate --top-structures 50 --top-terminals 100 --limit 1000000
  wlf.py pcfg generate --model .model/pcfg_grammar.json --min-len 8

positional arguments:
  {train,generate}      Action: train or generate (default: generate)

options:
  -h, --help            show this help message and exit
  --wordlist FILE [FILE ...]
                        Training file(s) - one password per line
  --model FILE          Grammar model file (default: .model/pcfg_grammar.json)
  --model-output FILE   Output path for trained model
  --max-lines MAX_LINES
                        Max training lines (0 = unlimited)
  --top-structures TOP_STRUCTURES
                        Limit to top N structures (0 = all)
  --top-terminals TOP_TERMINALS
                        Limit terminals per class to top N (0 = all)
  --min-len MIN_LEN     Min password length (default: 1)
  --max-len MAX_LEN     Max password length (default: 64)
  --limit LIMIT         Max candidates to generate (0 = unlimited)
  -o, --output OUTPUT   Output file
```

Help exit: 0

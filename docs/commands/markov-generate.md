# `markov generate`

Nested mode of `markov`.

## Syntax

```text
__          _______ _    _         
 \ \        / /  ____| |  | |        
  \ \  /\  / /| |__  | |__| |       
   \ \/  \/ / |  __| |  __  |       
    \  /\  /  | |    | |  | |       
     \/  \/   |_|    |_|  |_|       

  WordlistXPL-Forge  v1.2.0
  Author: Andr├® Henrique (@mrhenrike)
  Unified wordlist generation for pentest & red team

usage: wlf.py markov [-h] [--wordlist FILE [FILE ...]] [--model FILE]
                     [--model-output FILE] [--order ORDER]
                     [--smoothing SMOOTHING] [--max-lines MAX_LINES]
                     [--max-cost MAX_COST] [--min-len MIN_LEN]
                     [--max-len MAX_LEN] [--limit LIMIT] [-o OUTPUT]
                     [{train,generate}]

Positional Markov chain password generator (OMEN-style).
Learns character transition probabilities per position and
generates candidates in ascending cost order.

Examples:
  wlf.py markov train --wordlist rockyou.txt --order 4
  wlf.py markov generate --limit 500000
  wlf.py markov generate --min-len 8 --max-len 12 --max-cost 30

positional arguments:
  {train,generate}      Action: train or generate (default: generate)

options:
  -h, --help            show this help message and exit
  --wordlist FILE [FILE ...]
                        Training file(s)
  --model FILE          Model file (default: .model/markov_model.json)
  --model-output FILE   Output path for trained model
  --order ORDER         N-gram order (default: 3)
  --smoothing SMOOTHING
                        Laplace smoothing alpha for unseen n-grams (default:
                        0.01)
  --max-lines MAX_LINES
                        Max training lines (0 = unlimited)
  --max-cost MAX_COST   Max total cost threshold (0 = no limit)
  --min-len MIN_LEN     Min password length (default: 4)
  --max-len MAX_LEN     Max password length (default: 16)
  --limit LIMIT         Max candidates (0 = unlimited)
  -o, --output OUTPUT   Output file
```

Help exit: 0

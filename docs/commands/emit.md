# emit

Stream ordered candidates from a named engine to stdout (or `-o`).

## Usage

```bash
wlf.py --stream emit --engine markov --model .model/markov_model.json --limit 10000
wlf.py emit --engine pcfg --beam-width 50000 --zipf-s 1.0 -o out.lst
wlf.py emit --engine mask --mask '?l?l?d?d' --limit 50000
wlf.py emit --engine semantic --profile-file target.yaml --limit 20000
```

Engines: `markov` | `pcfg` | `mask` | `semantic`.

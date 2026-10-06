# maskgen

Chunked hashcat-style mask cartesian with ResourceGovernor / GPU batch hints.

```bash
wlf.py --compute gpu maskgen --mask '?l?l?d?d' --limit 100000
wlf.py maskgen --mask '?u?l?l?l?d?d' --chunk 65536 -o masks.lst
```

Keyspaces &gt;5M require `--limit` or `--force`.

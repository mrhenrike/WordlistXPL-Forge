# `hash-gen`

Generate hashes for a wordlist to build test corpora.

## Syntax

```text
 __          _______ _    _         
 \ \        / /  ____| |  | |        
  \ \  /\  / /| |__  | |__| |       
   \ \/  \/ / |  __| |  __  |       
    \  /\  /  | |    | |  | |       
     \/  \/   |_|    |_|  |_|       

  WordlistXPL-Forge  v1.0.0
  Author: André Henrique (@mrhenrike)
  Unified wordlist generation for pentest & red team

usage: wlf.py hash-gen [-h] --wordlist FILE
                       [--algo {md5,sha1,sha224,sha256,sha384,sha512,ntlm,md4,bcrypt,argon2,pbkdf2,scrypt}]
                       [--format {hash,hash:plain,plain:hash}]
                       [--separator SEPARATOR] [-o OUTPUT]

Compute digests for a wordlist to build test corpora. Supports
md5, sha1, sha224, sha256, sha384, sha512, ntlm, md4, bcrypt,
argon2, pbkdf2 and scrypt.

Examples:
  wlf.py hash-gen --wordlist pw.txt --algo ntlm -o ntlm.txt
  wlf.py hash-gen --wordlist pw.txt --algo md5 --format hash:plain -o pot.txt
  wlf.py hash-gen --wordlist pw.txt --algo bcrypt --format plain:hash

options:
  -h, --help            show this help message and exit
  --wordlist FILE       Input wordlist
  --algo {md5,sha1,sha224,sha256,sha384,sha512,ntlm,md4,bcrypt,argon2,pbkdf2,scrypt}
                        Hash algorithm (default: md5)
  --format {hash,hash:plain,plain:hash}
                        Output format (default: hash)
  --separator SEPARATOR
                        Field separator for combined formats (default: ':')
  -o, --output OUTPUT   Output file
```

## Flags

| Flag / arg | Default | Required | Description |
|------------|---------|----------|-------------|
| `--wordlist` | - | yes | Input wordlist |
| `--algo` | 'md5' | no | Hash algorithm (default: md5) |
| `--format` | 'hash' | no | Output format (default: hash) |
| `--separator` | ':' | no | Field separator for combined formats (default: ':') |
| `-o, --output` | - | no | Output file |

## Input combinations

- Minimum: `wlf hash-gen --help`
- Typical: see examples in the syntax block.
- Globals: `--min-len`, `--max-len`, `--limit`, `--threads` when the command generates lists.

## Output

Stdout and/or `-o` / `--output` when the parser exposes it. Exit 0 on success; non-zero on invalid input.

## Smoke

- Valid: exit 0
- Invalid: exit 2

## Notes

Examples use generic labels (`BrandX`, `acme.example`). This repo does not ship `wlist_brasil`.

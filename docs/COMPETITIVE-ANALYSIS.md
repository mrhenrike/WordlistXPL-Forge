# Competitive analysis and feature parity

Reference document mapping WordlistXPL-Forge against the open-source landscape for
wordlist generation, password modeling, entropy scoring, hashing and cracking interop.
The goal is a single toolkit that matches or exceeds the best specialized tools.

## 1. Landscape surveyed

Keyword mutation and profiling:

- `psudohash` (leet, case, padding, year suffixes, keyword combinations)
- `Mentalist` (graphical builder, exports hashcat and John rules)
- `TTPassGen` (regex-like scriptable rules, keyspace estimate, split output)
- `pydictor`, `CUPP`, `bopscrk`

Hashcat and John toolchain:

- `maskprocessor` (per-position mask engine)
- `princeprocessor` (PRINCE chained combinator)
- `kwprocessor` (keyboard walks)
- `hashcat-utils` (combinator, combipow, cutb, splitlen, rli, rli2, rules_optimize, tmesis, topmorph)

Large list operations:

- `rling` and `duplicut` (dedup without sorting, memory bounded, subtraction, frequency)

OSINT wordlists:

- `CeWL` (Ruby site spider)
- `cewlai` (Go, AI enrichment, secret detectors)
- `WordForge` (Wayback, GitHub org, DNS, NER, LLM providers)
- `Cracken` (Rust, smartlist and hybrid mask)

Entropy and strength:

- `zxcvbn` and `zxcvbn-ts` (pattern matching, l33t, keyboard, dates, sequences, HIBP, per-hash crack time)
- `nbvcxz`, `passcore`, `passwordthing`

Neural and probabilistic modeling (state of the art):

- `PassGPT` (GPT-2 transformer, roughly twice the yield of GAN models)
- `PagPassGPT` (pattern guided, more hits and fewer duplicates)
- `PLR-GAN` with Dynamic Password Guessing, `PassGAN`, `GNPassGAN`, `PassFlow`, `FLA` (LSTM)
- `MAYA` unified benchmark: FLA, PassGPT, PCFG and combinations generally beat GANs

Collections:

- `SecLists`, `weakpass` (crack-rate ranked, HIBP-like API), `rockyou`, `RockYou2024`

## 2. WordlistXPL-Forge baseline

Generation: charset (crunch and mask), pattern, profile and cupp, corp, corp-users,
phone, mutate, leet and leet-perm, num2text, phrase, combiner, iwlgen, br-names,
pharma, isp-keygen, dns, osint-perm.

Probabilistic models: pcfg (train and generate), markov (OMEN style), prince, kwalk.

OSINT and extraction: scrape, scrape-target, ocr, extract, default-creds.

Analysis and ranking: analyze (pipal style), pattern-rank, maya-rank, anomaly-score,
benchmark, password-dna, rulegen.

Utilities: merge, sanitize, reverse, mangle, improve, train (ML on SecLists), sysinfo,
compute backend (cpu, gpu, cuda, rocm, mps).

## 3. Gap closure delivered

The following capabilities were added to close the gaps identified above. They are
grouped by the tool families they match or exceed.

Rule engine (matches hashcat rule engine and hashcat-utils rules_optimize):

- `rules apply` runs hashcat and John rules against a wordlist, the equivalent of
  `hashcat --stdout -r rules.rule wordlist`.
- `rules convert` translates between hashcat and John syntaxes.
- `rules optimize` deduplicates and removes no-op rules.

High-performance list operations (matches rling and duplicut and hashcat-utils):

- `dedup` removes duplicates without sorting, order preserving, memory bounded with an
  optional Bloom filter for very large inputs.
- `subtract` removes entries present in one or more other files (rli style).
- `split` splits by entry count, by size, or by length (splitlen style).
- `keyspace` estimates candidate counts and time to exhaust for masks, charsets and rules.

Neural generation (matches FLA and PassGPT families, optional `[neural]` extra):

- `neural train` trains a character level model (LSTM by default, small GPT optional).
- `neural generate` supports temperature sampling, guided generation with a prefix or a
  mask, and Dynamic Password Guessing that adapts to already recovered passwords.
- external checkpoints from PassGPT and PassGAN style tools can be loaded as adapters.

Entropy and strength (matches zxcvbn and zxcvbn-ts):

- `strength` scores passwords with pattern detection (dictionary, l33t, sequences,
  repeats, keyboard, dates), reports guesses and entropy, estimates crack time per
  scenario and per hash, and can query HIBP with k-anonymity.

Hashing and cracking interop (matches name-that-hash, hashid and hcmask exports):

- `hash-id` identifies likely hash types.
- `hash-gen` computes md5, sha1, sha256, sha512, ntlm, bcrypt, argon2, pbkdf2 and scrypt
  for a wordlist to build test corpora.
- `hcmask` exports a `.hcmask` file from mask analysis of a wordlist.

Advanced OSINT and passphrases (matches CeWL, cewlai and WordForge):

- `osint` collects from the Wayback Machine and from GitHub organizations, extracts
  entities with lightweight NER, and can optionally enrich with a local or remote LLM.
- `passphrase` generates diceware and mnemonic passphrases using a CSPRNG.

Evaluation and curation (matches the MAYA benchmark and weakpass ranking):

- `evaluate` compares engines (pcfg, markov, neural and static lists) by guess number and
  coverage against a test split.
- `curate` ranks candidate lists by crack rate against a reference and merges the best.

## 4. Positioning

With the additions above, WordlistXPL-Forge unifies in one CLI the four families that are
usually separate tools: probabilistic and neural generation, a rule engine, high
performance list operations, and OSINT collection, plus entropy scoring and hashing
interop. No single open-source project currently combines all of these.

## 5. Notes

- Neural generation is an optional extra. The core keeps working with pcfg and markov when
  the extra is not installed.
- Examples use generic labels. This repository does not ship corporate data wordlists.

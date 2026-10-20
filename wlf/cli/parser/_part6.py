    p_affix.add_argument("keywords", nargs="*",
                         help="Inline base words (or use WORDLIST / '-' for stdin)")
    p_affix.add_argument("--wordlist", metavar="FILE",
                         help="Input wordlist file, or '-' for stdin")
    p_affix.add_argument("--dates", metavar="LIST", required=True,
                         help="Comma-separated numeric cores (dates/years), e.g. '0724,1988'")
    p_affix.add_argument("--specials", metavar="LIST",
                         help="Comma-separated special chars to wrap around cores (default: !,@,#)")
    p_affix.add_argument("--positions", choices=["suffix", "prefix", "both"], default="both",
                         help="Where specials may appear relative to the core (default: both)")
    p_affix.add_argument("--titlecase", action="store_true",
                         help="Also emit a per-token CamelCase variant of each base word")
    p_affix.add_argument("--case", action="store_true",
                         help="Also emit lower/UPPER/Title case variants of each base word")
    p_affix.add_argument("--bare-specials", dest="bare_specials", action="store_true",
                         help="Also append lone specials (e.g. word!) independent of cores")
    p_affix.add_argument("--no-base", dest="no_base", action="store_true",
                         help="Do not emit the untouched base words")
    p_affix.add_argument("--no-dedupe", dest="no_dedupe", action="store_true",
                         help="Allow duplicate outputs")
    p_affix.add_argument("--emit-ruleset", dest="emit_ruleset", metavar="FILE",
                         help="Write a hashcat rule set for these affixes instead of expanding")
    p_affix.add_argument("-o", "--output", help="Output file")

    # ── dedup ────────────────────────────────────────────────────────────
    p_dd = sub.add_parser(
        "dedup",
        help="Deduplicate a wordlist without sorting (order preserving)",
        description=(
            "Order-preserving deduplication, optionally with a Bloom filter\n"
            "for very large inputs (lower memory, tiny false-positive rate).\n\n"
            "Examples:\n"
            "  wlf.py dedup big.txt -o unique.txt\n"
            "  wlf.py dedup huge.txt --bloom --capacity 50000000 -o unique.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dd.add_argument("wordlist", metavar="WORDLIST", help="Input wordlist")
    p_dd.add_argument("--bloom", action="store_true",
                      help="Use a Bloom filter instead of an exact set")
    p_dd.add_argument("--capacity", type=int, default=1_000_000,
                      help="Expected distinct count for the Bloom filter")
    p_dd.add_argument("-o", "--output", help="Output file")

    # ── subtract ─────────────────────────────────────────────────────────
    p_sub = sub.add_parser(
        "subtract",
        help="Remove entries present in other files (rli style)",
        description=(
            "Yield entries from the input that are not present in any of the\n"
            "removal files. Useful to skip already-cracked or known lists.\n\n"
            "Examples:\n"
            "  wlf.py subtract candidates.txt --remove cracked.txt -o todo.txt\n"
            "  wlf.py subtract all.txt --remove a.txt b.txt -o remaining.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_sub.add_argument("wordlist", metavar="WORDLIST", help="Input wordlist")
    p_sub.add_argument("--remove", nargs="+", metavar="FILE", required=True,
                       help="File(s) whose entries are removed from the output")
    p_sub.add_argument("-o", "--output", help="Output file")

    # ── split ────────────────────────────────────────────────────────────
    p_spl = sub.add_parser(
        "split",
        help="Split a wordlist by count, size or entry length",
        description=(
            "Split a wordlist into multiple parts. Choose one mode:\n"
            "  --lines N     N entries per part\n"
            "  --size SPEC   max size per part (e.g. 50MB)\n"
            "  --by-length   one file per entry length (splitlen style)\n\n"
            "Examples:\n"
            "  wlf.py split big.txt --lines 1000000 -o part\n"
            "  wlf.py split big.txt --size 100MB -o chunk\n"
            "  wlf.py split words.txt --by-length -o bylen"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_spl.add_argument("wordlist", metavar="WORDLIST", help="Input wordlist")
    p_spl.add_argument("--lines", type=int, default=0,
                       help="Max entries per part")
    p_spl.add_argument("--size", default="",
                       help="Max size per part (e.g. 50MB)")
    p_spl.add_argument("--by-length", dest="by_length", action="store_true",
                       help="Group entries into one file per length")
    p_spl.add_argument("-o", "--output", metavar="PREFIX",
                       help="Output path prefix (default: input path)")

    # ── keyspace ─────────────────────────────────────────────────────────
    p_ks = sub.add_parser(
        "keyspace",
        help="Estimate candidate count and time to exhaust",
        description=(
            "Estimate keyspace and time-to-exhaust for a mask, a charset over\n"
            "a length range, or a wordlist optionally multiplied by a rule set.\n\n"
            "Examples:\n"
            "  wlf.py keyspace --mask '?u?l?l?l?d?d?d?d'\n"
            "  wlf.py keyspace --charset abcdef0123456789 --min-len 6 --max-len 8\n"
            "  wlf.py keyspace --wordlist base.txt --rules best64.rule --pps 5e9"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ks.add_argument("--mask", help="Hashcat mask string")
    p_ks.add_argument("--charset", help="Charset for brute-force estimate")
    p_ks.add_argument("--min-len", dest="min_len", type=int, default=1,
                      help="Min length (charset mode)")
    p_ks.add_argument("--max-len", dest="max_len", type=int, default=1,
                      help="Max length (charset mode)")
    p_ks.add_argument("--wordlist", help="Wordlist for count-based estimate")
    p_ks.add_argument("--rules", help="Rule file multiplier (wordlist mode)")
    p_ks.add_argument("--pps", type=float, default=1_000_000_000,
                      help="Guess rate in passwords/second (default: 1e9)")

    # ── neural ───────────────────────────────────────────────────────────
    p_nn = sub.add_parser(
        "neural",
        help="Neural char-level generation (optional [neural] extra)",
        description=(
            "Character-level neural password generation (FLA/PassGPT style).\n"
            "Requires the optional extra: pip install wordlistxpl-forge[neural].\n"
            "Supports temperature sampling, guided generation with a prefix or\n"
            "mask, Dynamic Password Guessing, and external PassGPT adapters.\n\n"
            "Examples:\n"
            "  wlf.py neural train --wordlist rockyou.txt --epochs 5\n"
            "  wlf.py --limit 100000 neural generate --temperature 0.9 -o out.lst\n"
            "  wlf.py --limit 5000 neural generate --prefix admin --mask '?u?l?l?l?d?d'\n"
            "  wlf.py --limit 100000 neural generate --adapt cracked.txt\n"
            "  wlf.py --limit 5000 neural generate --adapter passgpt --model javirandor/passgpt-10characters"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_nn.add_argument("neural_action", choices=["train", "generate"],
                      default="generate", nargs="?",
                      help="Action (default: generate)")
    p_nn.add_argument("--wordlist", nargs="+", metavar="FILE",
                      help="Training file(s) (train mode)")
    p_nn.add_argument("--model", metavar="PATH", default=".model/neural_lstm.pt",
                      help="Model path (.pt) or adapter model name")
    p_nn.add_argument("--epochs", type=int, default=5, help="Training epochs")
    p_nn.add_argument("--batch-size", dest="batch_size", type=int, default=256,
                      help="Training batch size")
    p_nn.add_argument("--embed", type=int, default=64, help="Embedding dim")
    p_nn.add_argument("--hidden", type=int, default=256, help="LSTM hidden size")
    p_nn.add_argument("--layers", type=int, default=2, help="LSTM layers")
    p_nn.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                      help="Max training lines (0 = all)")
    p_nn.add_argument("--count", type=int, default=10000,
                      help="Candidates to generate (generate mode)")
    p_nn.add_argument("--temperature", type=float, default=1.0,
                      help="Sampling temperature (default: 1.0)")
    p_nn.add_argument("--prefix", default="", help="Guided prefix")
    p_nn.add_argument("--mask", default="", help="Guided hashcat-style mask")
    p_nn.add_argument("--max-len", dest="max_len", type=int, default=32,
                      help="Max candidate length (default: 32)")
    p_nn.add_argument("--adapt", metavar="FILE",
                      help="Recovered passwords for Dynamic Password Guessing")
    p_nn.add_argument("--dpg-steps", dest="dpg_steps", type=int, default=200,
                      help="DPG adaptation steps (default: 200)")
    p_nn.add_argument("--adapter", choices=["passgpt", "hf"],
                      help="Use an external HuggingFace causal LM adapter")
    p_nn.add_argument("--no-dedupe", dest="no_dedupe", action="store_true",
                      help="Allow duplicate candidates")
    p_nn.add_argument("--seed", type=int, default=0,
                      help="RNG seed (0 = nondeterministic)")
    p_nn.add_argument("-o", "--output", help="Output file")

    # ── strength ─────────────────────────────────────────────────────────
    p_str = sub.add_parser(
        "strength",
        help="zxcvbn-style password strength and entropy estimation",
        description=(
            "Estimate password guessability with pattern matching (dictionary,\n"
            "l33t, sequences, repeats, keyboard, dates), report entropy and a\n"
            "0-4 score, and derive crack times per scenario and per hash.\n"
            "Optionally check exposure against HIBP with k-anonymity.\n\n"
            "Examples:\n"
            "  wlf.py strength 'Summer2024!'\n"
            "  wlf.py strength 'P@ssw0rd' --hibp\n"
            "  wlf.py strength --wordlist candidates.txt -o scored.tsv"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_str.add_argument("password", nargs="?", help="Password to score")
    p_str.add_argument("--wordlist", metavar="FILE",
                       help="Score every entry in a wordlist")
    p_str.add_argument("--dictionary", metavar="FILE",
                       help="Extra dictionary of known words")
    p_str.add_argument("--hibp", action="store_true",
                       help="Check HIBP via k-anonymity (single password mode)")
    p_str.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                       help="Max lines to score in wordlist mode (0 = all)")
    p_str.add_argument("-o", "--output", help="Output file")

    # ── hash-id ──────────────────────────────────────────────────────────
    p_hid = sub.add_parser(
        "hash-id",
        help="Identify likely hash algorithms",
        description=(
            "Identify likely hash algorithms for a digest, with the matching\n"
            "hashcat mode where known.\n\n"
            "Examples:\n"
            "  wlf.py hash-id 5f4dcc3b5aa765d61d8327deb882cf99\n"
            "  wlf.py hash-id --wordlist hashes.txt -o identified.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_hid.add_argument("hash", nargs="?", help="Hash string to identify")
    p_hid.add_argument("--wordlist", metavar="FILE",
                       help="Identify every hash in a file")
    p_hid.add_argument("-o", "--output", help="Output file")

    # ── hash-gen ─────────────────────────────────────────────────────────
    p_hg = sub.add_parser(
        "hash-gen",
        help="Generate hashes for a wordlist (test corpora)",
        description=(
            "Compute digests for a wordlist to build test corpora. Supports\n"
            "md5, sha1, sha224, sha256, sha384, sha512, ntlm, md4, bcrypt,\n"
            "argon2, pbkdf2 and scrypt.\n\n"
            "Examples:\n"
            "  wlf.py hash-gen --wordlist pw.txt --algo ntlm -o ntlm.txt\n"
            "  wlf.py hash-gen --wordlist pw.txt --algo md5 --format hash:plain -o pot.txt\n"
            "  wlf.py hash-gen --wordlist pw.txt --algo bcrypt --format plain:hash"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_hg.add_argument("--wordlist", required=True, metavar="FILE",
                      help="Input wordlist")
    p_hg.add_argument("--algo", default="md5",
                      choices=["md5", "sha1", "sha224", "sha256", "sha384",
                               "sha512", "ntlm", "md4", "bcrypt", "argon2",
                               "pbkdf2", "scrypt"],
                      help="Hash algorithm (default: md5)")
    p_hg.add_argument("--format", default="hash",
                      choices=["hash", "hash:plain", "plain:hash"],
                      help="Output format (default: hash)")
    p_hg.add_argument("--separator", default=":",
                      help="Field separator for combined formats (default: ':')")
    p_hg.add_argument("-o", "--output", help="Output file")

    # ── hcmask ───────────────────────────────────────────────────────────
    p_hm = sub.add_parser(
        "hcmask",
        help="Export a hashcat .hcmask from a wordlist",
        description=(
            "Analyze the mask distribution of a wordlist and export a hashcat\n"
            ".hcmask file (most frequent masks first).\n\n"
            "Examples:\n"
            "  wlf.py hcmask --wordlist leaked.txt -o masks.hcmask\n"
            "  wlf.py hcmask --wordlist leaked.txt --top 50 --min-count 5 -o top.hcmask"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_hm.add_argument("--wordlist", required=True, metavar="FILE",
                      help="Input wordlist")
    p_hm.add_argument("--top", type=int, default=0,
                      help="Keep only the top N masks (0 = all)")
    p_hm.add_argument("--min-count", dest="min_count", type=int, default=1,
                      help="Minimum occurrences to keep a mask (default: 1)")
    p_hm.add_argument("-o", "--output", metavar="FILE",
                      help="Output .hcmask file")

    # ── osint ────────────────────────────────────────────────────────────
    p_os = sub.add_parser(
        "osint",
        help="Advanced OSINT wordlists (Wayback, GitHub org, NER, LLM)",
        description=(
            "Build hyper-contextual wordlists from passive OSINT. Collects\n"
            "historical URLs from the Wayback Machine and public repository\n"
            "metadata from a GitHub organization, extracts entities, and can\n"
            "optionally enrich the result locally or with an LLM provider.\n\n"
            "Examples:\n"
            "  wlf.py osint --wayback example.com -o words.lst\n"
            "  wlf.py osint --github-org acme --lowercase -o org.lst\n"
            "  wlf.py osint --wayback example.com --github-org acme --enrich -o rich.lst\n"
            "  wlf.py osint --github-org acme --enrich --provider ollama --model llama3"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_os.add_argument("--wayback", metavar="DOMAIN",
                      help="Collect from the Wayback Machine for a domain")
    p_os.add_argument("--github-org", dest="github_org", metavar="ORG",
                      help="Collect from a GitHub organization")
    p_os.add_argument("--limit-urls", dest="limit_urls", type=int, default=5000,
                      help="Max Wayback URLs to fetch (default: 5000)")
    p_os.add_argument("--max-repos", dest="max_repos", type=int, default=200,
                      help="Max GitHub repos to inspect (default: 200)")
    p_os.add_argument("--enrich", action="store_true",
                      help="Enrich results (local heuristic or LLM provider)")
    p_os.add_argument("--provider", choices=["ollama", "openai"],
                      help="LLM provider for --enrich (optional)")
    p_os.add_argument("--model", default="llama3",
                      help="LLM model name for --provider (default: llama3)")
    p_os.add_argument("--lowercase", action="store_true",
                      help="Lowercase all output")
    p_os.add_argument("-o", "--output", help="Output file")

    # ── passphrase ───────────────────────────────────────────────────────
    p_pp = sub.add_parser(
        "passphrase",
        help="Diceware/mnemonic passphrase generation (CSPRNG)",
        description=(
            "Generate memorable passphrases from a word list using a secure\n"
            "random source. Ships a built-in list; pass a larger list (for\n"
            "example the EFF long wordlist) with --wordlist for more entropy.\n\n"
            "Examples:\n"
            "  wlf.py passphrase --count 20\n"
            "  wlf.py passphrase --words 5 --separator . --capitalize --number\n"
            "  wlf.py passphrase --wordlist eff_large_wordlist.txt --words 6 --symbol"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_pp.add_argument("--wordlist", metavar="FILE",
                      help="Custom word list (default: built-in)")
    p_pp.add_argument("--count", type=int, default=20,
                      help="Number of passphrases (default: 20)")
    p_pp.add_argument("--words", type=int, default=4,
                      help="Words per passphrase (default: 4)")
    p_pp.add_argument("--separator", default="-",
                      help="Separator between words (default: '-')")
    p_pp.add_argument("--capitalize", action="store_true",
                      help="Capitalize each word")
    p_pp.add_argument("--number", action="store_true",
                      help="Append a random digit")
    p_pp.add_argument("--symbol", action="store_true",
                      help="Append a random symbol")
    p_pp.add_argument("-o", "--output", help="Output file")

    # ── evaluate ─────────────────────────────────────────────────────────
    p_ev = sub.add_parser(
        "evaluate",
        help="Compare engines by guess-number and coverage (MAYA style)",
        description=(
            "Evaluate one or more candidate lists against a reference test set,\n"
            "reporting coverage, median guess number and cumulative hits at\n"
            "configurable cutoffs. Each candidate list represents an engine.\n\n"
            "Examples:\n"
            "  wlf.py evaluate --candidates pcfg.lst markov.lst --labels pcfg,markov --reference test.txt\n"
            "  wlf.py evaluate --candidates a.lst b.lst --reference test.txt --cutoffs 1e3,1e5,1e7"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ev.add_argument("--candidates", nargs="+", required=True, metavar="FILE",
                      help="Candidate list file(s)")
    p_ev.add_argument("--reference", required=True, metavar="FILE",
                      help="Reference (ground-truth) password file")
    p_ev.add_argument("--labels", metavar="L1,L2,...",
                      help="Comma-separated labels for the candidate lists")
    p_ev.add_argument("--cutoffs", metavar="N1,N2,...",
                      help="Guess-count cutoffs (default: 1e3,1e4,1e5,1e6,1e7)")
    p_ev.add_argument("--max-candidates", dest="max_candidates", type=int, default=0,
                      help="Max lines per candidate (0 = all)")
    p_ev.add_argument("--max-reference", dest="max_reference", type=int, default=0,
                      help="Max reference entries (0 = all)")
    p_ev.add_argument("-o", "--output", help="Save report to file")

    # ── curate ───────────────────────────────────────────────────────────
    p_cur = sub.add_parser(
        "curate",
        help="Rank lists by crack rate and merge the best (weakpass style)",
        description=(
            "Rank candidate lists by crack rate against a reference and merge\n"
            "the top performers into a single deduplicated wordlist.\n\n"
            "Examples:\n"
            "  wlf.py curate --candidates a.txt b.txt c.txt --reference test.txt --top-k 2 -o best.txt\n"
            "  wlf.py curate --candidates *.txt --reference test.txt --metric hits"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cur.add_argument("--candidates", nargs="+", required=True, metavar="FILE",
                       help="Candidate list file(s)")
    p_cur.add_argument("--reference", required=True, metavar="FILE",
                       help="Reference password file")
    p_cur.add_argument("--metric", choices=["hitrate", "hits"], default="hitrate",
                       help="Ranking metric (default: hitrate)")
    p_cur.add_argument("--top-k", dest="top_k", type=int, default=2,
                       help="Number of top lists to merge (default: 2)")
    p_cur.add_argument("--max-reference", dest="max_reference", type=int, default=0,
                       help="Max reference entries (0 = all)")
    p_cur.add_argument("-o", "--output", help="Merged output file")

    # ── v2.0 Aurora commands ──────────────────────────────────────────────
    p_pipe = sub.add_parser(
        "pipeline",
        help="Run a YAML multi-engine pipeline (async merge by score)",
        description=(
            "Compose engines via YAML DSL and emit ranked candidates.\n\n"
            "Examples:\n"
            "  wlf.py pipeline my_pipeline.yaml\n"
            "  wlf.py --limit 50000 pipeline attack.yaml -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_pipe.add_argument("pipeline_file", metavar="PIPELINE_FILE",
                        help="Path to pipeline YAML/JSON file")
    p_pipe.add_argument("-o", "--output", help="Output file (omit = stdout)")

    p_sess = sub.add_parser(
        "session",
        help="Save/list/resume generation sessions",
        description=(
            "Manage generation session checkpoints under ~/.wlf/sessions/.\n\n"
            "Examples:\n"
            "  wlf.py session list\n"
            "  wlf.py session show 1710000000-abcdef\n"
            "  wlf.py session resume 1710000000-abcdef"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_sess.add_argument(
        "session_sub", nargs="?", default="list",
        choices=["list", "show", "resume"],
        help="Sub-command (default: list)",
    )
    p_sess.add_argument("session_id", nargs="?", default=None,
                        help="Session id for show/resume")

    p_score = sub.add_parser(
        "score",
        help="Explain and score a candidate password",
        description=(
            "Heuristic structure/entropy score breakdown.\n\n"
            "Examples:\n"
            "  wlf.py score 'Admin2024!'\n"
            "  wlf.py score P@ssw0rd"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_score.add_argument("password", help="Password candidate to score")

    p_explain = sub.add_parser(
        "explain",
        help="Alias for score  - explain a candidate",
        description="Same as 'score'.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_explain.add_argument("password", help="Password candidate to explain")

    p_serve = sub.add_parser(
        "serve",
        help="REST API server (FastAPI/aiohttp) for generation streams",
        description=(
            "Start local API (AUTHORIZED USE ONLY).\n\n"
            "Examples:\n"
            "  wlf.py serve --port 8771\n"
            "  wlf.py serve --host 127.0.0.1 --port 7777 --api-key SECRET"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_serve.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8771, help="Bind port (default: 8771)")
    p_serve.add_argument("--api-key", dest="api_key", default="",
                         help="Optional API key (or env WLF_API_KEY)")

    p_brd = sub.add_parser(
        "br-deep",
        help="Brazilian deep patterns (CPF/CNPJ/CEP + PT-BR vocabulary)",
        description=(
            "Generate BR-centric candidates (synthetic structural patterns only).\n\n"
            "Examples:\n"
            "  wlf.py --limit 5000 br-deep --sector corporate -o br_corp.lst\n"
            "  wlf.py br-deep --profile-file alvo.yaml --no-cpf -o br_alvo.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_brd.add_argument("--profile-file", dest="profile_file", metavar="FILE",
                       help="JSON/YAML profile file")
    p_brd.add_argument(
        "--sector",
        choices=["generic", "corporate", "finance", "gov", "healthcare", "ecommerce"],
        default="generic",
        help="Sector prior (default: generic)",
    )
    p_brd.add_argument("--no-cpf", action="store_true", help="Skip CPF structural patterns")
    p_brd.add_argument("--no-cnpj", action="store_true", help="Skip CNPJ structural patterns")
    p_brd.add_argument("--no-cep", action="store_true", help="Skip CEP region tokens")
    p_brd.add_argument("--cep-prefix", dest="cep_prefix", metavar="XX",
                       help="Focus on CEP prefix (e.g. 01)")
    p_brd.add_argument("-o", "--output", help="Output file")

    # ── locale ───────────────────────────────────────────────────────────
    p_loc = sub.add_parser(
        "locale",
        help="Regional/cultural password patterns by locale",
        description=(
            "Generate password candidates using locale-specific cultural data\n"
            "(names, slang, sports, holidays, institutions).\n\n"
            "Available locales: en-us, en-gb, es, fr, de, pt-pt, pt-br\n\n"
            "Examples:\n"
            "  wlf.py locale --code en-us -o us_passwords.lst\n"
            "  wlf.py locale --code es --limit 10000\n"
            "  wlf.py locale --code de -o german.lst\n"
            "  wlf.py locale --list"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_loc.add_argument("--code", metavar="LOCALE",
                       help="Locale code (en-us, en-gb, es, fr, de, pt-pt, pt-br)")
    p_loc.add_argument("--list", dest="list_locales", action="store_true",
                       help="List available locale codes and exit")

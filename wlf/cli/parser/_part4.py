    p_dc.add_argument("--snmp", action="store_true",
                       help="Output SNMP community strings instead of credentials")
    p_dc.add_argument("--snmp-version", dest="snmp_version",
                       choices=["v2", "v3"], default="v2",
                       help="SNMP version (default: v2)")
    p_dc.add_argument("--list-vendors", dest="list_vendors", action="store_true",
                       help="List all vendors in the database and exit")
    p_dc.add_argument("--list-protocols", dest="list_protocols", action="store_true",
                       help="List all protocols in the database and exit")
    p_dc.add_argument(
        "--db",
        help="Path to default-creds JSON (default: generated/default-creds.json)",
    )
    p_dc.add_argument("-o", "--output", help="Output file")

    # ── isp-keygen ─────────────────────────────────────────────────────────────
    p_isp = sub.add_parser(
        "isp-keygen",
        help="ISP default WiFi password keyspace generator",
        description=(
            "Generate vendor-specific WiFi password wordlists based on known\n"
            "ISP default password patterns.\n\n"
            "Xfinity/Comcast pattern: word5 + 4digit + word6\n"
            "  e.g., fever7538harbor (15 chars, lowercase + digits)\n\n"
            "Keyspace: 686 × 10,000 × 685 = ~4.7 billion per direction.\n\n"
            "Examples:\n"
            "  wlf.py isp-keygen --list-isps\n"
            "  wlf.py isp-keygen --isp xfinity_comcast --estimate\n"
            "  wlf.py isp-keygen --isp xfinity_comcast --limit 1000 -o sample.lst\n"
            "  wlf.py isp-keygen --isp xfinity_comcast --direction both -o full.lst\n"
            "  wlf.py isp-keygen --isp xfinity_comcast --direction reverse --limit 500000 -o rev.lst\n"
            "  wlf.py isp-keygen --isp xfinity_comcast --word5-file custom5.txt -o custom.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_isp.add_argument("--isp", default="xfinity_comcast",
                        help="ISP pattern name (default: xfinity_comcast)")
    p_isp.add_argument("--direction", choices=["forward", "reverse", "both"],
                        default="forward",
                        help="Generation direction (default: forward)")
    p_isp.add_argument("--limit", type=int, default=0,
                        help="Max entries to generate (0 = all)")
    p_isp.add_argument("--estimate", action="store_true",
                        help="Show keyspace estimate only, don't generate")
    p_isp.add_argument("--word5-file", dest="word5_file",
                        help="Custom 5-letter word file (overrides built-in)")
    p_isp.add_argument("--word6-file", dest="word6_file",
                        help="Custom 6-letter word file (overrides built-in)")
    p_isp.add_argument("--list-isps", dest="list_isps", action="store_true",
                        help="List available ISP patterns and exit")
    p_isp.add_argument("-o", "--output", help="Output file")

    # ── sysinfo ───────────────────────────────────────────────────────────────
    p_si = sub.add_parser(
        "sysinfo",
        help="Show hardware profile, compute backend and thread status",
        description=(
            "Display detected CPU, RAM, GPU and compute backend.\n"
            "Shows current --threads and --compute settings.\n\n"
            "Examples:\n"
            "  wlf.py sysinfo\n"
            "  wlf.py sysinfo --crc32-stress 150000\n"
            "  wlf.py --compute gpu sysinfo\n"
            "  wlf.py --threads 20 sysinfo"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_si.add_argument("--crc32-stress", dest="crc32_stress", type=int, default=0, metavar="N",
                       help="Run CRC32 dedup stress test with N synthetic lines")

    # ── corp-prefixes ─────────────────────────────────────────────────────────
    p_cp = sub.add_parser(
        "corp-prefixes",
        help="Generate username variations with corporate department/role prefixes",
        description=(
            "Generate username variations with department, role, and functional prefixes.\n\n"
            "All patterns loaded from data/corp_prefix_patterns.json - no hardcoded data.\n"
            "No real company names ever stored or generated.\n\n"
            "Prefix categories:\n"
            "  department  - ti, helpdesk, adm, rh, fin, seg, dev, redes, ...\n"
            "  role        - svc, admin, ger, dir, analista, trainee, ...\n"
            "  contractor  - ext, externo, terceiro, vendor, pj, ...\n"
            "  temp        - temp, tmp, provisorio, ...\n"
            "  generic     - user, usr, account, login, ...\n\n"
            "Examples:\n"
            "  wlf.py corp-prefixes --names 'PessoaX' --domain acme.example\n"
            "  wlf.py corp-prefixes --names 'PessoaX' --prefixes svc,adm --separators .\n"
            "  wlf.py corp-prefixes --names 'PessoaX' --categories department,role\n"
            "  wlf.py corp-prefixes --names 'PessoaX' --sector judicial\n"
            "  wlf.py corp-prefixes --list-prefixes\n"
            "  wlf.py corp-prefixes --file employees.txt --domain corp.example -o prefixed.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cp.add_argument("--names", metavar="NAME1,NAME2", help="Comma-separated full names")
    p_cp.add_argument("--file", metavar="FILE", help="File with employee names")
    p_cp.add_argument("--domain", default="", help="Company domain for @domain suffix")
    p_cp.add_argument("--no-at", dest="no_at", action="store_true",
                       help="Omit @domain suffix from output")
    p_cp.add_argument(
        "--prefixes", metavar="pfx1,pfx2",
        help="Explicit prefix list (e.g. svc,adm,ti). Overrides --categories.",
    )
    p_cp.add_argument(
        "--categories", metavar="cat1,cat2",
        help="Prefix categories to include: department, role, contractor, temp, generic",
    )
    p_cp.add_argument(
        "--sector", metavar="SECTOR",
        help=(
            "Force sector label for prefix selection "
            "(energia_utilities, judicial, financas, saude, governo, generic, ...)"
        ),
    )
    p_cp.add_argument(
        "--separators", metavar="SEP",
        default=".",
        help="Separator(s) between prefix and name parts (default: '.')",
    )
    p_cp.add_argument(
        "--no-numeric", dest="no_numeric", action="store_true",
        help="Skip numeric suffix variants",
    )
    p_cp.add_argument(
        "--list-prefixes", dest="list_prefixes", action="store_true",
        help="List all available prefix groups and exit",
    )
    p_cp.add_argument(
        "--config", metavar="FILE",
        help="Custom prefix patterns JSON file (default: data/corp_prefix_patterns.json)",
    )
    p_cp.add_argument("-o", "--output", help="Output file")

    # ── train ─────────────────────────────────────────────────────────────────
    p_tr = sub.add_parser(
        "train",
        help="Train ML pattern model from AD exports, wordlists, and username lists",
        description=(
            "Train the statistical pattern model for corporate credential generation.\n\n"
            "Privacy: only structural patterns are extracted - no raw usernames,\n"
            "passwords, company names, or personal data are ever stored.\n\n"
            "Examples:\n"
            "  wlf.py train --csv export.csv --auto -o .model/pattern_model.json\n"
            "  wlf.py train --auto\n"
            "  wlf.py train --seclists\n"
            "  wlf.py train --seclists /path/to/SecLists --seclists-categories password frequency\n"
            "  wlf.py train --auto --seclists\n"
            "  wlf.py train --csv users.csv --wordlist passwords.lst --usernames users.lst\n"
            "  wlf.py train --csv export.csv --uid-col samaccountname --mail-col mail"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_tr.add_argument(
        "--csv", metavar="FILE", action="append", default=[],
        help="AD export CSV file(s) to train from (can repeat for multiple files)",
    )
    p_tr.add_argument(
        "--wordlist", metavar="FILE", action="append", default=[],
        help="Password wordlist file(s) to train from",
    )
    p_tr.add_argument(
        "--usernames", metavar="FILE", action="append", default=[],
        help="Username list file(s) to train from",
    )
    p_tr.add_argument(
        "--auto", action="store_true",
        help="Auto-discover and train from local generated/ corpora (passwords.lst, default-creds.lst, users.lst)",
    )
    p_tr.add_argument(
        "--uid-col", dest="uid_col", default="userid",
        help="CSV column name for username/samaccountname (default: userid)",
    )
    p_tr.add_argument(
        "--eid-col", dest="eid_col", default="employeeid",
        help="CSV column name for employee ID (default: employeeid)",
    )
    p_tr.add_argument(
        "--mail-col", dest="mail_col", default="workemail",
        help="CSV column name for work email (default: workemail)",
    )
    p_tr.add_argument(
        "--max-rows", dest="max_rows", type=int, default=0,
        help="Max CSV rows to process (0 = all)",
    )
    p_tr.add_argument(
        "--max-lines", dest="max_lines", type=int, default=500_000,
        help="Max lines to read from wordlists (default: 500000)",
    )
    p_tr.add_argument(
        "--seclists", metavar="PATH", nargs="?", const="auto",
        help="Train from SecLists corpus (auto-discover or specify path)",
    )
    p_tr.add_argument(
        "--seclists-categories", dest="seclists_categories",
        metavar="CAT", nargs="+", default=None,
        choices=["password", "username", "frequency"],
        help="SecLists categories to train: password username frequency (default: all)",
    )
    p_tr.add_argument(
        "-o", "--output", metavar="FILE",
        help="Output model file (default: .model/pattern_model.json)",
    )

    # ── password-dna ───────────────────────────────────────────────────────
    p_dna = sub.add_parser(
        "password-dna",
        help="Analyze password patterns and generate behavioral variants",
        description=(
            "Analyze 1-10 known passwords from a target to extract behavioral DNA:\n"
            "structural patterns, word banks, separator habits, number placement,\n"
            "capitalization style, and leet preferences. Then generate a wordlist\n"
            "of candidates matching the same behavioral profile.\n\n"
            "Minimum: 1 password. Ideal: 3+ passwords. Maximum: 10.\n\n"
            "Examples:\n"
            '  wlf.py password-dna "Empresa@2024" "empresa#2025" "Empresa!123"\n'
            '  wlf.py password-dna --file known_passwords.txt --depth deep -o candidates.lst\n'
            '  wlf.py password-dna "P@ssw0rd1" --depth quick --show-dna\n'
            '  wlf.py password-dna "PessoaX99" "pessoax.corpx@2024" "CorpX#pessoax1"'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dna.add_argument("passwords", nargs="*",
                        help="Known target passwords (1-10)")
    p_dna.add_argument("--file", metavar="FILE",
                        help="File with known passwords (one per line, max 10)")
    p_dna.add_argument("--depth", choices=["quick", "normal", "deep"],
                        default="normal",
                        help="Generation depth: quick (~2K), normal (~15K), deep (~100K+)")
    p_dna.add_argument("--show-dna", dest="show_dna", action="store_true",
                        help="Print the extracted DNA profile before generating")
    p_dna.add_argument("-o", "--output", help="Output file")

    # ── dna-extract ────────────────────────────────────────────────────────
    p_dx = sub.add_parser(
        "dna-extract",
        help="Extract password DNA profile and hashcat masks (no full generation)",
        description=(
            "Analyze known passwords and print DNA + structure/hashcat masks.\n"
            "Does not explode the full candidate space (use password-dna for that).\n\n"
            "Examples:\n"
            '  wlf.py dna-extract "BrandX#OzZY25" "_BR4NDX@2026#Pitty"\n'
            "  wlf.py dna-extract --file known.txt -o dna.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dx.add_argument("passwords", nargs="*", help="Known passwords (1-10)")
    p_dx.add_argument("--file", metavar="FILE", help="File with known passwords")
    p_dx.add_argument("-o", "--output", help="Output report file")

    # ── cover ──────────────────────────────────────────────────────────────
    p_cv = sub.add_parser(
        "cover",
        help="Sample local users/passwords corpus and report structural coverage",
        description=(
            "Memory-safe reservoir sample of generated/*.lst.\n"
            "Reports structure/mask families and which engines can cover them.\n\n"
            "Examples:\n"
            "  wlf.py cover\n"
            "  wlf.py cover --sample 2000 --kind passwords -o cover.tsv\n"
            "  wlf.py cover --corpus generated/users.lst --kind users"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cv.add_argument("--corpus", metavar="FILE", help="Corpus path (default: generated/passwords.lst)")
    p_cv.add_argument("--kind", choices=["passwords", "users"], default="passwords")
    p_cv.add_argument("--sample", type=int, default=1000, help="Reservoir sample size")
    p_cv.add_argument("--seed", type=int, default=42)
    p_cv.add_argument("-o", "--output", help="Optional TSV report")

    # ── replay ─────────────────────────────────────────────────────────────
    p_rp = sub.add_parser(
        "replay",
        help="Replay generated candidates vs bloom sample of local corpus",
        description=(
            "Generate (or load) candidates and measure hit-rate against a\n"
            "bloom filter built from a sample of generated/*.lst.\n"
            "Does not claim 100%% corpus coverage.\n\n"
            "Examples:\n"
            "  wlf.py replay\n"
            "  wlf.py replay --company BrandX --pet OzZY --year 2026 --tag CS\n"
            "  wlf.py replay --candidates my.lst --bloom-sample 100000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_rp.add_argument("--corpus", metavar="FILE", help="Corpus path")
    p_rp.add_argument("--kind", choices=["passwords", "users"], default="passwords")
    p_rp.add_argument("--candidates", metavar="FILE", help="Candidate list to score")
    p_rp.add_argument("--bloom-sample", dest="bloom_sample", type=int, default=200_000)
    p_rp.add_argument("--company", default="BrandX")
    p_rp.add_argument("--pet", default="OzZY")
    p_rp.add_argument("--year", default="2026")
    p_rp.add_argument("--tag", default="CS")
    p_rp.add_argument("--seeds", nargs="*", help="Optional password seeds for DNA expansion")
    p_rp.add_argument("--depth", choices=["quick", "normal", "deep"], default="quick")
    p_rp.add_argument("-o", "--output", help="Write hit examples")

    # ── emit (ordered stream) ─────────────────────────────────────────────
    p_em = sub.add_parser(
        "emit",
        help="Stream ordered candidates from an engine (stdout by default)",
        description=(
            "Pipe ranked candidates without materializing a giant set.\n\n"
            "Examples:\n"
            "  wlf.py --stream emit --engine markov --limit 10000\n"
            "  wlf.py emit --engine pcfg --model .model/pcfg_grammar.json -o out.lst\n"
            "  wlf.py emit --engine mask --mask '?l?l?d?d' --limit 50000\n"
            "  wlf.py emit --engine semantic --profile-file target.yaml --limit 20000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_em.add_argument(
        "--engine", choices=["markov", "pcfg", "mask", "semantic"], default="pcfg",
        help="Generator engine (default: pcfg)",
    )
    p_em.add_argument("--model", metavar="FILE", help="Markov/PCFG model path")
    p_em.add_argument("--mask", metavar="MASK", help="Hashcat-style mask (engine=mask)")
    p_em.add_argument("--profile-file", dest="profile_file", metavar="FILE",
                      help="Profile YAML (engine=semantic)")
    p_em.add_argument("--min-len", dest="min_len", type=int, default=4)
    p_em.add_argument("--max-len", dest="max_len", type=int, default=16)
    p_em.add_argument("--limit", type=int, default=0, help="Max candidates (0 = engine default)")
    p_em.add_argument("--beam-width", dest="beam_width", type=int, default=0,
                      help="Heap/beam cap for markov/pcfg")
    p_em.add_argument("--top-structures", dest="top_structures", type=int, default=50)
    p_em.add_argument("--top-terminals", dest="top_terminals", type=int, default=80)
    p_em.add_argument("--zipf-s", dest="zipf_s", type=float, default=0.0,
                      help="Optional Zipf reweight on emission rank")
    p_em.add_argument("-o", "--output", help="Output file (omit = stdout)")

    # ── maskgen ───────────────────────────────────────────────────────────
    p_mg = sub.add_parser(
        "maskgen",
        help="Chunked hashcat-style mask cartesian (GPU-aware batching)",
        description=(
            "Expand a mask keyspace in ordered chunks under ResourceGovernor.\n\n"
            "Examples:\n"
            "  wlf.py --compute gpu maskgen --mask '?l?l?d?d' --limit 100000\n"
            "  wlf.py maskgen --mask '?u?l?l?l?d?d' --chunk 65536 -o masks.lst\n"
            "  wlf.py maskgen --mask '?1?1?d' --custom-charset1 'ab@#' --force"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_mg.add_argument("--mask", metavar="MASK", required=True,
                      help="Hashcat-style mask (?l ?u ?d ?s ?a ?h ?H ?1)")
    p_mg.add_argument("--custom-charset1", dest="custom_charset1", metavar="CHARS",
                      help="Charset for ?1")
    p_mg.add_argument("--chunk", type=int, default=65536, help="Batch size hint")
    p_mg.add_argument("--limit", type=int, default=0, help="Max candidates (0 = full/cap)")
    p_mg.add_argument("--force", action="store_true",
                      help="Allow keyspaces >5M without --limit")
    p_mg.add_argument("-o", "--output", help="Output file (omit = stdout)")

    # ── strategy (PBMP-lite) ──────────────────────────────────────────────
    p_st = sub.add_parser(
        "strategy",
        help="Plan mutation engines from a profile (PBMP-lite)",
        description=(
            "Print a weighted engine plan; optionally run top strategies.\n\n"
            "Examples:\n"
            "  wlf.py strategy --profile-file target.yaml\n"
            "  wlf.py strategy --profile-file target.yaml --run -o plan.txt\n"
            "  wlf.py strategy --profile-file target.yaml --run --output-wordlist cands.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_st.add_argument("--profile-file", dest="profile_file", metavar="FILE", required=True)
    p_st.add_argument("--run", action="store_true", help="Execute top engines under governor")
    p_st.add_argument("-o", "--output", help="Write plan text")
    p_st.add_argument("--output-wordlist", dest="output_wordlist", metavar="FILE",
                      help="Candidate output when --run")

    # ── bandit ────────────────────────────────────────────────────────────
    p_bd = sub.add_parser(
        "bandit",
        help="Multi-armed bandit router over generation engines (UCB1)",
        description=(
            "Sample arms (markov/pcfg/prince/rules/pattern) with proxy rewards.\n\n"
            "Examples:\n"
            "  wlf.py bandit --rounds 8 --seeds BrandX OzZY 2026\n"
            "  wlf.py bandit --rounds 5 --ucb-c 1.2"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_bd.add_argument("--rounds", type=int, default=5, help="Bandit rounds (default: 5)")
    p_bd.add_argument("--seeds", nargs="*", help="Seed tokens for proxy reward")
    p_bd.add_argument("--ucb-c", dest="ucb_c", type=float, default=1.414,
                      help="UCB1 exploration constant")

    # ── combiner ──────────────────────────────────────────────────────────
    p_cb = sub.add_parser(
        "combiner",
        help="Keyword combiner (intelligence-wordlist-generator style)",
        description=(
            "Generate wordlists from keyword permutations with connectors.\n\n"
            "Examples:\n"
            "  wlf.py combiner admin password secret\n"
            "  wlf.py combiner admin test --connectors ',-,_,.,EMPTY' --leet --reverse\n"
            "  wlf.py combiner --keywords-file keywords.txt --depth 3 --abbreviation\n"
            "  wlf.py combiner brandx corp 2026 --tails '!,@,#,123' -o wordlist.lst\n"
            "  wlf.py combiner nerd trilha --titlecase --tails '0724' --affix-specials '!,@,#'\n"
            "  wlf.py combiner nerd trilha --link-lang pt --tails '0724!'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cb.add_argument("keywords", nargs="*", help="Keywords to combine")
    p_cb.add_argument("--keywords-file", dest="keywords_file", metavar="FILE",
                       help="File with one keyword per line")
    p_cb.add_argument("--connectors", metavar="LIST",
                       help="Comma-separated connectors (use EMPTY for no separator, default: EMPTY,-,_,.,@,#)")
    p_cb.add_argument("--tails", metavar="LIST",
                       help="Comma-separated numeric/special tails to append")
    p_cb.add_argument("--depth", type=int, default=0,
                       help="Max permutation depth (0 = all, default: 0)")
    p_cb.add_argument("--abbreviation", action="store_true",
                       help="Generate abbreviation variants")
    p_cb.add_argument("--reverse", action="store_true",
                       help="Generate reversed variants")
    p_cb.add_argument("--leet", action="store_true",
                       help="Generate leet speak variants")
    p_cb.add_argument("--lowercase", action="store_true",
                       help="Add lowercase duplicates")
    p_cb.add_argument("--titlecase", action="store_true",
                       help="Capitalize each component before joining (CamelCase, e.g. NerdTrilha)")
    p_cb.add_argument("--affix-specials", dest="affix_specials", metavar="LIST",
                       help="Special chars wrapped around numeric tails for composite affixes "
                            "(e.g. '!,@,#' yields word@0724, word0724!, word@0724!)")
    p_cb.add_argument("--link-lang", dest="link_lang", metavar="LANGS",
                       help="Add linguistic linking words as connectors for the given languages "
                            "(comma-separated codes/aliases or 'all': pt,en,es,fr,it,de). Prompts for confirmation")
    p_cb.add_argument("--link-words", dest="link_words", metavar="LIST",
                       help="Explicit extra linking words to use as connectors (comma-separated)")
    p_cb.add_argument("--assume-yes", dest="assume_yes", action="store_true",
                       help="Skip the linking-words confirmation prompt (for automation)")
    p_cb.add_argument("--theme", metavar="NAME",
                       help="Inject keywords from a theme pack (starwars, marvel, gaming, sports, anime, music, hacking, ctf)")
    p_cb.add_argument("--nouns", metavar="LANG",
                       help="Inject nouns from built-in dictionary (en, pt, all)")
    p_cb.add_argument("--fixed-suffix", dest="fixed_suffix", metavar="STR",
                       help="Append fixed string to each keyword (bypasses permutation)")
    p_cb.add_argument("--fixed-prefix", dest="fixed_prefix", metavar="STR",
                       help="Prepend fixed string to each keyword (bypasses permutation)")
    p_cb.add_argument("--min-len", dest="min_len", type=int, default=1,
                       help="Minimum output length (default: 1)")
    p_cb.add_argument("--max-len", dest="max_len", type=int, default=64,
                       help="Maximum output length (default: 64)")
    p_cb.add_argument("-o", "--output", help="Output file")

    # ── pcfg ─────────────────────────────────────────────────────────────
    p_pcfg = sub.add_parser(
        "pcfg",
        help="PCFG probabilistic grammar - train or generate",
        description=(
            "Probabilistic Context-Free Grammar engine (Weir et al.).\n"
            "Train a grammar from password corpora, then generate candidates\n"
            "in approximate probability order (most likely first).\n\n"
            "Examples:\n"
            "  wlf.py pcfg train --wordlist rockyou.txt\n"
            "  wlf.py pcfg generate -o candidates.lst\n"
            "  wlf.py pcfg generate --top-structures 50 --top-terminals 100 --limit 1000000\n"
            "  wlf.py pcfg generate --model .model/pcfg_grammar.json --min-len 8"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_pcfg.add_argument("pcfg_action", choices=["train", "generate"], default="generate",
                         nargs="?", help="Action: train or generate (default: generate)")
    p_pcfg.add_argument("--wordlist", nargs="+", metavar="FILE",
                         help="Training file(s) - one password per line")
    p_pcfg.add_argument("--model", metavar="FILE", default=".model/pcfg_grammar.json",
                         help="Grammar model file (default: .model/pcfg_grammar.json)")
    p_pcfg.add_argument("--model-output", dest="model_output", metavar="FILE",
                         help="Output path for trained model")
    p_pcfg.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                         help="Max training lines (0 = unlimited)")
    p_pcfg.add_argument("--top-structures", dest="top_structures", type=int, default=0,
                         help="Limit to top N structures (0 = all)")
    p_pcfg.add_argument("--top-terminals", dest="top_terminals", type=int, default=0,
                         help="Limit terminals per class to top N (0 = all)")
    p_pcfg.add_argument("--min-len", dest="min_len", type=int, default=1,
                         help="Min password length (default: 1)")
    p_pcfg.add_argument("--max-len", dest="max_len", type=int, default=64,
                         help="Max password length (default: 64)")
    p_pcfg.add_argument("--limit", type=int, default=0,
                         help="Max candidates to generate (0 = unlimited)")
    p_pcfg.add_argument("--beam-width", dest="beam_width", type=int, default=250_000,
                         help="Max pending heap nodes (RAM guard, default: 250000)")
    p_pcfg.add_argument("--zipf-s", dest="zipf_s", type=float, default=0.0,
                         help="Zipf reweight exponent s (0 = off)")
    p_pcfg.add_argument("-o", "--output", help="Output file")

    # ── markov ───────────────────────────────────────────────────────────
    p_mk = sub.add_parser(
        "markov",
        help="OMEN-style positional Markov generator - train or generate",
        description=(
            "Positional Markov chain password generator (OMEN-style).\n"
            "Learns character transition probabilities per position and\n"
            "generates candidates in ascending cost order.\n\n"
            "Examples:\n"
            "  wlf.py markov train --wordlist rockyou.txt --order 4\n"
            "  wlf.py markov generate --limit 500000\n"

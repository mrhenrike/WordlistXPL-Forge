            "  wlf.py markov generate --min-len 8 --max-len 12 --max-cost 30"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_mk.add_argument("markov_action", choices=["train", "generate"], default="generate",
                       nargs="?", help="Action: train or generate (default: generate)")
    p_mk.add_argument("--wordlist", nargs="+", metavar="FILE",
                       help="Training file(s)")
    p_mk.add_argument("--model", metavar="FILE", default=".model/markov_model.json",
                       help="Model file (default: .model/markov_model.json)")
    p_mk.add_argument("--model-output", dest="model_output", metavar="FILE",
                       help="Output path for trained model")
    p_mk.add_argument("--order", type=int, default=3,
                       help="N-gram order (default: 3)")
    p_mk.add_argument("--smoothing", type=float, default=0.01,
                       help="Laplace smoothing alpha for unseen n-grams (default: 0.01)")
    p_mk.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                       help="Max training lines (0 = unlimited)")
    p_mk.add_argument("--max-cost", dest="max_cost", type=int, default=0,
                       help="Max total cost threshold (0 = no limit)")
    p_mk.add_argument("--min-len", dest="min_len", type=int, default=4,
                       help="Min password length (default: 4)")
    p_mk.add_argument("--max-len", dest="max_len", type=int, default=16,
                       help="Max password length (default: 16)")
    p_mk.add_argument("--limit", type=int, default=0,
                       help="Max candidates (0 = unlimited)")
    p_mk.add_argument("--beam-width", dest="beam_width", type=int, default=100_000,
                       help="Max live heap nodes (RAM guard, default: 100000)")
    p_mk.add_argument("-o", "--output", help="Output file")

    # ── kwalk ────────────────────────────────────────────────────────────
    p_kw = sub.add_parser(
        "kwalk",
        help="Keyboard walk password generator (kwprocessor-style)",
        description=(
            "Generate passwords based on physical keyboard adjacency walks.\n"
            "Supports QWERTY, AZERTY, QWERTZ, ABNT2, Dvorak, Colemak and numpad.\n\n"
            "Examples:\n"
            "  wlf.py kwalk --min-len 6 --max-len 10\n"
            "  wlf.py kwalk --layout azerty --no-shift\n"
            "  wlf.py kwalk --layout all\n"
            "  wlf.py kwalk --layout abnt2,qwerty --start-chars qaz1\n"
            "  wlf.py kwalk --list-layouts"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_kw.add_argument("--layout", default="qwerty",
                       help="Layout name(s), comma-separated, or 'all' (default: qwerty)")
    p_kw.add_argument("--min-len", dest="min_len", type=int, default=4,
                       help="Min walk length (default: 4)")
    p_kw.add_argument("--max-len", dest="max_len", type=int, default=10,
                       help="Max walk length (default: 10)")
    p_kw.add_argument("--max-changes", dest="max_changes", type=int, default=3,
                       help="Max direction changes per walk (default: 3)")
    p_kw.add_argument("--directions", metavar="LIST",
                       help="Comma-separated directions: N,S,E,W,NE,NW,SE,SW")
    p_kw.add_argument("--no-shift", dest="no_shift", action="store_true",
                       help="Exclude shifted layer (uppercase/symbols)")
    p_kw.add_argument("--start-chars", dest="start_chars", metavar="CHARS",
                       help="Restrict starting characters")
    p_kw.add_argument("--route", metavar="START:DIRS",
                       help="Explicit walk route, e.g. q:3467 or q,3467 (0-7 = N..NW)")
    p_kw.add_argument("--route-file", dest="route_file", metavar="FILE",
                       help="Route file: one 'start dirs' per line (kwprocessor-style)")
    p_kw.add_argument("--list-layouts", dest="list_layouts", action="store_true",
                       help="List available keyboard layouts")
    p_kw.add_argument("--limit", type=int, default=0,
                       help="Max candidates (0 = unlimited)")
    p_kw.add_argument("-o", "--output", help="Output file")

    # ── phonetic ────────────────────────────────────────────────────────
    p_ph = sub.add_parser(
        "phonetic",
        help="Phonetic similarity password generator (Soundex/Metaphone)",
        description=(
            "Generate passwords based on phonetic similarity to seed words.\n"
            "Uses Soundex, Metaphone and visual substitutions.\n\n"
            "Examples:\n"
            "  wlf.py phonetic --seed password,company\n"
            "  wlf.py phonetic --seed john --min-len 6 --limit 5000\n"
            "  wlf.py phonetic --profile target.json\n"
            "  wlf.py phonetic --seed admin --analyze"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ph.add_argument("--seed", metavar="WORDS",
                       help="Comma-separated seed words")
    p_ph.add_argument("--wordlist", metavar="FILE",
                       help="File with seed words (one per line)")
    p_ph.add_argument("--profile", metavar="FILE",
                       help="JSON profile with target info (name, keywords, pets)")
    p_ph.add_argument("--min-len", dest="min_len", type=int, default=4,
                       help="Min candidate length (default: 4)")
    p_ph.add_argument("--max-len", dest="max_len", type=int, default=32,
                       help="Max candidate length (default: 32)")
    p_ph.add_argument("--max-subs", dest="max_subs", type=int, default=30,
                       help="Max substitution variants per word (default: 30)")
    p_ph.add_argument("--analyze", action="store_true",
                       help="Show Soundex/Metaphone grouping analysis instead of generating")
    p_ph.add_argument("--limit", type=int, default=10000,
                       help="Max candidates (default: 10000)")
    p_ph.add_argument("-o", "--output", help="Output file")

    # ── rule-mine ────────────────────────────────────────────────────────
    p_rm = sub.add_parser(
        "rule-mine",
        help="Mine hashcat rules from plaintext passwords (inverse of rulegen)",
        description=(
            "Given a wordlist of cracked passwords, automatically derive the\n"
            "hashcat rules that transform base words into those passwords.\n\n"
            "Examples:\n"
            "  wlf.py rule-mine --wordlist cracked.txt -o mined.rule\n"
            "  wlf.py rule-mine --wordlist cracked.txt --dictionary english.txt\n"
            "  wlf.py rule-mine --wordlist passwords.lst --min-confidence 3"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_rm.add_argument("--wordlist", required=True, metavar="FILE",
                       help="Plaintext password file to analyze")
    p_rm.add_argument("--dictionary", metavar="FILE",
                       help="Base word dictionary for matching (optional)")
    p_rm.add_argument("--max-rules", dest="max_rules", type=int, default=200,
                       help="Max rules to output (default: 200)")
    p_rm.add_argument("--min-confidence", dest="min_confidence", type=int, default=2,
                       help="Min pair count for a rule to be reported (default: 2)")
    p_rm.add_argument("-o", "--output", help="Output .rule file")

    # ── finetune-data ───────────────────────────────────────────────────
    p_ft = sub.add_parser(
        "finetune-data",
        help="Generate LLM fine-tuning datasets from wordlists (LoRA/QLoRA)",
        description=(
            "Convert password wordlists into instruction-tuning JSONL datasets\n"
            "suitable for LoRA/QLoRA fine-tuning of language models.\n\n"
            "Supported formats: alpaca, sharegpt, completion.\n"
            "Augmentation: partial masking, prefix completion, style transfer.\n\n"
            "Examples:\n"
            "  wlf.py finetune-data --wordlist rockyou.txt -o train.jsonl\n"
            "  wlf.py finetune-data --wordlist leaked.txt --format sharegpt --no-augment\n"
            "  wlf.py finetune-data --wordlist cracked.txt --max-samples 50000 --seed 123"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ft.add_argument("--wordlist", required=True, metavar="FILE",
                       help="Password wordlist to convert")
    p_ft.add_argument("--format", choices=["alpaca", "sharegpt", "completion"],
                       default="alpaca", help="Output format (default: alpaca)")
    p_ft.add_argument("--no-augment", dest="no_augment", action="store_true",
                       help="Disable data augmentation (prefix, mask, style)")
    p_ft.add_argument("--max-samples", dest="max_samples", type=int, default=0,
                       help="Max samples to generate (0 = all, default: 0)")
    p_ft.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility (default: 42)")
    p_ft.add_argument("-o", "--output", help="Output JSONL file")

    # ── nflow ────────────────────────────────────────────────────────────
    p_nf = sub.add_parser(
        "nflow",
        help="Generate passwords via normalizing flow (RealNVP)",
        description=(
            "Learn password distributions with a RealNVP normalizing flow\n"
            "and generate new candidates by sampling from the latent space.\n"
            "Supports interpolation between passwords in latent space.\n\n"
            "Examples:\n"
            "  wlf.py nflow --wordlist rockyou.txt -o generated.txt --limit 5000\n"
            "  wlf.py nflow --wordlist leaked.txt --epochs 20 --temperature 0.8\n"
            "  wlf.py nflow --wordlist pw.txt --interpolate-a Password1 --interpolate-b Summer2024"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_nf.add_argument("--wordlist", required=True, metavar="FILE",
                       help="Training wordlist")
    p_nf.add_argument("--limit", type=int, default=1000,
                       help="Number of passwords to generate (default: 1000)")
    p_nf.add_argument("--max-len", dest="max_len", type=int, default=16,
                       help="Max password length for encoding (default: 16)")
    p_nf.add_argument("--layers", type=int, default=4,
                       help="Number of coupling layers (default: 4)")
    p_nf.add_argument("--epochs", type=int, default=10,
                       help="Training epochs (default: 10)")
    p_nf.add_argument("--lr", type=float, default=0.01,
                       help="Learning rate (default: 0.01)")
    p_nf.add_argument("--temperature", type=float, default=1.0,
                       help="Sampling temperature (default: 1.0)")
    p_nf.add_argument("--interpolate-a", dest="interpolate_a", metavar="PW",
                       help="First password for interpolation")
    p_nf.add_argument("--interpolate-b", dest="interpolate_b", metavar="PW",
                       help="Second password for interpolation")
    p_nf.add_argument("--interpolate-steps", dest="interpolate_steps", type=int,
                       default=10, help="Interpolation steps (default: 10)")
    p_nf.add_argument("-o", "--output", help="Output file")

    # ── combo ────────────────────────────────────────────────────────────
    p_cb = sub.add_parser(
        "combo",
        help="Generate credential combos (user:password pairs)",
        description=(
            "Generate user:password combinations for credential testing\n"
            "from username and password lists using multiple strategies.\n\n"
            "Strategies: cartesian, user_as_pass, email_prefix, smart, reverse.\n\n"
            "Examples:\n"
            "  wlf.py combo --userlist users.txt --passlist passwords.txt -o combos.txt\n"
            "  wlf.py combo --userlist emails.txt --strategy email_prefix\n"
            "  wlf.py combo --userlist users.txt --strategy user_as_pass --format json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cb.add_argument("--userlist", required=True, metavar="FILE",
                       help="Username/email list file")
    p_cb.add_argument("--passlist", metavar="FILE",
                       help="Password list file (optional for some strategies)")
    p_cb.add_argument("--strategy", choices=["cartesian", "user_as_pass", "email_prefix",
                       "smart", "reverse"], default="smart",
                       help="Pairing strategy (default: smart)")
    p_cb.add_argument("--format", choices=["colon", "tab", "json"], default="colon",
                       help="Output format (default: colon)")
    p_cb.add_argument("--no-dedup", dest="no_dedup", action="store_true",
                       help="Disable deduplication of output combos")
    p_cb.add_argument("--limit", type=int, default=0,
                       help="Max combos to generate (0 = all)")
    p_cb.add_argument("-o", "--output", help="Output file")

    # ── corp-conv ────────────────────────────────────────────────────────
    p_cc = sub.add_parser(
        "corp-conv",
        help="Generate passwords from corporate naming conventions",
        description=(
            "Generate passwords following common enterprise conventions:\n"
            "  verb+sep+corp+digits, season+year+symbol, dept+project+digits,\n"
            "  corp+year+symbol, month+year+corp.\n\n"
            "Examples:\n"
            "  wlf.py corp-conv --corp-names Acme XPTO -o corp_wl.txt\n"
            "  wlf.py corp-conv --corp-names Globo --years 2024 2025\n"
            "  wlf.py corp-conv --corp-names Corp --patterns verb_sep_corp season_year"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cc.add_argument("--corp-names", dest="corp_names", nargs="+", required=True,
                       metavar="NAME", help="Company/brand names to use")
    p_cc.add_argument("--years", nargs="+", metavar="YEAR",
                       help="Years to include (default: 2023-2026)")
    p_cc.add_argument("--patterns", nargs="+", metavar="PATTERN",
                       choices=["verb_sep_corp", "season_year", "dept_project",
                                "corp_year", "month_year"],
                       help="Specific patterns to use (default: all)")
    p_cc.add_argument("--limit", type=int, default=0,
                       help="Max candidates (0 = all)")
    p_cc.add_argument("-o", "--output", help="Output file")

    # ── rulegen ──────────────────────────────────────────────────────────
    p_rg = sub.add_parser(
        "rulegen",
        help="Auto-generate hashcat .rule files from password analysis",
        description=(
            "Analyze real passwords to discover transformation rules\n"
            "and generate hashcat-compatible .rule files.\n\n"
            "Examples:\n"
            "  wlf.py rulegen --wordlist leaked.txt -o rules.rule\n"
            "  wlf.py rulegen --wordlist passwords.lst --dictionary english.txt --top-rules 200\n"
            "  wlf.py rulegen --wordlist hashes.pot --max-lines 100000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_rg.add_argument("--wordlist", nargs="+", metavar="FILE",
                       help="Password file(s) to analyze")
    p_rg.add_argument("--dictionary", metavar="FILE",
                       help="Optional base word dictionary for matching")
    p_rg.add_argument("--top-rules", dest="top_rules", type=int, default=100,
                       help="Number of top rules to output (default: 100)")
    p_rg.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                       help="Max passwords to analyze (0 = all)")
    p_rg.add_argument("-o", "--output", help="Output file (.rule for hashcat format)")

    # ── benchmark ────────────────────────────────────────────────────────
    p_bm = sub.add_parser(
        "benchmark",
        help="Measure wordlist quality against a reference set",
        description=(
            "Benchmark a generated wordlist against a reference password set.\n"
            "Measures hit rate, coverage, efficiency, diversity, and more.\n"
            "Inspired by MAYA (IEEE S&P 2026) benchmarking framework.\n\n"
            "Examples:\n"
            "  wlf.py benchmark --wordlist generated.lst --reference rockyou.txt\n"
            "  wlf.py benchmark --wordlist out.lst --reference test_set.txt --json report.json\n"
            "  wlf.py benchmark --wordlist my_list.lst --reference leaked.txt --max-candidates 1000000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_bm.add_argument("--wordlist", required=True, metavar="FILE",
                       help="Generated wordlist to evaluate")
    p_bm.add_argument("--reference", required=True, metavar="FILE",
                       help="Reference password set (ground truth)")
    p_bm.add_argument("--max-candidates", dest="max_candidates", type=int, default=0,
                       help="Max lines to read from wordlist (0 = all)")
    p_bm.add_argument("--max-reference", dest="max_reference", type=int, default=0,
                       help="Max lines to read from reference (0 = all)")
    p_bm.add_argument("--json", dest="json_output", metavar="FILE",
                       help="Save results as JSON report")
    p_bm.add_argument("-o", "--output", help="Save text report to file")

    # anomaly-score
    p_anm = sub.add_parser(
        "anomaly-score",
        help="Rank wordlist entries by anomaly score (most unusual first)",
        description=(
            "Score each password in a wordlist using a native ensemble of\n"
            "IsolationForest-lite and HBOS-lite algorithms. No external\n"
            "ML library required. Higher score = more anomalous.\n\n"
            "Examples:\n"
            "  wlf.py anomaly-score wordlist.lst --top 50\n"
            "  wlf.py anomaly-score leak.txt --top 100 -o rare.txt\n"
            "  wlf.py anomaly-score corpus.lst --max-lines 200000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_anm.add_argument("wordlist", metavar="WORDLIST", help="Input wordlist file path")
    p_anm.add_argument("--top", type=int, default=0, metavar="N",
                       help="Return only the top-N most anomalous entries (0 = all)")
    p_anm.add_argument("--max-lines", dest="max_lines", type=int, default=100_000,
                       help="Maximum lines to read from wordlist (default: 100000)")
    p_anm.add_argument("-o", "--output", metavar="FILE",
                       help="Save scored password list to file (one per line, no scores)")

    # ── prince ───────────────────────────────────────────────────────────
    p_pr = sub.add_parser(
        "prince",
        help="PRINCE attack - chained element combination",
        description=(
            "PRINCE (PRobability INfinite Chained Elements) attack mode.\n"
            "Generates passwords by chaining elements from a wordlist.\n"
            "Discovers multi-word passwords like 'correcthorsebatterystaple'.\n\n"
            "Examples:\n"
            "  wlf.py prince --wordlist base_words.txt --min-elem 2 --max-elem 4\n"
            "  wlf.py prince --wordlist words.txt --separator '-' --case-permute\n"
            "  wlf.py prince --wordlist top1000.txt --min-len 8 --max-len 20 --limit 500000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_pr.add_argument("--wordlist", required=True, metavar="FILE",
                       help="Input wordlist (element source)")
    p_pr.add_argument("--min-len", dest="min_len", type=int, default=1,
                       help="Min password length (default: 1)")
    p_pr.add_argument("--max-len", dest="max_len", type=int, default=32,
                       help="Max password length (default: 32)")
    p_pr.add_argument("--min-elem", dest="min_elem", type=int, default=1,
                       help="Min elements per chain (default: 1)")
    p_pr.add_argument("--max-elem", dest="max_elem", type=int, default=4,
                       help="Max elements per chain (default: 4)")
    p_pr.add_argument("--separator", default="",
                       help="Element separator (default: empty, use EMPTY for none)")
    p_pr.add_argument("--case-permute", dest="case_permute", action="store_true",
                       help="Generate case permutations")
    p_pr.add_argument("--wordlen-min", dest="wordlen_min", type=int, default=0,
                       help="Min element word length (0 = no filter)")
    p_pr.add_argument("--wordlen-max", dest="wordlen_max", type=int, default=0,
                       help="Max element word length (0 = no filter)")
    p_pr.add_argument("--superchop", type=int, default=0,
                       help="Truncate each element to N chars (pp64 superchop parity)")
    p_pr.add_argument("--max-words", dest="max_words", type=int, default=0,
                       help="Max words to load from file (0 = all)")
    p_pr.add_argument("--limit", type=int, default=0,
                       help="Max candidates (0 = unlimited)")
    p_pr.add_argument("-o", "--output", help="Output file")

    # ── br-names ─────────────────────────────────────────────────────────
    p_brn = sub.add_parser(
        "br-names",
        help="Generate username list from BRWordList Brazilian name files",
        description=(
            "Loads name lists from the BRWordList submodule and produces\n"
            "a deduplicated username wordlist suitable for credential attacks.\n\n"
            "Requires: --brwordlist-path PATH or WLF_BRWORDLIST_PATH\n\n"
            "Examples:\n"
            "  wlf.py br-names\n"
            "  wlf.py br-names --category surnames -o surnames.lst\n"
            "  wlf.py br-names --category all --leet -o names_leet.lst\n"
            "  wlf.py br-names --brwordlist-path /opt/BRWordList"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_brn.add_argument(
        "--category", default="names",
        choices=["names", "surnames", "full_names", "initials", "rev_initials", "a-z", "all"],
        help="Name category to load (default: names)",
    )
    p_brn.add_argument(
        "--leet", action="store_true",
        help="Also generate basic leet variants",
    )
    p_brn.add_argument(
        "--brwordlist-path", dest="brwordlist_path", metavar="PATH",
        help="Explicit path to BRWordList root (auto-detected if omitted)",
    )
    p_brn.add_argument("-o", "--output", help="Output file")

    # ── iwlgen ───────────────────────────────────────────────────────────
    p_iw = sub.add_parser(
        "iwlgen",
        help="Intelligence keyword permutation wordlist generator",
        description=(
            "Generates wordlists from keyword permutations with optional\n"
            "leet substitution, abbreviation, reversal, and numeric tails.\n"
            "Native Python 3 port of intelligence-wordlist-generator.\n\n"
            "Examples:\n"
            "  wlf.py iwlgen --keywords admin,router,2024 --connectors @.\n"
            "  wlf.py iwlgen --keywords empresa,corp --leet --abbreviation\n"
            "  wlf.py iwlgen --keywords cisco,admin --num-tails 1-99 --connectors ._\n"
            "  wlf.py iwlgen --keywords guest,pass --connectors '' -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_iw.add_argument(
        "--keywords", required=True, metavar="KW1,KW2,...",
        help="Comma-separated keywords (e.g. admin,router,2024)",
    )
    p_iw.add_argument(
        "--connectors", default="", metavar="CHARS",
        help=(
            "Connector characters to join keywords, specified as a string.\n"
            "Each character becomes a separate connector (default: '._-@' empty).\n"
            "Example: --connectors '@._' uses @, ., _ and also empty string."
        ),
    )
    p_iw.add_argument(
        "--leet", action="store_true",
        help="Apply leet-speak substitutions to generated words",
    )
    p_iw.add_argument(
        "--abbreviation", action="store_true",
        help="Generate single-character abbreviation variants",
    )
    p_iw.add_argument(
        "--reverse", action="store_true",
        help="Generate element-reversal variants",
    )
    p_iw.add_argument(
        "--num-tails", dest="num_tails", metavar="SPEC",
        help="Numeric tail specs, comma-separated (e.g. '1,2,01-05,2024')",
    )
    p_iw.add_argument(
        "--min-length", dest="min_length", type=int, default=4,
        help="Minimum entry length (default: 4)",
    )
    p_iw.add_argument(
        "--max-length", dest="max_length", type=int, default=64,
        help="Maximum entry length (default: 64)",
    )
    p_iw.add_argument("-o", "--output", help="Output file")

    # ── rules ────────────────────────────────────────────────────────────
    p_rules = sub.add_parser(
        "rules",
        help="Apply, convert or optimize hashcat/John rules",
        description=(
            "Rule engine: run hashcat and John the Ripper rules against a\n"
            "wordlist (like hashcat --stdout -r), convert between the two\n"
            "dialects, or optimize a rule file.\n\n"
            "Examples:\n"
            "  wlf.py rules apply --wordlist base.txt --rules best64.rule -o out.lst\n"
            "  wlf.py rules apply --wordlist base.txt --rule 'c $1;$2;so0' --dedupe\n"
            "  wlf.py rules convert --rules hc.rule --to john -o jtr.rule\n"
            "  wlf.py rules optimize --rules messy.rule -o clean.rule"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_rules.add_argument("rules_action", choices=["apply", "convert", "optimize"],
                         default="apply", nargs="?",
                         help="Action (default: apply)")
    p_rules.add_argument("--wordlist", metavar="FILE",
                         help="Input wordlist (for apply)")
    p_rules.add_argument("--rules", metavar="FILE",
                         help="Rule file (one rule per line, # comments)")
    p_rules.add_argument("--rule", metavar="STR",
                         help="Inline rule(s), separated by ';'")
    p_rules.add_argument("--to", choices=["hashcat", "john"], default="john",
                         help="Target dialect for convert (default: john)")
    p_rules.add_argument("--dedupe", action="store_true",
                         help="Suppress duplicate outputs (apply mode)")
    p_rules.add_argument("-o", "--output", help="Output file")

    # ── affix ────────────────────────────────────────────────────────────
    p_affix = sub.add_parser(
        "affix",
        help="Composite-affix mutation layer (chain date + special affixes)",
        description=(
            "Append composite affixes to a wordlist in a single pass: the core\n"
            "alone, special+core, core+special, and special+core+special (e.g.\n"
            "0724, @0724, 0724!, @0724!). Guarantees two-affix chaining that a\n"
            "single combiner --tails or plain mutate --suffixes does not produce.\n"
            "Can also emit a hashcat rule set for use with 'rules apply'.\n\n"
            "Examples:\n"
            "  wlf.py combiner nerd trilha --titlecase | wlf.py affix - --dates '0724,1988'\n"
            "  wlf.py affix base.lst --dates '0724,2806' --specials '!,@,#' -o out.lst\n"
            "  wlf.py affix base.lst --dates '0724' --case -o out.lst\n"
            "  wlf.py affix nerdtrilha --dates '0724' --titlecase\n"
            "  wlf.py affix --dates '0724,1988' --specials '!,@,#' --emit-ruleset affix.rule\n"
            "  wlf.py rules apply --wordlist base.lst --rules affix.rule -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

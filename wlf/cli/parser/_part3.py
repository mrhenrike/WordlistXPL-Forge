                       help="Leet substitution mode")
    p_lt.add_argument("--custom-map", dest="custom_map", default="",
                       help="Custom mapping (e.g. a=@,4;t=7;s=$;l=1,|)")
    p_lt.add_argument("--max-results", type=int, default=10000, dest="max_results")
    p_lt.add_argument("--gpu", action="store_true",
                       help="Prefer GPU-assisted leet expansion via compute_backend")
    p_lt.add_argument("-o", "--output", help="Output file")

    p_lp = sub.add_parser(
        "leet-perm",
        help="Cartesian leet permutation over a wordlist (elpscrk-style)",
        description=(
            "Apply full cartesian leet substitution to each line of a wordlist.\n"
            "Useful as a post-pass after profile or combiner generation.\n\n"
            "Examples:\n"
            "  wlf.py leet-perm words.lst -o leet_words.lst\n"
            "  wlf.py leet-perm base.lst --max-per-word 256 --max-lines 5000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_lp.add_argument("wordlist", help="Input wordlist (one token per line)")
    p_lp.add_argument("-o", "--output", help="Output file")
    p_lp.add_argument("-m", "--mode", default="medium", choices=["medium", "custom"],
                       help="Leet map preset (default: medium)")
    p_lp.add_argument("--custom-map", dest="custom_map", default="",
                       help="Custom char map (e.g. a=@,4;t=7;s=$)")
    p_lp.add_argument("--max-per-word", dest="max_per_word", type=int, default=512,
                       help="Max variants per input word (default: 512)")
    p_lp.add_argument("--max-lines", dest="max_lines", type=int, default=0,
                       help="Max input lines to process (0 = all)")

    # ── xor ───────────────────────────────────────────────────────────────
    p_xr = sub.add_parser("xor", help="XOR encryption / brute-force")
    xr_group = p_xr.add_mutually_exclusive_group(required=True)
    xr_group.add_argument("--brute", metavar="HEX", help="Brute-force single-byte key")
    xr_group.add_argument("--encrypt", metavar="TEXT", help="Encrypt text")
    xr_group.add_argument("--decrypt", metavar="HEX", help="Decrypt hex string")
    p_xr.add_argument("--key", help="Key for encrypt/decrypt")
    p_xr.add_argument("-o", "--output", help="Output file")

    # ── analyze ───────────────────────────────────────────────────────────
    p_an = sub.add_parser("analyze", help="Statistical analysis of wordlist")
    p_an.add_argument("wordlist", help="Wordlist to analyze")
    p_an.add_argument("--top", type=int, default=20, help="Top N most frequent (default: 20)")
    p_an.add_argument("--masks", action="store_true",
                       help="Include Hashcat mask analysis (?u?l?d?s frequency)")
    p_an.add_argument("--base-words", dest="base_words", action="store_true",
                       help="Extract base words (strip trailing digits/specials)")
    p_an.add_argument("--base-output", dest="base_output", metavar="FILE",
                       help="Save base words to file")
    p_an.add_argument("--base-ranked", dest="base_ranked", action="store_true",
                       help="Show base words with frequency ranking (pipal parity)")
    p_an.add_argument("--position-freq", dest="position_freq", action="store_true",
                       help="Show character frequency by position (pipal Frequency_Checker)")
    p_an.add_argument("--all-masks", dest="all_masks", action="store_true",
                       help="Show ALL masks (not just top N)")
    p_an.add_argument("--mask-optindex", dest="mask_optindex", action="store_true",
                       help="PACK maskgen optindex ranking with time budget")
    p_an.add_argument("--mask-csv", dest="mask_csv", metavar="FILE",
                       help="Export PACK-compatible mask CSV (requires --mask-optindex)")
    p_an.add_argument("--time-budget", dest="time_budget", type=float, default=1.0,
                       help="Crack time budget hours for --mask-optindex")
    p_an.add_argument("--pps", type=int, default=0,
                       help="Passwords/sec for --mask-optindex (0=auto)")
    p_an.add_argument("--use-gpu", dest="use_gpu", action="store_true",
                       help="GPU PPS for --mask-optindex (optional)")
    p_an.add_argument("--format", dest="format", choices=["text", "json", "csv", "markdown"],
                       default="text", help="Output format: text, json, csv, markdown (default: text)")
    p_an.add_argument("-o", "--output", help="Save report to file")

    # ── compare ──────────────────────────────────────────────────────────
    p_cmp = sub.add_parser("compare", help="Compare two wordlists (overlap metrics)")
    p_cmp.add_argument("file_a", help="First wordlist")
    p_cmp.add_argument("file_b", help="Second wordlist")
    p_cmp.add_argument("--format", choices=["text", "json", "csv"],
                        default="text", help="Output format (default: text)")
    p_cmp.add_argument("--case-insensitive", action="store_true",
                        dest="case_insensitive",
                        help="Case-insensitive comparison")
    p_cmp.add_argument("--sample", type=int, default=0, metavar="N",
                        help="Reservoir sample N entries per file (for large wordlists)")
    p_cmp.add_argument("--output-common", dest="output_common", metavar="FILE",
                        help="Save common entries to file")
    p_cmp.add_argument("--output-only-a", dest="output_only_a", metavar="FILE",
                        help="Save entries only in A to file")
    p_cmp.add_argument("--output-only-b", dest="output_only_b", metavar="FILE",
                        help="Save entries only in B to file")
    p_cmp.add_argument("-o", "--output", help="Save report to file")

    # ── cluster ──────────────────────────────────────────────────────────
    p_cl = sub.add_parser("cluster", help="Cluster/classify passwords by structure")
    p_cl.add_argument("wordlist", help="Wordlist to cluster")
    p_cl.add_argument("--algorithm", choices=["kmeans", "dbscan"],
                       default="kmeans", help="Clustering algorithm (default: kmeans)")
    p_cl.add_argument("--clusters", type=int, default=5, metavar="K",
                       help="Number of clusters for K-means (default: 5)")
    p_cl.add_argument("--eps", type=float, default=0.3,
                       help="DBSCAN epsilon radius (default: 0.3)")
    p_cl.add_argument("--min-samples", type=int, default=3, dest="min_samples",
                       help="DBSCAN min samples (default: 3)")
    p_cl.add_argument("--seed", type=int, default=42, help="Random seed")
    p_cl.add_argument("--label", action="store_true",
                       help="Classify only (no clustering)  - label each password by type")
    p_cl.add_argument("--format", choices=["text", "json", "csv"],
                       default="text", help="Output format (default: text)")
    p_cl.add_argument("-o", "--output", help="Save report to file")

    # ── hibp ─────────────────────────────────────────────────────────────
    p_hb = sub.add_parser("hibp", help="Check passwords against HIBP Pwned Passwords")
    p_hb.add_argument("wordlist", help="Wordlist to check")
    p_hb.add_argument("--format", choices=["text", "json", "csv"],
                       default="text", help="Output format (default: text)")
    p_hb.add_argument("--min-count", type=int, default=0, dest="min_count",
                       help="Minimum breach count to report (default: 0 = all)")
    p_hb.add_argument("--offline", metavar="HASH_FILE",
                       help="Offline HIBP hash file (SHA-1:count per line)")
    p_hb.add_argument("--api-key-file", dest="api_key_file", metavar="FILE",
                       help="Path to HIBP API key file (default: .hibp-key or ~/.hibp-key)")
    p_hb.add_argument("--output-breached", dest="output_breached", metavar="FILE",
                       help="Save breached passwords to file (pw:count)")
    p_hb.add_argument("--output-clean", dest="output_clean", metavar="FILE",
                       help="Save clean (not breached) passwords to file")
    p_hb.add_argument("-o", "--output", help="Save report to file")

    # ── entropy ──────────────────────────────────────────────────────────
    p_ent = sub.add_parser("entropy", help="Entropy distribution analysis and visualization")
    p_ent.add_argument("wordlist", help="Wordlist to analyze")
    p_ent.add_argument("--bins", type=int, default=20,
                        help="Histogram bins (default: 20)")
    p_ent.add_argument("--classify", action="store_true",
                        help="Show per-password classification by strength band")
    p_ent.add_argument("--format", choices=["text", "json", "csv"],
                        default="text", help="Output format (default: text)")
    p_ent.add_argument("-o", "--output", help="Save report to file")

    # ── hcmon (cracker monitor) ──────────────────────────────────────────
    p_hm = sub.add_parser("hcmon", help="Monitor Hashcat/JtR cracking sessions")
    p_hm.add_argument("--tool", choices=["hashcat", "john"],
                       default="hashcat", help="Cracking tool (default: hashcat)")
    p_hm.add_argument("--session", help="Session name")
    p_hm.add_argument("--status-file", dest="status_file", metavar="FILE",
                       help="Status output file (text or JSON)")
    p_hm.add_argument("--restore-file", dest="restore_file", metavar="FILE",
                       help="Restore/rec file path")
    p_hm.add_argument("--format", choices=["text", "json"],
                       default="text", help="Output format (default: text)")
    p_hm.add_argument("-o", "--output", help="Save report to file")

    # ── intelx ───────────────────────────────────────────────────────────
    p_ix = sub.add_parser("intelx", help="Search IntelX for leaked credentials/data")
    p_ix.add_argument("--query", help="Search term (email, domain, credential)")
    p_ix.add_argument("--query-file", dest="query_file", metavar="FILE",
                       help="File with search terms (one per line)")
    p_ix.add_argument("--api-key-file", dest="api_key_file", metavar="FILE",
                       help="IntelX API key file (default: .intelx-key or ~/.intelx-key)")
    p_ix.add_argument("--type", dest="type", choices=["all", "leak", "paste", "darknet", "document", "whois"],
                       default="all", help="Result type filter (default: all)")
    p_ix.add_argument("--max-results", type=int, default=100, dest="max_results",
                       help="Maximum results per query (default: 100)")
    p_ix.add_argument("--format", choices=["text", "json", "csv"],
                       default="text", help="Output format (default: text)")
    p_ix.add_argument("-o", "--output", help="Save report to file")

    # ── merge ─────────────────────────────────────────────────────────────
    p_mg = sub.add_parser("merge", help="Merge and deduplicate wordlists")
    p_mg.add_argument("files", nargs="+", help="Input wordlists")
    p_mg.add_argument("--min-len", type=int, default=6, dest="min_len")
    p_mg.add_argument("--max-len", type=int, default=128, dest="max_len")
    p_mg.add_argument("--no-numeric", action="store_true", dest="no_numeric",
                       help="Remove purely numeric entries")
    p_mg.add_argument("--filter", help="Include regex filter (only matches pass)")
    p_mg.add_argument("--no-dedupe", action="store_true", dest="no_dedupe")
    p_mg.add_argument("--sort", choices=["alpha", "length", "random", "frequency"],
                       help="Sort mode: alpha, length, random, or frequency (most common first)")
    p_mg.add_argument("-o", "--output", help="Output file")

    # ── dns ───────────────────────────────────────────────────────────────
    p_dn = sub.add_parser("dns", help="DNS/subdomain fuzzing (alterx + DNSCewl style)")
    p_dn.add_argument("-d", "--domain", default="", help="Target domain (required unless --domain-list)")
    p_dn.add_argument("--domain-list", dest="domain_list", metavar="FILE",
                       help="File with one domain per line (multi-domain mode)")
    p_dn.add_argument("-w", "--wordlist", help="Words file")
    p_dn.add_argument("--words", nargs="+", help="Direct word list")
    p_dn.add_argument("-t", "--template", help="Inline template (e.g. dev-{word}.{domain})")
    p_dn.add_argument("--template-file", dest="template_file", metavar="FILE",
                       help="YAML file with permutation templates (alterx-compatible)")
    p_dn.add_argument("--separator", help="Custom separator between tokens (e.g. _ or .)")
    p_dn.add_argument("--match-regex", dest="match_regex", metavar="REGEX",
                       help="Include only output matching this regex")
    p_dn.add_argument("--filter-regex", dest="filter_regex", metavar="REGEX",
                       help="Exclude output matching this regex")
    p_dn.add_argument("--no-prefixes", action="store_true", dest="no_prefixes")
    p_dn.add_argument("--no-suffixes", action="store_true", dest="no_suffixes")
    p_dn.add_argument("--enrich", action="store_true",
                       help="Extract tokens from input FQDNs to enrich payloads (alterx -enrich)")
    p_dn.add_argument("--clusterbomb", action="store_true",
                       help="Use ClusterBomb mode with built-in alterx patterns and payloads")
    p_dn.add_argument("--payload", dest="payloads", action="append", metavar="KEY=FILE",
                       help="Custom payload file (key=file, can repeat). Keys: word, number, region")
    p_dn.add_argument("--dnscewl", action="store_true",
                       help="Add DNSCewl-style mutations (append/prepend/numeric-range)")
    p_dn.add_argument("--numeric-range", dest="numeric_range", type=int, default=10,
                       help="Numeric range for DNSCewl mutations (default: 10)")
    p_dn.add_argument("--extension-swap", dest="extension_swap", nargs="+", metavar="TLD",
                       help="Swap TLD extensions (e.g. com.au co.uk org)")
    p_dn.add_argument("--estimate", action="store_true",
                       help="Estimate output size without generating")
    p_dn.add_argument("-o", "--output", help="Output file")

    # ── pharma ────────────────────────────────────────────────────────────
    p_ph = sub.add_parser(
        "pharma",
        help="Generate passwords and usernames for retail/pharmacy chain patterns",
        description=(
            "Generates wordlists based on common credential patterns in retail chain environments.\n\n"
            "Password patterns:\n"
            "  abbrev+sep+id       Brand#1206  ABBREV_1206  abbrev1206\n"
            "  partner+cnpj        system01234567890123\n"
            "  abbrev+sep+cnpj     AB-01234567890123\n\n"
            "Username patterns:\n"
            "  abbrev+id@domain    XX1206@corp.com  xx0100@corp.com\n"
            "  IJ/LJ/TC+id         IJ1206  IJ120601  IJ120602  LJ0100\n\n"
            "Examples:\n"
            "  wlf pharma --brand BrandX --ids 1200-1210 -o out.lst\n"
            "  wlf pharma --brand RetailCo --abbrevs RC,RET --cnpj 01234567890123 --mode passwords\n"
            "  wlf pharma --brand BrandX --ids 5,6,7,8 --domains corp.example --mode usernames\n"
            "  wlf pharma --brand BrandX --ids 1206 --partners system,partner --separators @,#\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ph.add_argument("--brand", "-b", default="BrandX",
                      help="Brand/company name (default: BrandX)")
    p_ph.add_argument("--ids",
                      help="Store ID range '1200-1210' or list '1206,1207,1208'")
    p_ph.add_argument("--cnpj",
                      help="Tax ID(s) comma-separated (e.g. 01234567890123)")
    p_ph.add_argument("--abbrevs",
                      help="Extra abbreviations comma-separated (e.g. AB,ABBRV,ABR)")
    p_ph.add_argument("--separators",
                      help="Separators comma-separated (default: @,#,!,&,_,-,.,*,'')")
    p_ph.add_argument("--partners",
                      help="System/partner prefixes comma-separated (default: system,portal,erp,...)")
    p_ph.add_argument("--domains",
                      help="Email domains for usernames comma-separated (e.g. corp.example)")
    p_ph.add_argument("--mode", choices=["passwords", "usernames", "both"], default="both",
                      help="Generation mode: passwords | usernames | both (default: both)")
    p_ph.add_argument("--no-padding", action="store_true", dest="no_padding",
                      help="Skip zero-padded ID variants (0100, 01206...)")
    p_ph.add_argument("--min-len", type=int, default=0, dest="min_len",
                      help="Minimum length of generated entries")
    p_ph.add_argument("--max-len", type=int, default=0, dest="max_len",
                      help="Maximum length of generated entries")
    p_ph.add_argument("-o", "--output", help="Output file")

    # ── sanitize ──────────────────────────────────────────────────────────
    p_sa = sub.add_parser(
        "sanitize",
        help="Clean wordlist (dedupe, sort, filter, remove blanks and comments)",
        description=(
            "Sanitize an existing wordlist applying filters in order:\n"
            "  1. Remove comments (#)     2. Remove blank lines\n"
            "  3. Filter by length        4. Filter by regex\n"
            "  5. Deduplicate             6. Sort\n\n"
            "Examples:\n"
            "  wlf.py sanitize list.lst --inplace\n"
            "  wlf.py sanitize list.lst --min-len 8 --sort alpha -o clean.lst\n"
            "  wlf.py sanitize list.lst --filter '^[a-zA-Z]' --exclude '\\d{3,}$' -o out.lst\n"
            "  wlf.py sanitize list.lst --min-len 6 --max-len 20 --sort length-rev -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_sa.add_argument("wordlist", help="Wordlist to sanitize")
    p_sa.add_argument("--min-len", type=int, default=None, dest="min_len",
                       help="Minimum length (removes shorter entries)")
    p_sa.add_argument("--max-len", type=int, default=None, dest="max_len",
                       help="Maximum length (removes longer entries)")
    p_sa.add_argument("--sort", dest="sort",
                       choices=["alpha", "alpha-rev", "length", "length-rev", "random", "frequency"],
                       help="Sort mode: alpha, alpha-rev, length, length-rev, random, frequency")
    p_sa.add_argument("--filter", dest="filter", metavar="REGEX",
                       help="Include regex - keep only matching lines")
    p_sa.add_argument("--exclude", dest="exclude", metavar="REGEX",
                       help="Exclude regex - remove matching lines")
    p_sa.add_argument("--no-dedupe", action="store_true", dest="no_dedupe",
                       help="Do not remove duplicates")
    p_sa.add_argument("--keep-blank", action="store_true", dest="keep_blank",
                       help="Keep blank lines")
    p_sa.add_argument("--keep-comments", action="store_true", dest="keep_comments",
                       help="Keep comment lines (#)")
    p_sa.add_argument("--strip-control", dest="strip_control", action="store_true",
                       help="Remove control characters (tabs, null bytes, escape sequences) from lines")
    p_sa.add_argument("--inplace", action="store_true",
                       help="Overwrite original file")
    p_sa.add_argument("-o", "--output", help="Output file (default: stdout)")

    # ── reverse ───────────────────────────────────────────────────────────
    p_rv = sub.add_parser(
        "reverse",
        help="Reverse line order of a wordlist (tac)",
        description=(
            "Reverse the line order of a wordlist (equivalent to 'tac').\n\n"
            "Examples:\n"
            "  wlf.py reverse list.lst -o reversed.lst\n"
            "  wlf.py reverse list.lst --inplace"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_rv.add_argument("wordlist", help="Wordlist to reverse")
    p_rv.add_argument("--inplace", action="store_true",
                       help="Overwrite original file")
    p_rv.add_argument("-o", "--output", help="Output file (default: stdout)")

    # ── mangle ────────────────────────────────────────────────────────────────
    p_mn = sub.add_parser(
        "mangle",
        help="Apply hashcat-style mangling rules to a wordlist",
        description=(
            "Apply transformation rules to every word in a wordlist.\n\n"
            "Rules (inspired by Hashcat/John rule engine):\n"
            "  capitalize   - Capitalize first letter\n"
            "  upper        - Uppercase entire word\n"
            "  lower        - Lowercase entire word\n"
            "  reverse      - Reverse the word\n"
            "  toggle       - Toggle case of all chars\n"
            "  append_num   - Append 0-99, common years\n"
            "  prepend_num  - Prepend 0-9\n"
            "  append_special - Append !, @, #, $, %, etc.\n"
            "  leet_basic   - Basic leet substitutions\n"
            "  duplicate    - Duplicate the word (e.g. passpass)\n"
            "  strip_vowels - Remove all vowels\n\n"
            "Examples:\n"
            "  wlf.py mangle wordlist.lst -o mangled.lst\n"
            "  wlf.py mangle wordlist.lst --rules capitalize,leet_basic,append_num\n"
            "  wlf.py mangle wordlist.lst --list-rules"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_mn.add_argument("wordlist", nargs="?", default=None, help="Wordlist to mangle")
    p_mn.add_argument("--rules", default="all",
                       help="Comma-separated rule names or 'all' (default: all)")
    p_mn.add_argument("--list-rules", dest="list_rules", action="store_true",
                       help="List available mangling rules and exit")
    p_mn.add_argument("--overseer", action="store_true",
                       help="PyMangler Overseer mask mode with time budget")
    p_mn.add_argument("--masks", metavar="LIST",
                       help="Comma-separated masks for Overseer (w,wd,wds,...)")
    p_mn.add_argument("--time-budget", dest="time_budget", type=float, default=1.0,
                       help="Crack time budget in hours for Overseer (default: 1.0)")
    p_mn.add_argument("--pps", type=int, default=0,
                       help="Passwords/sec for Overseer budget (0=auto CPU/GPU)")
    p_mn.add_argument("--use-gpu", dest="use_gpu", action="store_true",
                       help="Use GPU PPS defaults in Overseer mode (optional)")
    p_mn.add_argument("--capswap", action="store_true",
                       help="Enable positional capswap in Overseer mode")
    p_mn.add_argument("-o", "--output", help="Output file")

    # ── improve (CUPP -w parity) ─────────────────────────────────────────────
    p_imp = sub.add_parser(
        "improve",
        help="Enrich an existing wordlist with leet, years, and specials",
    )
    p_imp.add_argument("wordlist", help="Source wordlist")
    p_imp.add_argument("-o", "--output", help="Output file")
    p_imp.add_argument("--leet", default="basic", choices=["basic", "medium", "aggressive"])
    p_imp.add_argument("--no-years", dest="no_years", action="store_true")
    p_imp.add_argument("--no-specials", dest="no_specials", action="store_true")
    p_imp.add_argument("--year-start", dest="year_start", type=int, default=2020)
    p_imp.add_argument("--year-end", dest="year_end", type=int, default=2027)
    p_imp.add_argument("--min-len", dest="min_len", type=int, default=6)
    p_imp.add_argument("--max-len", dest="max_len", type=int, default=32)

    # ── maya-rank ─────────────────────────────────────────────────────────────
    p_mr = sub.add_parser(
        "maya-rank",
        help="Rank wordlist candidates by MAYA cracking probability",
    )
    p_mr.add_argument("wordlist", help="Wordlist to rank")
    p_mr.add_argument("-o", "--output", help="Ranked output file")
    p_mr.add_argument("--top", type=int, default=0, help="Keep top N candidates (0=all)")
    p_mr.add_argument("--backend", choices=["auto", "torch", "fallback"], default="auto")
    p_mr.add_argument("--use-gpu", dest="use_gpu", action="store_true",
                       help="Use GPU for torch backend (optional)")
    p_mr.add_argument("--min-score", dest="min_score", type=float, default=0.0)

    # ── osint-perm ────────────────────────────────────────────────────────────
    p_op = sub.add_parser(
        "osint-perm",
        help="OSINT-based password permutations from target profile",
        description=(
            "Generate password candidates from OSINT profile fields\n"
            "(name, nickname, birth date, pet, phone, keywords).\n\n"
            "Examples:\n"
            "  wlf.py osint-perm --first-name PessoaX --last-name CorpX -o out.lst\n"
            "  wlf.py osint-perm --nick robotx --birth 01/1990 --complexity 2 -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_op.add_argument("--first-name", dest="first_name", help="Target first name")
    p_op.add_argument("--last-name", dest="last_name", help="Target last name")
    p_op.add_argument("--nick", help="Nickname or handle")
    p_op.add_argument("--birth", help="Birth date (DD/MM/YYYY or MM/YYYY)")
    p_op.add_argument("--pet", help="Pet name")
    p_op.add_argument("--phone", help="Phone number")
    p_op.add_argument("--complexity", type=int, default=1, choices=range(6),
                       metavar="0-5", help="Permutation depth (default: 1)")
    p_op.add_argument("--keywords", nargs="+", metavar="WORD", help="Extra keywords")
    p_op.add_argument("-o", "--output", help="Output file")

    # ── cupp ──────────────────────────────────────────────────────────────────
    p_cupp = sub.add_parser(
        "cupp",
        help="CUPP-style target-specific password generation",
        description=(
            "Generate password candidates from a personal profile\n"
            "(names, dates, pets, company, custom words).\n\n"
            "Examples:\n"
            "  wlf.py cupp --first-name PessoaX --last-name CorpX --company BrandX -o out.lst\n"
            "  wlf.py cupp --nick robotx --birth 01/1990 --words petx robotx --max-output 50000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cupp.add_argument("--first-name", dest="first_name", help="Target first name")
    p_cupp.add_argument("--last-name", dest="last_name", help="Target last name")
    p_cupp.add_argument("--nick", help="Nickname or handle")
    p_cupp.add_argument("--birth", help="Birth date")
    p_cupp.add_argument("--pet", help="Pet name")
    p_cupp.add_argument("--company", help="Company name")
    p_cupp.add_argument("--words", nargs="+", metavar="WORD", help="Extra words")
    p_cupp.add_argument("--max-output", dest="max_output", type=int, default=0,
                       help="Max candidates (0 = unlimited)")
    p_cupp.add_argument("-o", "--output", help="Output file")

    # ── pattern-rank ────────────────────────────────────────────────────────
    p_prk = sub.add_parser(
        "pattern-rank",
        help="Analyze wordlist patterns: keyboard walks, Hashcat masks",
        description=(
            "Analyze a password wordlist for structural patterns:\n"
            "keyboard walks, PT-BR month names, top Hashcat masks.\n\n"
            "Examples:\n"
            "  wlf.py pattern-rank passwords.lst\n"
            "  wlf.py pattern-rank leaked.txt --layout qwerty --max-lines 100000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_prk.add_argument("wordlist", help="Wordlist to analyze")
    p_prk.add_argument("--layout", default="qwerty",
                       help="Keyboard layout for walk detection (default: qwerty)")
    p_prk.add_argument("--max-lines", dest="max_lines", type=int, default=500_000,
                       help="Max lines to analyze (default: 500000)")

    # ── scrape-target ───────────────────────────────────────────────────────
    p_st = sub.add_parser(
        "scrape-target",
        help="Crawl a target URL and extract words for wordlists",
        description=(
            "Lightweight target spider: crawl a URL and extract\n"
            "unique words suitable for wordlist generation.\n\n"
            "Examples:\n"
            "  wlf.py scrape-target --url https://example.com -o words.lst\n"
            "  wlf.py scrape-target --url https://corp.com --depth 3 --max-pages 50"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_st.add_argument("--url", required=True, help="Target URL to crawl")
    p_st.add_argument("--depth", type=int, default=2, help="Crawl depth (default: 2)")
    p_st.add_argument("--min-len", dest="min_len", type=int, default=4,
                       help="Min word length (default: 4)")
    p_st.add_argument("--max-pages", dest="max_pages", type=int, default=20,
                       help="Max pages to fetch (default: 20)")
    p_st.add_argument("-o", "--output", help="Output file")

    # ── default-creds ─────────────────────────────────────────────────────────
    p_dc = sub.add_parser(
        "default-creds",
        help="Query local default credentials corpus (IoT/routers/printers/ICS)",
        description=(
            "Query the local default-credentials corpus under generated/\n"
            "(gitignored; not shipped in the public tree).\n\n"
            "Requires --db PATH to a default-creds JSON (suite EmbedXPL resources).\n"
            "  python3 update_wordlists.py\n\n"
            "Examples:\n"
            "  wlf.py default-creds -o all_defaults.lst\n"
            "  wlf.py default-creds --vendor mikrotik -o mikrotik.lst\n"
            "  wlf.py default-creds --vendor huawei --format json\n"
            "  wlf.py default-creds --snmp -o snmp_communities.lst\n"
            "  wlf.py default-creds --snmp --snmp-version v3 -o snmpv3.lst\n"
            "  wlf.py default-creds --format user -o usernames.lst\n"
            "  wlf.py default-creds --list-vendors\n"
            "  wlf.py default-creds --db /path/to/default-creds.json -o out.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dc.add_argument("--vendor", help="Filter by vendor name (partial match)")
    p_dc.add_argument("--protocol", help="Filter by protocol (api, ssh, telnet, http)")
    p_dc.add_argument("--category", help="Filter by category (router, printer, ics)")
    p_dc.add_argument(
        "--format", choices=["combo", "user", "pass", "json"],
        default="combo", help="Output format (default: combo = user:pass)",
    )

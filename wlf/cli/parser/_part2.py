def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="wlf.py",
        description="WordlistXPL-Forge - Professional wordlist generation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python wlf.py charset 6 8 abc123
  python wlf.py charset 8 8 --pattern "Pass@@@%%%"
  python wlf.py charset 8 8 --mask "?u?l?l?l?d?d?s"
  python wlf.py charset 8 8 --digits 2 --lower 4 --upper 1 --special 1
  python wlf.py charset 6 8 -f charsets.cfg mixalpha-numeric
  python wlf.py charset --create-charset my_charsets.cfg
  python wlf.py pattern -t "XX{cod}@corp.example.com" --vars cod=1200-1300
  python wlf.py profile
  python wlf.py profile --name "PessoaX" --nick "robotx" --birth 15/03/1990
  python wlf.py profile --profile-file target.yaml -o wordlist.lst
  python wlf.py profile --year-start 2000 --year-end 2026 --suffix-range 00-99
  python wlf.py corp
  python wlf.py corp-users --domain acme.example --file employees.txt -o users.lst
  python wlf.py corp-users --domain acme.example --search "EmpresaXpto" --passwords -o combo.lst
  python wlf.py corp-users --domain acme.example --names "PessoaX,PersonY" --combo -o combo.lst
  python wlf.py corp-users --domain acme.example --subdomain corp-ad -o admins.lst
  python wlf.py phone --country brazil --state SP --type mobile -o phones_sp.lst
  python wlf.py phone --country usa --state NY --formats e164,local -o phones_ny.lst
  python wlf.py phone --ddi 55 --ddd 11 --pattern "9XXXX-XXXX" -o custom.lst
  python wlf.py scrape https://site.com -d 2 --emails --no-stopwords
  python wlf.py scrape https://site.com --proxy http://127.0.0.1:8080
  python wlf.py scrape https://site.com --user-agent "Mozilla/5.0" --header "X-Token: abc"
  python wlf.py ocr image.png -o wordlist.txt
  python wlf.py extract report.pdf spreadsheet.xlsx -o extracted.txt
  python wlf.py leet admin -m aggressive
  python wlf.py leet password -m custom --custom-map "a=@,4;s=$;e=3"
  python wlf.py xor --brute 1a2b3c4d
  python wlf.py analyze wordlist.lst --top 30
  python wlf.py analyze wordlist.lst --masks --format json -o stats.json
  python wlf.py analyze wordlist.lst --base-words --base-output bases.lst
  python wlf.py merge l1.lst l2.lst --no-numeric --sort alpha -o merged.lst
  python wlf.py dns -w words.lst -d acme.example
  python wlf.py dns -d acme.example --template-file patterns.yaml -w words.lst
  python wlf.py dns --domain-list domains.txt -w words.lst -o subdomains.lst
  python wlf.py dns -d acme.example --match-regex "^api" --filter-regex "test"
  python wlf.py pharma --codes 1200-1250 -o pharma_passwords.lst
  python wlf.py sanitize wordlist.lst --min-len 8 --sort alpha --inplace
  python wlf.py sanitize list.lst --filter "^[a-zA-Z]" --exclude "\\d{3,}$" -o clean.lst
  python wlf.py sanitize list.lst --min-len 6 --max-len 20 --sort length -o output.lst
  python wlf.py reverse list.lst -o reversed.lst
  python wlf.py reverse list.lst --inplace
  python wlf.py mangle wordlist.lst --rules capitalize,append_num -o mangled.lst
  python wlf.py mangle wordlist.lst --list-rules
  python wlf.py scrape https://site.com --with-numbers --capture-paths
  python wlf.py scrape --urls-file urls.txt -d 2 -o scraped.lst
  python wlf.py analyze list.lst --format markdown -o report.md
  python wlf.py sanitize list.lst --strip-control --sort frequency -o clean.lst
  python wlf.py --limit 100000 charset 6 8 abc123 -o limited.lst
  python wlf.py --timeout 60 profile -o timed.lst
""",
    )
    parser.add_argument("--version", action="version", version=f"wlf.py {VERSION}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument(
        "--lang", metavar="LOCALE", default=None,
        help=(
            "Language/locale for generated tokens and interactive prompts: "
            "en (default) | pt-br | pt-pt | es. "
            "Controls month names, zodiac sign names, and UI language in the wizard. "
            "When omitted, defaults to 'en' (or the YAML locale: field if present)."
        ),
    )

    # ── Global compute / threading / ML args ──────────────────────────────────
    parser.add_argument(
        "--threads", "-T", metavar="N", type=int, default=5,
        help=(
            "Number of worker threads for parallel generation (default: 5, range: 1-300). "
            "Warning at >50, alert at >100, critical at >200."
        ),
    )
    parser.add_argument(
        "--compute", metavar="MODE", default="auto",
        choices=["auto", "cpu", "gpu", "cuda", "rocm", "mps", "hybrid"],
        help=(
            "Compute backend for ML operations: "
            "auto (default) | cpu | gpu | cuda | rocm | mps | hybrid. "
            "'auto' selects the best available GPU, falls back to CPU."
        ),
    )
    parser.add_argument(
        "--no-ml", dest="no_ml_global", action="store_true", default=False,
        help=(
            "Disable ML-based ranking globally for all subcommands. "
            "When set, all modules run in rule-based mode regardless of "
            "per-command --no-ml flags."
        ),
    )
    parser.add_argument(
        "--limit", "-L", metavar="N", type=int, default=0,
        help=(
            "Global limit: stop after writing N entries (default: 0 = unlimited). "
            "Applies to all generation and extraction commands."
        ),
    )
    parser.add_argument(
        "--timeout", metavar="SECS", type=int, default=0,
        help=(
            "Global timeout: stop after SECS seconds of execution (default: 0 = unlimited). "
            "Applies to all generation commands."
        ),
    )
    parser.add_argument(
        "--min-len", dest="global_min_len", metavar="N", type=int, default=0,
        help=(
            "Global minimum entry length (default: 0 = no filter). "
            "Entries shorter than N are discarded from all output. "
            "Combined with per-command limits: most restrictive bound applies. "
            "Example: --min-len 8 keeps only entries with 8+ characters."
        ),
    )
    parser.add_argument(
        "--max-len", dest="global_max_len", metavar="N", type=int, default=0,
        help=(
            "Global maximum entry length (default: 0 = no filter). "
            "Entries longer than N are discarded from all output. "
            "Combined with per-command limits: most restrictive bound applies. "
            "Example: --max-len 16 discards entries longer than 16 characters."
        ),
    )
    parser.add_argument(
        "--ram-budget-pct", dest="ram_budget_pct", type=float, default=50.0,
        help="Stop generation when free RAM falls below (100-PCT)%% of total (default: 50).",
    )
    parser.add_argument(
        "--vram-budget-mb", dest="vram_budget_mb", type=int, default=4096,
        help="Soft VRAM budget for GPU batch sizing (default: 4096).",
    )
    parser.add_argument(
        "--chunk-lines", dest="chunk_lines", type=int, default=0,
        help="Rotate -o file every N lines (0 = off).",
    )
    parser.add_argument(
        "--chunk-bytes", dest="chunk_bytes", type=int, default=0,
        help="Rotate -o file every N bytes (0 = off).",
    )
    parser.add_argument(
        "--stream", dest="stream_global", action="store_true",
        help="Flush each line (stdout/file) for real-time piping to hashcat/etc.",
    )
    parser.add_argument(
        "--safe-default-limit", dest="safe_default_limit", action="store_true",
        help="If --limit is 0, cap at 5,000,000 candidates (nuclear-safe default).",
    )
    parser.add_argument(
        "--checkpoint", dest="checkpoint", action="store_true",
        help="Auto-save session checkpoint every 100k candidates (resumable).",
    )
    parser.add_argument(
        "--resume", dest="resume_id", metavar="SESSION_ID",
        help="Resume a previously checkpointed session by ID.",
    )

    sub = parser.add_subparsers(dest="command", help="Operation mode")

    # ── charset ───────────────────────────────────────────────────────────
    p_cs = sub.add_parser("charset", help="Generate by charset and length")
    p_cs.add_argument("min_len", nargs="?", type=int, default=6, help="Minimum length (also fixed length for --constrained)")
    p_cs.add_argument("max_len", nargs="?", type=int, default=8, help="Maximum length")
    p_cs.add_argument("charset", nargs="?", default="lalpha",
                       help="Charset: built-in name or direct character string")
    p_cs.add_argument("-f", "--charset-file", dest="charset_file", help=".cfg charset file")
    p_cs.add_argument("-p", "--pattern", help="Pattern with Crunch-style placeholders (@,%%,^,...)")
    p_cs.add_argument("--mask", metavar="MASK",
                       help="Hashcat-style mask (e.g. ?u?l?l?d?d?s - ?u=upper ?l=lower ?d=digit ?s=special ?a=all)")
    p_cs.add_argument("--custom-charset1", dest="custom_charset1", metavar="CHARS",
                       help="Custom charset for ?1 placeholder in mask")
    p_cs.add_argument("--digits", dest="n_digits", type=int, default=0,
                       help="Exact digit count (constrained composition mode)")
    p_cs.add_argument("--lower", dest="n_lower", type=int, default=0,
                       help="Exact lowercase count (constrained composition mode)")
    p_cs.add_argument("--upper", dest="n_upper", type=int, default=0,
                       help="Exact uppercase count (constrained composition mode)")
    p_cs.add_argument("--special", dest="n_special", type=int, default=0,
                       help="Exact special char count (constrained composition mode)")
    p_cs.add_argument("--create-charset", dest="create_charset", metavar="FILE",
                       help="Wizard to create a charset file")
    p_cs.add_argument("-o", "--output", help="Output file")

    # ── pattern ───────────────────────────────────────────────────────────
    p_pt = sub.add_parser("pattern", help="Generate by template with variables")
    p_pt.add_argument("-t", "--template", help="Template (e.g. XX{cod}@corp.example.com)")
    p_pt.add_argument("-f", "--template-file", dest="template_file", help="Template file")
    p_pt.add_argument("--vars", nargs="+", metavar="KEY=VALUE",
                       help="Variables (e.g. cod=1200-1300 company=BrandX,CorpX)")
    p_pt.add_argument("-o", "--output", help="Output file")

    # ── profile ───────────────────────────────────────────────────────────
    p_pr = sub.add_parser("profile", help="Interactive personal target profiling")
    p_pr.add_argument("--name", help="Target full name")
    p_pr.add_argument("--nick", help="Nickname or alias")
    p_pr.add_argument("--birth", help="Date of birth (dd/mm/yyyy, ddmmyyyy, yyyy, or age)")
    p_pr.add_argument("--profile-file", dest="profile_file", metavar="FILE",
                       help="Load profile from YAML file (non-interactive mode)")
    p_pr.add_argument("--year-start", dest="year_start", type=int, metavar="YYYY",
                       help="Include year range from this year (e.g. 2000)")
    p_pr.add_argument("--year-end", dest="year_end", type=int, metavar="YYYY",
                       help="Include year range to this year (e.g. 2026)")
    p_pr.add_argument("--suffix-range", dest="suffix_range", metavar="START-END",
                       help="Append numeric suffix range (e.g. 00-99 or 1-9999)")
    p_pr.add_argument("--leet", default=None,
                       choices=["basic", "medium", "aggressive", "none"],
                       help="Leet speak mode (default: from profile YAML or basic)")
    p_pr.add_argument("--surname", help="Surname (separate from first name, CUPP parity)")
    p_pr.add_argument("--old-passwords", dest="old_passwords", nargs="+", metavar="PWD",
                       help="Known old passwords to mutate (elpscrk parity)")
    p_pr.add_argument("--depth", type=int, default=3, choices=[3, 4, 5],
                       help="Permutation depth: 3 (default), 4 (enhanced), 5 (max BEWGor)")
    p_pr.add_argument("--parents", nargs="+", metavar="NAME",
                       help="Parent names (BEWGor parity)")
    p_pr.add_argument("--siblings", nargs="+", metavar="NAME",
                       help="Sibling names (BEWGor parity)")
    p_pr.add_argument("--engines", metavar="SPEC",
                       help=(
                           "Engine selection: preset name (light/medium/potent/nuclear), "
                           "numeric IDs (1,3,5), range (1-10), or 'all'. "
                           "Skips interactive engine menu when provided."
                       ))
    p_pr.add_argument("--max-candidates", dest="max_candidates", type=int, default=0, metavar="N",
                       help="Hard limit on generated candidates (0 = unlimited)")
    p_pr.add_argument("--timeout", dest="timeout_secs", type=float, default=0.0, metavar="SECS",
                       help="Pipeline timeout in seconds (0 = no timeout)")
    p_pr.add_argument("-o", "--output", help="Output file")

    # ── corp ──────────────────────────────────────────────────────────────
    p_co = sub.add_parser("corp", help="Interactive corporate target profiling")
    p_co.add_argument("--leet", default="basic",
                       choices=["basic", "medium", "aggressive", "none"],
                       help="Leet speak mode")
    p_co.add_argument("-o", "--output", help="Output file")

    # ── corp-users ────────────────────────────────────────────────────────
    p_cu = sub.add_parser(
        "corp-users",
        help="Generate corporate domain usernames and passwords",
        description=(
            "Generate corporate username/password lists from employee names.\n\n"
            "Name sources (choose one or combine):\n"
            "  --file       Load names from txt/csv/xlsx/pdf file\n"
            "  --search     Search online via Google dorks (no API needed)\n"
            "  --names      Comma-separated names inline\n\n"
            "LinkedIn API (optional):\n"
            "  Set LINKEDIN_RAPIDAPI_KEY env var to enable API-based search.\n"
            "  Without it, Google dorks are used automatically.\n\n"
            "Username patterns generated (default separator: '.'; use --separators to change):\n"
            "  firstname.lastname  f.lastname  flastname  lastname.firstname\n"
            "  firstname  lastname  firstnamel  initials  and 15+ more\n\n"
            "Examples:\n"
            "  wlf.py corp-users --domain acme.example --file employees.txt\n"
            "  wlf.py corp-users --domain acme.example --search 'BrandX'\n"
            "  wlf.py corp-users --domain acme.example --names 'PessoaX,PersonY'\n"
            "  wlf.py corp-users --domain acme.example --file names.txt --combo -o combo.lst\n"
            "  wlf.py corp-users --domain acme.example --subdomain corp-ad -o admins.lst\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_cu.add_argument("--domain", default="",
                       help="Company domain (e.g. acme.example)")
    p_cu.add_argument("--company", default="",
                       help="Company trade name (for passwords). Defaults to domain prefix.")
    # Name sources
    p_cu.add_argument("--file", metavar="FILE",
                       help="File with employee names (txt/csv/xlsx/pdf/docx)")
    p_cu.add_argument("--search", metavar="COMPANY_NAME",
                       help="Search online for employee names (Google dorks)")
    p_cu.add_argument("--names", metavar="NAME1,NAME2,...",
                       help="Comma-separated full names inline")
    p_cu.add_argument("--max-results", dest="max_results", type=int, default=50,
                       help="Max online search results (default: 50)")
    p_cu.add_argument("--no-api", dest="no_api", action="store_true",
                       help="Skip LinkedIn API even if LINKEDIN_RAPIDAPI_KEY is set")
    # Username options
    p_cu.add_argument("--separators", metavar="SEP",
                       help=(
                           "Username separator(s) used between name parts. "
                           "Default: '.' (dot only). "
                           "Examples: --separators _ | --separators .,_ | "
                           "--separators all (uses . _ - and empty) | "
                           "--separators none (no separator)."
                       ))
    p_cu.add_argument("--subdomain", metavar="SUB1,SUB2",
                       help="Subdomain(s) for admin patterns (e.g. corp-ad,webmail)")
    p_cu.add_argument("--no-users", dest="no_users", action="store_true",
                       help="Skip username generation (only passwords or combo)")
    p_cu.add_argument("--no-at", dest="no_at", action="store_true",
                       help="Omit @domain suffix from usernames")
    # Password and combo options
    p_cu.add_argument("--passwords", action="store_true",
                       help="Also generate password list")
    p_cu.add_argument("--combo", action="store_true",
                       help="Generate user:password combo list")
    p_cu.add_argument("--year-start", dest="year_start", type=int, default=2020,
                       help="Password year range start (default: 2020)")
    p_cu.add_argument("--year-end", dest="year_end", type=int, default=2026,
                       help="Password year range end (default: 2026)")
    p_cu.add_argument("-o", "--output", help="Output file")
    p_cu.add_argument(
        "--no-ml", dest="use_ml", action="store_false", default=True,
        help="Disable ML-based ranking (use original rule-based order)",
    )

    # ── phone ─────────────────────────────────────────────────────────────
    p_ph2 = sub.add_parser("phone", help="Generate phone number wordlists")
    p_ph2.add_argument("--country", help="Country name (e.g. brazil, usa, uk)")
    p_ph2.add_argument("--state", help="State/region code (e.g. SP, NY)")
    p_ph2.add_argument("--ddi", help="Manual DDI override (e.g. 55)")
    p_ph2.add_argument("--ddd", help="Manual DDD/area code override (e.g. 11)")
    p_ph2.add_argument("--type", dest="type", default="both",
                        choices=["mobile", "landline", "both"],
                        help="Phone type to generate")
    p_ph2.add_argument("--pattern", dest="pattern",
                        help="Custom digit pattern (X=any digit, e.g. '9XXXX-XXXX')")
    p_ph2.add_argument("--formats", dest="formats", default="e164,local",
                        help="Output formats: e164,local,bare (comma-sep, default: e164,local)")
    p_ph2.add_argument("--suffix", dest="suffix",
                        help="Append suffix to each generated number (pnwgen parity)")
    p_ph2.add_argument("--prefix-file", dest="prefix_file", metavar="FILE",
                        help="File with one prefix per line (pnwgen multi-prefix mode)")
    p_ph2.add_argument("--digit-length", dest="digit_length", type=int, metavar="N",
                        help="Override digit count for brute-force (4-10, pnwgen parity)")
    p_ph2.add_argument("-o", "--output", help="Output file")

    # ── scrape ────────────────────────────────────────────────────────────
    p_sc = sub.add_parser("scrape", help="Web scraping wordlist extraction")
    p_sc.add_argument("url", help="Target URL")
    p_sc.add_argument("-d", "--depth", type=int, default=2, help="Crawl depth (default: 2)")
    p_sc.add_argument("--min-word", type=int, default=6, dest="min_word",
                       help="Minimum word length to extract (default: 6)")
    p_sc.add_argument("--max-word", type=int, default=32, dest="max_word",
                       help="Maximum word length to extract (default: 32)")
    p_sc.add_argument("--emails", action="store_true", help="Extract email addresses")
    p_sc.add_argument("--meta", action="store_true", help="Extract metadata (Author, Generator)")
    p_sc.add_argument("--auth", help="HTTP Basic Auth (user:password)")
    p_sc.add_argument("--proxy", help="HTTP/SOCKS proxy URL (e.g. http://127.0.0.1:8080)")
    p_sc.add_argument("--user-agent", dest="user_agent",
                       help="Custom User-Agent string")
    p_sc.add_argument("--header", dest="headers", action="append", metavar="NAME:VALUE",
                       help="Extra HTTP header (can be repeated)")
    p_sc.add_argument("--no-stopwords", dest="no_stopwords", action="store_true",
                       help="Exclude common EN/PT-BR stop-words from output")
    p_sc.add_argument("--stopwords-file", dest="stopwords_file", metavar="FILE",
                       help="Custom stop-words file (one word per line)")
    p_sc.add_argument("--delay", type=float, default=0.5,
                       help="Delay between requests in seconds (default: 0.5)")
    p_sc.add_argument("--with-numbers", dest="with_numbers", action="store_true",
                       help="Include words containing digits (normally excluded)")
    p_sc.add_argument("--with-spaces", dest="with_spaces", action="store_true",
                       help="Include multi-word phrases (space-separated tokens)")
    p_sc.add_argument("--urls-file", dest="urls_file", metavar="FILE",
                       help="File with one URL per line (multi-URL scraping mode)")
    p_sc.add_argument("--capture-paths", dest="capture_paths", action="store_true",
                       help="Extract URL path segments as additional words")
    p_sc.add_argument("--capture-subdomains", dest="capture_subdomains", action="store_true",
                       help="Extract subdomain labels as additional words")
    p_sc.add_argument("--include-js", dest="include_js", action="store_true",
                       help="Include words from JavaScript content (cewler parity)")
    p_sc.add_argument("--include-css", dest="include_css", action="store_true",
                       help="Include words from CSS content (cewler parity)")
    p_sc.add_argument("--include-pdf", dest="include_pdf", action="store_true",
                       help="Extract text from PDF files found during crawl (requires pypdf)")
    p_sc.add_argument("--lowercase", action="store_true",
                       help="Lowercase all extracted words")
    p_sc.add_argument("--subdomain-strategy", dest="subdomain_strategy",
                       choices=["exact", "children", "all"], default="exact",
                       help="Subdomain crawl scope: exact (default), children, all")
    p_sc.add_argument("--output-emails", dest="output_emails", metavar="FILE",
                       help="Write extracted emails to separate file")
    p_sc.add_argument("--output-urls", dest="output_urls", metavar="FILE",
                       help="Write visited URLs to separate file")
    p_sc.add_argument("--stream", action="store_true",
                       help="Flush output after each page (real-time streaming, requires -o)")
    p_sc.add_argument("-o", "--output", help="Output file")

    # ── ocr ───────────────────────────────────────────────────────────────
    p_oc = sub.add_parser("ocr", help="Extract text from image via OCR")
    p_oc.add_argument("image", help="Image path")
    p_oc.add_argument("--lang", default="pt,en", help="OCR languages (default: pt,en)")
    p_oc.add_argument("-o", "--output", help="Output file")

    # ── extract ───────────────────────────────────────────────────────────
    p_ex = sub.add_parser("extract", help="Extract wordlist from files")
    p_ex.add_argument("files", nargs="+", help="Input files (max 50)")
    p_ex.add_argument("--min-len", type=int, default=4, dest="min_len")
    p_ex.add_argument("--max-len", type=int, default=64, dest="max_len")
    p_ex.add_argument("-o", "--output", help="Output file")

    # ── leet ─────────────────────────────────────────────────────────────
    p_mut = sub.add_parser(
        "mutate",
        help="Generate mutations from an existing password (case, leet, prefix, suffix)",
        description=(
            "Given an existing password, generate all mutations:\n"
            "case variants, leet substitutions, reversed, duplicated,\n"
            "vowels stripped, and cartesian product with prefixes/suffixes.\n\n"
            "Examples:\n"
            "  wlf.py mutate \"1q2w3e4r\"\n"
            "  wlf.py mutate \"minhasenha\" --leet-mode basic --min-len 8\n"
            "  wlf.py mutate \"abc123\" --prefixes _,! --suffixes @0x90,#0x90,EMPTY\n"
            "  wlf.py mutate \"nerd_trilha\" --titlecase --suffixes '0724!,@0724!'\n"
            "  wlf.py mutate \"senha\" --leet-mode none -o mutations.lst\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_mut.add_argument("password", help="Existing password to mutate")
    p_mut.add_argument(
        "--leet-mode", dest="leet_mode", default="all",
        choices=["basic", "v2", "v3", "all", "none"],
        help="Leet substitution table (default: all)",
    )
    p_mut.add_argument(
        "--prefixes", metavar="P1,P2,...",
        help="Extra prefixes (comma-separated). Use EMPTY for empty string.",
    )
    p_mut.add_argument(
        "--suffixes", metavar="S1,S2,...",
        help="Extra suffixes (comma-separated). Use EMPTY for empty string.",
    )
    p_mut.add_argument("--min-len", dest="min_len", type=int, default=1,
                       help="Minimum result length (default: 1)")
    p_mut.add_argument("--max-len", dest="max_len", type=int, default=128,
                       help="Maximum result length (default: 128)")
    p_mut.add_argument("--titlecase", action="store_true",
                       help="Also seed a per-token CamelCase variant of the base (e.g. nerd_trilha -> Nerd_Trilha)")
    p_mut.add_argument("-o", "--output", help="Output file")

    # ── num2text ──────────────────────────────────────────────────────────
    p_n2t = sub.add_parser(
        "num2text",
        help="Convert digits to text words and generate case/leet/separator variants",
        description=(
            "Converts a number (up to 12 digits) into its digit-by-digit word\n"
            "representation and generates multiple case, leet and separator variants.\n\n"
            "Language codes accepted:\n"
            "  en / en-us / en-gb  - English (default)    one, two, three, ...\n"
            "  pt / pt-pt          - European Portuguese   um, dois, tres, ...\n"
            "  br / pt-br          - Brazilian Portuguese  um/uma, dois/duas, tres, ...\n"
            "  es / es-es / es-mx  - Spanish               uno, dos, tres, ...\n\n"
            "Examples:\n"
            "  wlf num2text --number 123\n"
            "  wlf num2text --number 123 --lang pt\n"
            "  wlf num2text --number 123 --lang br\n"
            "  wlf num2text --number 123 --lang es\n"
            "  wlf num2text --number 1206 --lang en --separators -,_,@\n"
            "  wlf num2text --range 0-9999 --lang en -o numbers.lst\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_n2t.add_argument("--number", metavar="N",
                       help="Single number to convert (up to 12 digits)")
    p_n2t.add_argument("--range", metavar="START-END",
                       help="Range of numbers to convert (e.g. 0-9999)")
    p_n2t.add_argument("--lang", metavar="LANG", default="en",
                       help="Digit language: en (default), pt, br, es - also: en-us, pt-br, es-mx, etc.")
    p_n2t.add_argument("--separators", metavar="SEP1,SEP2,...",
                       help="Word separators (default: \"\", -, _, ., @, #, !)")
    p_n2t.add_argument("--no-leet", action="store_true", dest="no_leet",
                       help="Skip leet substitutions")
    p_n2t.add_argument("--min-len", type=int, default=0, dest="min_len",
                       help="Minimum entry length")
    p_n2t.add_argument("--max-len", type=int, default=0, dest="max_len",
                       help="Maximum entry length")
    p_n2t.add_argument("-o", "--output", help="Output file")

    p_phrase = sub.add_parser(
        "phrase",
        help="Generate passwords from phrase initials (acrostic mutations + @0x90 style)",
        description=(
            "Extract the first letter of each word in a phrase and generate\n"
            "password variants with case mutations, leet substitutions, and\n"
            "prefix/suffix combinations, including hacker patterns (@0x90, #0x90).\n\n"
            "PT-BR: 'mais' is replaced by '+' (common informal shorthand).\n\n"
            "Examples:\n"
            "  wlf.py phrase \"é mais fácil pedir do que tentar quebrar\"\n"
            "  wlf.py phrase \"minha empresa segura\" --suffixes @0x90,#0x90\n"
            "  wlf.py phrase \"apenas um teste\" --prefixes _,__ -o out.lst\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_phrase.add_argument("phrase", help="Input phrase")
    p_phrase.add_argument(
        "--prefixes", metavar="P1,P2,...",
        help="Extra prefixes (comma-separated). Use EMPTY for empty string.",
    )
    p_phrase.add_argument(
        "--suffixes", metavar="S1,S2,...",
        help="Extra suffixes (comma-separated). Use EMPTY for empty string.",
    )
    p_phrase.add_argument("-o", "--output", help="Output file")

    p_lt = sub.add_parser("leet", help="Leet speak variants")
    p_lt.add_argument("word", help="Base word")
    p_lt.add_argument("-m", "--mode", default="basic",
                       choices=["basic", "medium", "aggressive", "custom"],

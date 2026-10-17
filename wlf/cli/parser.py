"""CLI argument parser (argparse configuration)."""
from __future__ import annotations

import argparse

from wlf.cli.context import VERSION


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
            "Supports QWERTY, AZERTY, QWERTZ, Dvorak, and numpad layouts.\n\n"
            "Examples:\n"
            "  wlf.py kwalk --min-len 6 --max-len 10\n"
            "  wlf.py kwalk --layout qwerty,numpad --no-shift\n"
            "  wlf.py kwalk --max-changes 2 --start-chars qaz1\n"
            "  wlf.py kwalk --list-layouts"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_kw.add_argument("--layout", default="qwerty",
                       help="Comma-separated layout names (default: qwerty)")
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
        help="Alias for score — explain a candidate",
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

    p_pbmp = sub.add_parser(
        "pbmp",
        help="Full PBMP strategy distribution for a profile",
        description=(
            "Print weighted engine plan (History/Context/Behavior/Population).\n\n"
            "Examples:\n"
            "  wlf.py pbmp --n-engines 8\n"
            "  wlf.py pbmp --profile-file alvo.yaml"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_pbmp.add_argument("--profile-file", dest="profile_file", metavar="FILE",
                        help="JSON/YAML profile")
    p_pbmp.add_argument("--n-engines", dest="n_engines", type=int, default=5,
                        help="Top strategies to show (default: 5)")

    p_evl = sub.add_parser(
        "evolve",
        help="Evolutionary generation (genetic / MAP-Elites)",
        description=(
            "Population-based candidate search.\n\n"
            "Examples:\n"
            "  wlf.py --limit 2000 evolve --mode genetic -o ga.lst\n"
            "  wlf.py evolve --mode map-elites --seed-file seeds.txt --limit 5000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_evl.add_argument("--mode", choices=["genetic", "map-elites"], default="genetic")
    p_evl.add_argument("--seed-file", dest="seed_file", metavar="FILE",
                       help="Seed wordlist to initialize population")
    p_evl.add_argument("-o", "--output", help="Output file")

    p_ge = sub.add_parser(
        "graph-expand",
        help="Graph neighbourhood expansion from a seed corpus",
        description=(
            "Expand transformations around seed passwords.\n\n"
            "Examples:\n"
            "  wlf.py --limit 5000 graph-expand seeds.txt -o graph.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ge.add_argument("corpus_file", metavar="CORPUS", help="Seed corpus file")
    p_ge.add_argument("-o", "--output", help="Output file")

    p_tm = sub.add_parser(
        "temporal-model",
        help="Temporal drift generation across years",
        description=(
            "Evolve seed styles from base_year toward target_year.\n\n"
            "Examples:\n"
            "  wlf.py temporal-model --seed-file seeds.txt --base-year 2019 --target-year 2026"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_tm.add_argument("--seed-file", dest="seed_file", metavar="FILE")
    p_tm.add_argument("--base-year", dest="base_year", type=int, default=2019)
    p_tm.add_argument("--target-year", dest="target_year", type=int, default=2026)
    p_tm.add_argument("-o", "--output", help="Output file")

    p_dpc = sub.add_parser(
        "domain-pcfg",
        help="Domain-specific PCFG (corporate/healthcare/finance/...)",
        description=(
            "Sector-biased PCFG-style expansion.\n\n"
            "Examples:\n"
            "  wlf.py --limit 5000 domain-pcfg --sector healthcare -o hc.lst\n"
            "  wlf.py domain-pcfg --sector finance --corpus-file corp.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dpc.add_argument(
        "--sector",
        default="generic",
        help="Sector label (default: generic)",
    )
    p_dpc.add_argument("--corpus-file", dest="corpus_file", metavar="FILE",
                       help="Optional domain corpus for terminals")
    p_dpc.add_argument("-o", "--output", help="Output file")

    p_plg = sub.add_parser(
        "plugin",
        help="List/run user plugins (~/.wlf/plugins/)",
        description=(
            "Plugin discovery and execution.\n\n"
            "Examples:\n"
            "  wlf.py plugin list\n"
            "  wlf.py --limit 1000 plugin run myplugin -o plug.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_plg.add_argument(
        "plugin_sub", nargs="?", default="list", choices=["list", "run"],
        help="Sub-command (default: list)",
    )
    p_plg.add_argument("plugin_name", nargs="?", default=None,
                       help="Plugin name for run")
    p_plg.add_argument("-o", "--output", help="Output file when running a plugin")

    p_vi = sub.add_parser(
        "vae-interp",
        help="VAE latent-space interpolation between two passwords",
        description=(
            "Requires optional [gpu]/neural] torch stack when using real VAE weights.\n\n"
            "Examples:\n"
            "  wlf.py vae-interp senha1 senha2 --steps 10"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_vi.add_argument("pw_from", help="Start password")
    p_vi.add_argument("pw_to", help="End password")
    p_vi.add_argument("--steps", type=int, default=10, help="Interpolation steps")
    p_vi.add_argument("-o", "--output", help="Output file")

    # ── test (credential testing pipeline) ──────────────────────────────────
    p_te = sub.add_parser(
        "test",
        help="Credential testing: generate wordlist + hashcat cracking",
        description=(
            "Generate a targeted wordlist and test it against a hash file.\n\n"
            "Examples:\n"
            "  wlf.py test --target hashes.txt\n"
            "  wlf.py test --target hashes.txt --model M2 --mode ntlm\n"
            "  wlf.py test --target hashes.txt --max-words 500000 --timeout 600"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_te.add_argument("--target", "-t", required=True, help="Hash file to crack")
    p_te.add_argument("--model", default="M2", help="Generation model (default: M2)")
    p_te.add_argument("--mode", help="Hash mode name or number (auto-detect if omitted)")
    p_te.add_argument("--max-words", dest="max_words", type=int, default=100000,
                      help="Max wordlist size (default: 100000)")
    p_te.add_argument("--timeout", type=int, default=300,
                      help="Hashcat timeout in seconds (default: 300)")
    p_te.add_argument("-o", "--output", default=".", help="Output directory for report")

    return parser


# ── Entrypoint ────────────────────────────────────────────────────────────────


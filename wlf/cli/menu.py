"""Interactive menu for wlf."""
from __future__ import annotations

import argparse
import sys

from wlf.cli.context import Fore, Style
from wlf.cli.utils import _info, _warn


MENU = f"""
{Fore.CYAN}=== MAIN MENU ==={Style.RESET_ALL}

  {Fore.GREEN}[1]{Style.RESET_ALL}  charset     - Generate by charset and length
  {Fore.GREEN}[2]{Style.RESET_ALL}  pattern     - Generate by template with variables
  {Fore.GREEN}[3]{Style.RESET_ALL}  profile     - Interactive personal target profiling
  {Fore.GREEN}[4]{Style.RESET_ALL}  corp        - Interactive corporate target profiling
  {Fore.GREEN}[5]{Style.RESET_ALL}  corp-users  - Corporate domain user/password generation
  {Fore.GREEN}[6]{Style.RESET_ALL}  phone       - Generate phone number wordlists
  {Fore.GREEN}[7]{Style.RESET_ALL}  scrape      - Web scraping wordlist extraction
  {Fore.GREEN}[8]{Style.RESET_ALL}  ocr         - Extract text from image via OCR
  {Fore.GREEN}[9]{Style.RESET_ALL}  extract     - Extract wordlist from files (pdf/xlsx/docx/img)
  {Fore.GREEN}[10]{Style.RESET_ALL} leet        - Leet speak variants (basic/medium/aggressive/custom)
  {Fore.GREEN}[11]{Style.RESET_ALL} xor         - XOR encryption / brute-force
  {Fore.GREEN}[12]{Style.RESET_ALL} analyze     - Statistical analysis of wordlist
  {Fore.GREEN}[13]{Style.RESET_ALL} merge       - Merge and deduplicate wordlists
  {Fore.GREEN}[14]{Style.RESET_ALL} dns         - DNS/subdomain fuzzing wordlist
  {Fore.GREEN}[15]{Style.RESET_ALL} pharma      - Brazilian pharmacy and health plan patterns
  {Fore.GREEN}[16]{Style.RESET_ALL} sanitize    - Clean wordlist (dedupe, sort, filter, remove blanks/#)
  {Fore.GREEN}[17]{Style.RESET_ALL} reverse     - Reverse line order (tac)
  {Fore.GREEN}[18]{Style.RESET_ALL} corp-prefixes - Corporate prefix username generation
  {Fore.GREEN}[19]{Style.RESET_ALL} train       - Train ML pattern model
  {Fore.GREEN}[20]{Style.RESET_ALL} sysinfo     - Show hardware profile and compute backend
  {Fore.GREEN}[21]{Style.RESET_ALL} mangle      - Apply hashcat-style mangling rules
  {Fore.GREEN}[22]{Style.RESET_ALL} default-creds - Query default credentials database (IoT/routers/SNMP)
  {Fore.GREEN}[23]{Style.RESET_ALL} isp-keygen    - ISP default WiFi password keyspace generator
  {Fore.GREEN}[24]{Style.RESET_ALL} phrase        - Phrase-initials password generator (@0x90 style)
  {Fore.GREEN}[25]{Style.RESET_ALL} mutate        - Mutate an existing password (case/leet/prefix/suffix)
  {Fore.GREEN}[26]{Style.RESET_ALL} num2text      - Convert digits to text words and generate variations
  {Fore.GREEN}[0]{Style.RESET_ALL}  Exit
"""



def interactive_menu() -> None:
    """Display and process the main interactive menu."""
    from wlf.cli.handlers import (
        cmd_charset, cmd_pattern, cmd_profile, cmd_corp, cmd_corp_users,
        cmd_phone, cmd_scrape, cmd_ocr, cmd_extract, cmd_leet, cmd_xor,
        cmd_analyze, cmd_merge, cmd_dns, cmd_pharma, cmd_sanitize,
        cmd_reverse, cmd_phrase, cmd_mutate,
    )

    print(MENU)
    choice = input(f"{Fore.CYAN}Select an option: {Style.RESET_ALL}").strip()

    if choice == "0":
        _info("Exiting wlf.py.")
        sys.exit(0)

    ns = argparse.Namespace(output=None)
    if choice != "3":
        ns.output = input("  Output file (Enter for stdout): ").strip() or None

    if choice == "1":
        ns.charset = input("  Charset (built-in name or chars): ").strip() or "lalpha"
        ns.min_len = int(input("  Min length: ").strip() or "6")
        ns.max_len = int(input("  Max length: ").strip() or "8")
        ns.charset_file = None
        ns.pattern = None
        ns.create_charset = None
        cmd_charset(ns)

    elif choice == "2":
        ns.template = input("  Template (e.g. XX{cod}@corp.example.com): ").strip()
        ns.template_file = None
        ns.vars = []
        while True:
            v = input("  Variable (name=value, Enter to stop): ").strip()
            if not v:
                break
            ns.vars.append(v)
        cmd_pattern(ns)

    elif choice == "3":
        ns.name = None
        ns.nick = None
        ns.birth = None
        cmd_profile(ns)

    elif choice == "4":
        ns.leet = input("  Leet mode (basic/medium/aggressive/none): ").strip() or "basic"
        cmd_corp(ns)

    elif choice == "5":
        # corp-users interactive - delegate entirely to wizard
        ns.domain = None
        cmd_corp_users(ns)

    elif choice == "6":
        ns.country = input("  Country (e.g. brazil, usa, uk): ").strip() or None
        ns.state = input("  State/region (e.g. SP, NY): ").strip() or None
        ns.ddi = input("  DDI override (or Enter): ").strip() or None
        ns.ddd = input("  DDD/area code override (or Enter): ").strip() or None
        ns.type = input("  Type [mobile/landline/both]: ").strip() or "both"
        ns.pattern = input("  Custom pattern (X=digit, or Enter): ").strip() or None
        ns.formats = input("  Formats (e164,local,bare - comma-sep): ").strip() or "e164,local"
        cmd_phone(ns)

    elif choice == "7":
        ns.url = input("  URL to crawl: ").strip()
        ns.depth = int(input("  Depth (default 2): ").strip() or "2")
        ns.min_word = int(input("  Min word length (6): ").strip() or "6")
        ns.max_word = int(input("  Max word length (32): ").strip() or "32")
        ns.emails = input("  Extract emails? [y/N]: ").strip().lower() in ("y", "yes")
        ns.meta = input("  Extract metadata? [y/N]: ").strip().lower() in ("y", "yes")
        ns.auth = None
        ns.delay = 0.5
        ns.proxy = None
        ns.user_agent = None
        ns.headers = None
        ns.no_stopwords = False
        ns.stopwords_file = None
        cmd_scrape(ns)

    elif choice == "8":
        ns.image = input("  Image path: ").strip()
        ns.lang = input("  OCR languages (default: pt,en): ").strip() or "pt,en"
        cmd_ocr(ns)

    elif choice == "9":
        files_raw = input("  Files (space-separated): ").strip()
        ns.files = files_raw.split()
        ns.min_len = int(input("  Min length (4): ").strip() or "4")
        ns.max_len = int(input("  Max length (64): ").strip() or "64")
        cmd_extract(ns)

    elif choice == "10":
        ns.word = input("  Base word: ").strip()
        ns.mode = input("  Mode (basic/medium/aggressive/custom): ").strip() or "basic"
        ns.custom_map = ""
        if ns.mode == "custom":
            ns.custom_map = input("  Mapping (e.g. a=@,4;t=7;s=$): ").strip()
        ns.max_results = int(input("  Max results (10000): ").strip() or "10000")
        cmd_leet(ns)

    elif choice == "11":
        sub = input("  [1] Brute-force  [2] Encrypt  [3] Decrypt: ").strip()
        ns.brute = None
        ns.encrypt = None
        ns.decrypt = None
        ns.key = None
        if sub == "1":
            ns.brute = input("  Hex string: ").strip()
        elif sub == "2":
            ns.encrypt = input("  Text to encrypt: ").strip()
            ns.key = input("  Key: ").strip()
        elif sub == "3":
            ns.decrypt = input("  Encrypted hex: ").strip()
            ns.key = input("  Key: ").strip()
        cmd_xor(ns)

    elif choice == "12":
        ns.wordlist = input("  Wordlist to analyze: ").strip()
        ns.top = int(input("  Top N (20): ").strip() or "20")
        ns.masks = input("  Run Hashcat mask analysis? [y/N]: ").strip().lower() in ("y", "yes")
        ns.base_words = False
        ns.base_output = None
        ns.format = "text"
        cmd_analyze(ns)

    elif choice == "13":
        files_raw = input("  Files to merge (space-separated): ").strip()
        ns.files = files_raw.split()
        ns.min_len = int(input("  Min length (6): ").strip() or "6")
        ns.max_len = int(input("  Max length (128): ").strip() or "128")
        ns.no_numeric = input("  Remove purely numeric? [y/N]: ").strip().lower() in ("y", "yes")
        ns.filter = None
        ns.no_dedupe = False
        ns.sort = input("  Sort (alpha/length/random or Enter to skip): ").strip() or None
        cmd_merge(ns)

    elif choice == "14":
        ns.domain = input("  Target domain: ").strip()
        ns.wordlist = input("  Words file (or Enter): ").strip() or None
        ns.words = []
        ns.template = None
        ns.template_file = None
        ns.domain_list = None
        ns.separator = None
        ns.match_regex = None
        ns.filter_regex = None
        ns.no_prefixes = False
        ns.no_suffixes = False
        cmd_dns(ns)

    elif choice == "15":
        ns.codes = input("  Store codes (e.g. 1200-1300 or 1200,1201, Enter for default): ").strip() or None
        cmd_pharma(ns)

    elif choice == "16":
        ns.wordlist = input("  Wordlist to sanitize: ").strip()
        ns.sort = input("  Sort (alpha/alpha-rev/length/length-rev/random or Enter): ").strip() or None
        min_raw = input("  Min length (Enter to skip): ").strip()
        max_raw = input("  Max length (Enter to skip): ").strip()
        ns.min_len = int(min_raw) if min_raw else None
        ns.max_len = int(max_raw) if max_raw else None
        ns.filter = input("  Include regex (Enter to skip): ").strip() or None
        ns.exclude = input("  Exclude regex (Enter to skip): ").strip() or None
        ns.keep_blank = False
        ns.keep_comments = False
        ns.no_dedupe = False
        ns.inplace = input("  Overwrite original? [y/N]: ").strip().lower() in ("y", "yes")
        if not ns.inplace:
            ns.output = input("  Output file (Enter for stdout): ").strip() or None
        cmd_sanitize(ns)

    elif choice == "17":
        ns.wordlist = input("  Wordlist to reverse: ").strip()
        ns.inplace = input("  Overwrite original? [y/N]: ").strip().lower() in ("y", "yes")
        if not ns.inplace:
            ns.output = input("  Output file (Enter for stdout): ").strip() or None
        cmd_reverse(ns)

    elif choice == "24":
        ns.phrase = input("  Phrase (e.g. 'é mais fácil pedir do que tentar quebrar'): ").strip()
        ns.prefixes = input("  Extra prefixes (comma-sep, EMPTY for '', or Enter): ").strip() or None
        ns.suffixes = input("  Extra suffixes (comma-sep, EMPTY for '', or Enter): ").strip() or None
        cmd_phrase(ns)

    elif choice == "25":
        ns.password = input("  Existing password to mutate: ").strip()
        ns.leet_mode = input("  Leet mode [basic/v2/v3/all/none] (default: all): ").strip() or "all"
        ns.prefixes = input("  Extra prefixes (comma-sep, EMPTY for '', or Enter to use defaults): ").strip() or None
        ns.suffixes = input("  Extra suffixes (comma-sep, EMPTY for '', or Enter to use defaults): ").strip() or None
        min_raw = input("  Min length (default: 1): ").strip()
        max_raw = input("  Max length (default: 128): ").strip()
        ns.min_len = int(min_raw) if min_raw.isdigit() else 1
        ns.max_len = int(max_raw) if max_raw.isdigit() else 128
        cmd_mutate(ns)

    else:
        _warn("Invalid option.")


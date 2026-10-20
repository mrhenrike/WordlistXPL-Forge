def cmd_phone(args: argparse.Namespace) -> None:
    """Handler for phone number wordlist generation."""
    from wlf_modules.phone_gen import (
        generate_phones,
        interactive_phone_wizard,
    )

    interactive = not any([
        getattr(args, "country", None),
        getattr(args, "ddi", None),
        getattr(args, "ddd", None),
    ])

    if interactive:
        params = interactive_phone_wizard()
    else:
        formats_raw = getattr(args, "formats", None) or "e164,local"
        params = {
            "country": getattr(args, "country", None),
            "state": getattr(args, "state", None),
            "ddi": getattr(args, "ddi", None),
            "ddd": getattr(args, "ddd", None),
            "phone_type": getattr(args, "type", "both"),
            "custom_pattern": getattr(args, "pattern", None),
            "output_formats": [f.strip() for f in formats_raw.split(",")],
        }

    suffix = getattr(args, "suffix", None) or ""
    prefix_file = getattr(args, "prefix_file", None)
    digit_length = getattr(args, "digit_length", None)

    if prefix_file:
        from wlf_modules.dns_wordlist import load_words_from_file
        prefixes = load_words_from_file(prefix_file)
        _info(f"Loaded {len(prefixes)} prefixes from {prefix_file}")
        pattern = "X" * (digit_length or 7)

        def _multi_prefix_gen() -> Generator[str, None, None]:
            for px in prefixes:
                px = px.strip().lstrip("#")
                if not px:
                    continue
                for num in generate_phones(
                    ddi="", ddd="",
                    custom_pattern=pattern,
                    output_formats=["bare"],
                ):
                    entry = px + num + suffix
                    yield entry

        count = _write_output(_multi_prefix_gen(), args.output)
        _ok(f"Generated: {count:,} phone entries (multi-prefix)")
        return

    if digit_length:
        params["custom_pattern"] = "X" * digit_length

    _info(f"Generating phone numbers [country={params.get('country') or 'custom'}]...")

    def _gen_with_suffix() -> Generator[str, None, None]:
        for num in generate_phones(**params):
            yield num + suffix if suffix else num

    count = _write_output(_gen_with_suffix(), args.output)
    _ok(f"Generated: {count:,} phone entries")



def cmd_scrape(args: argparse.Namespace) -> None:
    """Handler for web scraping mode."""
    from wlf_modules.web_scraper import DEFAULT_STOPWORDS, WebScraper

    auth = None
    if args.auth:
        parts = args.auth.split(":", 1)
        auth = (parts[0], parts[1]) if len(parts) == 2 else None

    # Parse extra headers (--header "Name: Value")
    extra_headers: dict[str, str] = {}
    for hdr in (getattr(args, "headers", None) or []):
        if ":" in hdr:
            k, v = hdr.split(":", 1)
            extra_headers[k.strip()] = v.strip()

    # Stop-words
    stopwords: set[str] = frozenset()  # type: ignore[assignment]
    if getattr(args, "no_stopwords", False):
        stopwords = DEFAULT_STOPWORDS  # type: ignore[assignment]
    stopwords_file = getattr(args, "stopwords_file", None)
    if stopwords_file:
        try:
            with open(stopwords_file, encoding="utf-8") as f:
                custom_sw = frozenset(line.strip().lower() for line in f if line.strip())
            stopwords = stopwords | custom_sw
            _info(f"Loaded {len(custom_sw)} custom stop-words from {stopwords_file}")
        except FileNotFoundError:
            _warn(f"Stop-words file not found: {stopwords_file}")

    with_numbers = getattr(args, "with_numbers", False)
    with_spaces = getattr(args, "with_spaces", False)
    capture_paths = getattr(args, "capture_paths", False)
    capture_subdomains = getattr(args, "capture_subdomains", False)
    include_js = getattr(args, "include_js", False)
    include_css = getattr(args, "include_css", False)
    include_pdf = getattr(args, "include_pdf", False)
    lowercase = getattr(args, "lowercase", False)
    subdomain_strategy = getattr(args, "subdomain_strategy", "exact")
    output_emails = getattr(args, "output_emails", None)
    output_urls = getattr(args, "output_urls", None)

    # Multi-URL mode
    urls_file = getattr(args, "urls_file", None)
    urls_to_crawl: list[str] = []
    if urls_file:
        try:
            with open(urls_file, encoding="utf-8") as uf:
                urls_to_crawl = [u.strip() for u in uf if u.strip() and not u.startswith("#")]
            _info(f"Loaded {len(urls_to_crawl)} URLs from {urls_file}")
        except FileNotFoundError:
            _err(f"URLs file not found: {urls_file}")
            return
    else:
        urls_to_crawl = [args.url]

    all_emails: set[str] = set()
    all_urls: list[str] = []

    total_count = 0
    for url in urls_to_crawl:
        if is_shutdown():
            break
        scraper = WebScraper(
            start_url=url,
            depth=args.depth,
            min_word_len=args.min_word,
            max_word_len=args.max_word,
            extract_emails=args.emails,
            extract_meta=args.meta,
            auth=auth,
            delay=args.delay,
            user_agent=getattr(args, "user_agent", None),
            proxy=getattr(args, "proxy", None),
            extra_headers=extra_headers or None,
            stopwords=stopwords if stopwords else None,  # type: ignore[arg-type]
            with_numbers=with_numbers,
            with_spaces=with_spaces,
            capture_paths=capture_paths,
            capture_subdomains=capture_subdomains,
            include_js=include_js,
            include_css=include_css,
            include_pdf=include_pdf,
            lowercase=lowercase,
            subdomain_strategy=subdomain_strategy,
        )
        _info(f"Crawling: {url} [depth={args.depth}]")
        if include_js:
            _info("Including JavaScript content")
        if include_css:
            _info("Including CSS content")
        if include_pdf:
            _info("Including PDF content")
        if getattr(args, "proxy", None):
            _info(f"Proxy: {args.proxy}")
        stream_mode = getattr(args, "stream", False)
        if stream_mode and not args.output:
            _warn("--stream requires -o/--output. Ignoring --stream.")
            stream_mode = False
        count = _write_output(scraper.crawl(), args.output, append=(total_count > 0), stream=stream_mode)
        total_count += count
        all_emails |= scraper.emails_found
        all_urls.extend(scraper.urls_visited)

    _ok(f"Extracted: {total_count:,} words from {len(urls_to_crawl)} URL(s)")

    if output_emails and all_emails:
        with open(output_emails, "w", encoding="utf-8", newline="\n") as ef:
            for email in sorted(all_emails):
                ef.write(email + "\n")
        _ok(f"Emails: {len(all_emails)} written to {output_emails}")

    if output_urls and all_urls:
        with open(output_urls, "w", encoding="utf-8", newline="\n") as uf:
            for u in all_urls:
                uf.write(u + "\n")
        _ok(f"URLs visited: {len(all_urls)} written to {output_urls}")



def cmd_ocr(args: argparse.Namespace) -> None:
    """Handler for OCR mode."""
    from wlf_modules.ocr_extractor import extract_from_image

    _info(f"Processing OCR: {args.image}")
    try:
        result = extract_from_image(args.image, lang=args.lang.split(","))
    except ImportError:
        _err("easyocr not installed. Run: pip install easyocr")
        return

    _ok(f"Extracted: {len(result['usernames'])} users, "
        f"{len(result['passwords'])} passwords, {len(result['words'])} words")

    all_tokens = result["usernames"] + result["passwords"] + result["words"]

    def gen() -> Generator[str, None, None]:
        yield from all_tokens

    count = _write_output(gen(), args.output)
    _ok(f"Total written: {count:,}")



def cmd_extract(args: argparse.Namespace) -> None:
    """Handler for file extraction mode."""
    from wlf_modules.file_extractor import extract_wordlist_from_files

    _info(f"Extracting from {len(args.files)} file(s)...")
    gen = extract_wordlist_from_files(
        args.files, min_len=args.min_len, max_len=args.max_len,
    )
    count = _write_output(gen, args.output)
    _ok(f"Extracted: {count:,} words")




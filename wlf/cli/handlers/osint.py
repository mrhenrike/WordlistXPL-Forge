"""Command handlers: osint."""
from __future__ import annotations

import argparse

from typing import Any, Generator

from wlf.cli.context import (
    Fore, Style, _GLOBAL_CTX, _TQDM, _tqdm, logger, is_shutdown, VERSION,
)
from wlf.cli.utils import (
    _info, _ok, _warn, _err, _write_output,
    _effective_len_bounds, _format_bytes, _check_disk_space,
    _confirm_large, _count_generator_entries,
    _profile_preview_and_confirm, _resolve_path, _load_profile_file,
)


def cmd_profile(args: argparse.Namespace) -> None:
    """Handler for personal profiling mode."""
    from wlf_modules.profiler import interactive_profile, resolve_profile_output

    # ── Resolve locale: CLI --lang > YAML locale > session default ────────────
    from wlf_modules.i18n import set_session_locale as _set_locale
    _cli_lang = getattr(args, "lang", None)
    if _cli_lang:
        _set_locale(_cli_lang)

    # ── Load from YAML file ──────────────────────────────────────────────────
    if getattr(args, "profile_file", None):
        from wlf_modules.profiler import load_profile_yaml
        try:
            profile = load_profile_yaml(args.profile_file)
            if not _cli_lang and profile.get("locale"):
                _set_locale(profile["locale"])
            _info(f"Profile loaded from: {args.profile_file}")
        except (FileNotFoundError, ImportError) as exc:
            _err(str(exc))
            return
    elif hasattr(args, "name") and args.name:
        from wlf_modules.profiler import parse_date_input
        birth_parsed = parse_date_input(getattr(args, "birth", "") or "") or (0, 0, 0)
        profile = {
            "full_name": args.name,
            "short_name": "",
            "nicknames": [],
            "birth_day": birth_parsed[0],
            "birth_month": birth_parsed[1],
            "birth_year": birth_parsed[2],
            "national_id": "",
            "phones": [],
            "location_city": "",
            "location_state": "",
            "location_country": "",
            "children": [],
            "pets": [],
            "social_handles": [],
            "keywords": [],
            "special_dates": [],
            "leet_mode": getattr(args, "leet", None) or "basic",
            "with_spaces": False,
            "min_len": 6,
            "max_len": 32,
            "include_specials": False,
        }
        if getattr(args, "nick", ""):
            profile["nicknames"] = [args.nick]
    else:
        profile = interactive_profile(
            preset_leet=getattr(args, "leet", None),
            preset_output=getattr(args, "output", None),
        )

    # ── Inject year-range / suffix-range from CLI ────────────────────────────
    if getattr(args, "year_start", None) and getattr(args, "year_end", None):
        profile["year_start"] = args.year_start
        profile["year_end"] = args.year_end
    if getattr(args, "suffix_range", None):
        try:
            parts = args.suffix_range.split("-")
            profile["suffix_range_start"] = int(parts[0])
            profile["suffix_range_end"] = int(parts[1])
            profile["suffix_range_zero_pad"] = len(parts[0]) if parts[0].startswith("0") else 0
        except (ValueError, IndexError):
            _warn(f"Invalid --suffix-range format '{args.suffix_range}', expected START-END (e.g. 00-99)")

    # ── Inject CUPP/elpscrk/BEWGor fields from CLI ──────────────────────────
    if getattr(args, "surname", None):
        profile["surname"] = args.surname
    if getattr(args, "old_passwords", None):
        profile["old_passwords"] = args.old_passwords
    if getattr(args, "depth", None):
        profile["depth"] = args.depth
    if getattr(args, "parents", None):
        profile["parents"] = args.parents
    if getattr(args, "siblings", None):
        profile["siblings"] = args.siblings

    # ── Inject engine/pipeline flags from CLI ───────────────────────────────
    _cli_engines = getattr(args, "engines", None)
    if _cli_engines:
        profile["engines"] = _cli_engines
    elif profile.get("_engine_ids"):
        # Promote interactive wizard selection to pipeline-compatible format
        profile["engines"] = ",".join(str(i) for i in profile["_engine_ids"])

    _max_cand = getattr(args, "max_candidates", 0)
    if _max_cand:
        profile["max_candidates"] = _max_cand
    _timeout = getattr(args, "timeout_secs", 0.0)
    if _timeout:
        profile["timeout_secs"] = _timeout

    leet_mode = getattr(args, "leet", None) or profile.get("leet_mode", "basic")
    profile["leet_mode"] = leet_mode

    output = resolve_profile_output(getattr(args, "output", None), profile)

    # Validate engine selection before expensive preview/pipeline
    if profile.get("engines") or profile.get("_engine_ids"):
        try:
            from wlf_modules.generation_engines import resolve_engines
            raw_eng = profile.get("engines") or ",".join(
                str(i) for i in profile.get("_engine_ids", [])
            )
            resolve_engines(str(raw_eng))
        except MemoryError as exc:
            _err(str(exc))
            return
        except ValueError as exc:
            _err(f"Invalid engine selection: {exc}")
            return

    # ── Pipeline execution ───────────────────────────────────────────────────
    try:
        from wlf_modules.pipeline_engine import run_profile_pipeline, ProfilePipeline, PipelineConfig
        _use_pipeline = True
    except ImportError:
        _use_pipeline = False

    if _use_pipeline:
        if output:
            profile["output_path"] = output
            # Quick preview using legacy generator before the heavy pipeline runs
            _preview_ok = True
            if profile.get("interactive_mode"):
                from wlf_modules.profiler import generate_from_profile
                preview = _profile_preview_and_confirm(profile, leet_mode, output)
                if preview is None:
                    return
            _info(f"Running generation pipeline [leet={leet_mode}, engines={profile.get('engines', 'default')}]...")
            try:
                result = run_profile_pipeline(profile, output_path=output)
                count = result.get("lines_written", 0)
                elapsed = result.get("elapsed_secs", 0)
                archive = result.get("archive", {})
                feedback = result.get("feedback", {})
                if count:
                    dest = archive.get("output_path") or output
                    _ok(f"Generated: {count:,} entries → {dest} [{elapsed}s]")
                    if feedback:
                        hit_rate = feedback.get("hit_rate", 0)
                        hits = feedback.get("hits", 0)
                        total = feedback.get("total", 0)
                        _info(f"Feedback: {hits}/{total} known targets found ({hit_rate:.1%} hit rate)")
                else:
                    _warn("No entries written.")
            except Exception as exc:
                _err(f"Pipeline error: {exc}")
        else:
            _info(f"Running generation pipeline [leet={leet_mode}] → stdout...")
            try:
                config = PipelineConfig.from_profile(profile)
                pipeline = ProfilePipeline(profile, config)
                count = _write_output(pipeline.run(), None)
                _ok(f"Generated: {count:,} entries (stdout - use -o or interactive output prompt to save)")
            except Exception as exc:
                _err(f"Pipeline error: {exc}")
    else:
        # Fallback to legacy generator when pipeline_engine is unavailable
        from wlf_modules.profiler import generate_from_profile
        if output:
            preview = _profile_preview_and_confirm(profile, leet_mode, output)
            if preview is None:
                return
            est_count, avg_len = preview
            _info(f"Generating wordlist from profile [leet={leet_mode}]...")
            gen = generate_from_profile(profile, leet_mode=leet_mode)
            count = _write_output(
                gen, output,
                estimate=est_count,
                min_len=int(profile.get("min_len", 0) or 0),
                max_len=int(profile.get("max_len", 0) or 0),
                avg_entry_len=max(1, int(avg_len)),
            )
            if count:
                _ok(f"Generated: {count:,} entries → {output}")
            else:
                _warn("No entries written.")
        else:
            _info(f"Generating wordlist from profile [leet={leet_mode}]...")
            gen = generate_from_profile(profile, leet_mode=leet_mode)
            count = _write_output(gen, None)
            _ok(f"Generated: {count:,} entries (stdout - use -o or interactive output prompt to save)")



def cmd_corp(args: argparse.Namespace) -> None:
    """Handler for corporate profiling mode."""
    from wlf_modules.corp_profiler import interactive_corp_profile, generate_from_corp_profile

    profile = interactive_corp_profile()
    leet_mode = getattr(args, "leet", "basic") or profile.get("leet_mode", "basic")
    _info(f"Generating corporate wordlist [leet={leet_mode}]...")
    gen = generate_from_corp_profile(profile, leet_mode=leet_mode)
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} entries")



def cmd_corp_users(args: argparse.Namespace) -> None:
    """Handler for corporate domain user/password generation."""
    from wlf_modules.domain_users import (
        interactive_domain_users_wizard,
        run_domain_users,
        collect_names_from_file,
        collect_names_online,
        generate_subdomain_admin_users,
        DOMAIN_SEPARATORS,
        ALL_DOMAIN_SEPARATORS,
    )

    params: dict[str, Any] = {}

    # ── Interactive mode (no --domain provided) ────────────────────────────
    if not getattr(args, "domain", None):
        params = interactive_domain_users_wizard()
    else:
        domain = args.domain
        company_name = getattr(args, "company", None) or domain.split(".")[0]
        names: list[str] = []

        # Collect names from file
        if getattr(args, "file", None):
            _info(f"Loading names from: {args.file}")
            try:
                names = collect_names_from_file(args.file)
                _ok(f"Loaded {len(names)} name(s) from file")
            except FileNotFoundError as exc:
                _err(str(exc))
                return

        # Collect names online (Google dorks + optional LinkedIn API)
        if getattr(args, "search", None):
            _info(f"Searching online for employees of '{args.search}'...")
            online = collect_names_online(
                args.search,
                domain=domain,
                max_results=getattr(args, "max_results", 50),
                use_linkedin_api=not getattr(args, "no_api", False),
            )
            _ok(f"Found {len(online)} name(s) online")
            names.extend(online)

        # Manual name list (args.names is a single string)
        if getattr(args, "names", None):
            raw_names = args.names if isinstance(args.names, str) else ",".join(args.names)
            names.extend([n.strip() for n in raw_names.split(",") if n.strip()])

        # Parse separators - default is "." only; user can supply custom list or "all"
        sep_raw = getattr(args, "separators", None)
        if sep_raw:
            if sep_raw.strip().lower() == "all":
                separators = ALL_DOMAIN_SEPARATORS
            elif sep_raw.strip().lower() == "none":
                separators = [""]
            else:
                separators = []
                for token in sep_raw.split(","):
                    t = token.strip()
                    if t.lower() in ("none", "empty", "''", '""'):
                        if "" not in separators:
                            separators.append("")
                    elif t:
                        if t not in separators:
                            separators.append(t)
                if not separators:
                    separators = DOMAIN_SEPARATORS
        else:
            separators = DOMAIN_SEPARATORS  # default: ["."]

        subdomains = []
        if getattr(args, "subdomain", None):
            subdomains = [s.strip() for s in args.subdomain.split(",") if s.strip()]

        year_start = int(getattr(args, "year_start", None) or 2020)
        year_end = int(getattr(args, "year_end", None) or 2026)

        params = {
            "domain": domain,
            "company_name": company_name,
            "names": names,
            "separators": separators,
            "subdomains": subdomains,
            "gen_users": not getattr(args, "no_users", False),
            "gen_passwords": getattr(args, "passwords", False),
            "gen_combo": getattr(args, "combo", False),
            "year_start": year_start,
            "year_end": year_end,
            "with_at_domain": not getattr(args, "no_at", False),
        }

    if not params.get("names") and not params.get("subdomains"):
        _warn("No names or subdomains provided. Use --file, --search, --names, or --subdomain.")
        return

    _info(
        f"Generating for domain: {params.get('domain')} | "
        f"names: {len(params.get('names', []))} | "
        f"subdomains: {len(params.get('subdomains', []))}"
    )

    # ── Threads ────────────────────────────────────────────────────────────────
    threads = _GLOBAL_CTX.get("threads", 5)

    # ── ML ranking ─────────────────────────────────────────────────────────────
    # Respects both per-command --no-ml and global --no-ml
    cmd_use_ml = getattr(args, "use_ml", True)
    global_ml  = _GLOBAL_CTX.get("use_ml", True)
    use_ml     = cmd_use_ml and global_ml

    ml_model = None
    if use_ml:
        try:
            from wlf_modules.ml_patterns import get_model, DEFAULT_MODEL_FILE
            if DEFAULT_MODEL_FILE.exists():
                ml_model = get_model()
                if ml_model.is_trained():
                    _info(f"ML model loaded ({ml_model._total_uid_samples:,} samples) - ranking by probability")
                else:
                    ml_model = None
        except Exception:
            ml_model = None

    # ── Parallel generation across multiple names ──────────────────────────────
    names_list = params.get("names", [])
    if threads > 1 and len(names_list) > 1:
        from wlf_modules.thread_pool import parallel_generate

        _info(f"Parallel generation: {threads} threads × {len(names_list)} names")

        single_name_params = []
        for name in names_list:
            p = dict(params)
            p["names"] = [name]
            single_name_params.append(p)

        def _gen_for_params(p: dict[str, Any]) -> Generator[Any, None, None]:
            return run_domain_users(p)

        gen = parallel_generate(_gen_for_params, single_name_params, threads=threads)
    else:
        gen = run_domain_users(params)

    if ml_model:
        domain = params.get("domain", "")
        candidates = list(gen)
        ranked     = ml_model.rank_and_yield(candidates, domain)
        count      = _write_output(ranked, args.output)
    else:
        count = _write_output(gen, args.output)

    _ok(f"Generated: {count:,} entries")



def cmd_phone(args: argparse.Namespace) -> None:
    """Handler for phone number wordlist generation."""
    from wlf_modules.phone_gen import (
        generate_phones, interactive_phone_wizard, estimate_count, COUNTRIES,
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
    from wlf_modules.web_scraper import WebScraper, DEFAULT_STOPWORDS

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



def cmd_dns(args: argparse.Namespace) -> None:
    """Handler for DNS wordlist generation (alterx + DNSCewl parity)."""
    from wlf_modules.dns_wordlist import (
        generate_subdomain_permutations, generate_from_template, load_words_from_file,
        load_templates_from_yaml, generate_from_yaml_templates,
        generate_multi_domain, filter_dns_output, clusterbomb_generate,
        parse_fqdn, enrich_payloads, dnscewl_mutations, estimate_output,
        PAYLOAD_WORD, PAYLOAD_NUMBER, PAYLOAD_REGION, DEFAULT_PATTERNS,
    )
    from itertools import chain

    match_regex = getattr(args, "match_regex", None)
    filter_regex = getattr(args, "filter_regex", None)
    separator = getattr(args, "separator", None)
    separators = [separator] if separator else None

    words: list[str] = []
    if getattr(args, "wordlist", None):
        words = load_words_from_file(args.wordlist)
    if getattr(args, "words", None):
        words.extend(args.words)

    custom_payloads: dict[str, list[str]] = {}
    for pp in (getattr(args, "payloads", None) or []):
        if "=" in pp:
            key, fpath = pp.split("=", 1)
            custom_payloads[key.strip()] = load_words_from_file(fpath.strip())

    # ── Multi-domain mode ──────────────────────────────────────
    domain_list = getattr(args, "domain_list", None)
    if domain_list and not getattr(args, "clusterbomb", False):
        gen = generate_multi_domain(
            domain_list, words or PAYLOAD_WORD, separators,
            use_prefixes=not getattr(args, "no_prefixes", False),
            use_suffixes=not getattr(args, "no_suffixes", False),
            match_regex=match_regex, filter_regex=filter_regex,
        )
        count = _write_output(gen, args.output)
        _ok(f"Generated: {count:,} DNS entries")
        return

    # ── ClusterBomb mode (alterx-style) ────────────────────────
    if getattr(args, "clusterbomb", False) or getattr(args, "template_file", None):
        payloads = {
            "word": words if words else PAYLOAD_WORD,
            "number": PAYLOAD_NUMBER,
            "region": PAYLOAD_REGION,
        }
        payloads.update(custom_payloads)

        patterns = DEFAULT_PATTERNS
        extra_yaml_payloads: dict[str, Any] = {}

        template_file = getattr(args, "template_file", None)
        if template_file:
            try:
                yaml_templates, yaml_payloads = load_templates_from_yaml(template_file)
                if yaml_templates:
                    patterns = yaml_templates  # type: ignore[assignment]
                if yaml_payloads:
                    extra_yaml_payloads = yaml_payloads  # type: ignore[assignment]
                    payloads.update(yaml_payloads)  # type: ignore[arg-type]
            except (FileNotFoundError, ImportError) as exc:
                _err(str(exc))
                return

        input_fqdns = []
        if args.domain:
            input_fqdns = [args.domain]
        elif domain_list:
            input_fqdns = load_words_from_file(domain_list)

        if getattr(args, "enrich", False) and input_fqdns:
            payloads["word"], payloads["number"] = enrich_payloads(
                input_fqdns, payloads["word"], payloads["number"],
            )
            _info(f"Enriched: {len(payloads['word'])} words, {len(payloads['number'])} numbers")

        if getattr(args, "estimate", False):
            est = estimate_output(patterns, payloads, len(input_fqdns) or 1)
            _ok(f"Estimated output: {est:,} lines")
            return

        generators = []
        for fqdn in (input_fqdns or [""]):
            input_vars = parse_fqdn(fqdn) if fqdn else {}
            generators.append(clusterbomb_generate(
                patterns, payloads, input_vars,
                match_regex=match_regex, filter_regex=filter_regex,
            ))

        if getattr(args, "dnscewl", False) and input_fqdns:
            for fqdn in input_fqdns:
                generators.append(dnscewl_mutations(
                    payloads["word"][:50], fqdn,
                    numeric_range=getattr(args, "numeric_range", 10),
                    extension_swap=getattr(args, "extension_swap", None),
                ))

        count = _write_output(chain(*generators), args.output)  # type: ignore[arg-type]
        _ok(f"Generated: {count:,} DNS entries (ClusterBomb)")
        return

    if not words:
        words = PAYLOAD_WORD[:30]
        _info(f"No words provided - using {len(words)} built-in payloads")

    generators = []

    if args.template:
        gen = generate_from_template(args.template, words, args.domain)
        generators.append(filter_dns_output(gen, match_regex, filter_regex))
    else:
        generators.append(generate_subdomain_permutations(
            words, args.domain, separators,
            use_prefixes=not args.no_prefixes,
            use_suffixes=not args.no_suffixes,
            match_regex=match_regex, filter_regex=filter_regex,
        ))

    if getattr(args, "dnscewl", False):
        generators.append(dnscewl_mutations(
            words[:50], args.domain,
            numeric_range=getattr(args, "numeric_range", 10),
            extension_swap=getattr(args, "extension_swap", None),
        ))

    count = _write_output(chain(*generators), args.output)  # type: ignore[arg-type]
    _ok(f"Generated: {count:,} subdomains")



def cmd_pharma(args: argparse.Namespace) -> None:
    """Generate passwords and usernames for retail/pharmacy chain patterns."""
    from wlf_modules.pharma_gen import (
        gen_passwords, gen_usernames, gen_both, _expand_id_range,
    )

    brand  = getattr(args, "brand", None) or "BrandX"
    mode   = getattr(args, "mode", "both") or "both"

    raw_ids = getattr(args, "ids", None)
    if raw_ids:
        store_ids = _expand_id_range(raw_ids)
    else:
        store_ids = list(range(1200, 1215))

    raw_cnpjs  = getattr(args, "cnpj", None)
    cnpjs      = [c.strip() for c in raw_cnpjs.split(",")] if raw_cnpjs else []

    raw_abbrevs = getattr(args, "abbrevs", None)
    abbrevs     = [a.strip() for a in raw_abbrevs.split(",")] if raw_abbrevs else None

    raw_seps = getattr(args, "separators", None)
    seps     = [s for s in raw_seps.split(",")] if raw_seps else None

    raw_partners = getattr(args, "partners", None)
    partners     = [p.strip() for p in raw_partners.split(",")] if raw_partners else None

    raw_domains = getattr(args, "domains", None)
    domains     = [d.strip() for d in raw_domains.split(",")] if raw_domains else None

    padding  = not getattr(args, "no_padding", False)
    min_len  = getattr(args, "min_len", 0) or 0
    max_len  = getattr(args, "max_len", 0) or 0

    _info(f"Brand: {brand}  |  IDs: {len(store_ids)}  |  Tax IDs: {len(cnpjs)}  |  Mode: {mode}")

    if mode == "passwords":
        gen = gen_passwords(brand, store_ids, cnpjs, abbrevs, seps, partners,
                            padding, min_len, max_len)
    elif mode == "usernames":
        gen = gen_usernames(brand, store_ids, domains, abbrevs, padding,
                            True, min_len, max_len)
    else:
        gen = gen_both(brand, store_ids, cnpjs, abbrevs, seps, partners,
                       domains, padding, min_len, max_len)

    count = _write_output(gen, args.output)
    _ok(f"pharma: {count:,} entries generated")



def cmd_default_creds(args: argparse.Namespace) -> None:
    """Handler for the default-creds subcommand - query IoT/router default credentials."""
    from wlf_modules.default_creds import handle_default_creds
    handle_default_creds(args, {})



def cmd_isp_keygen(args: argparse.Namespace) -> None:
    """Handler for ISP default WiFi password keyspace generation."""
    from wlf_modules.isp_keygen import handle_isp_keygen
    handle_isp_keygen(args, {})



def cmd_corp_prefixes(args: argparse.Namespace) -> None:
    """Handler for corporate username prefix generation."""
    from wlf_modules.corp_prefixes import (
        load_prefix_config,
        generate_from_name,
        get_all_prefixes,
        list_all_prefixes,
    )

    try:
        config = load_prefix_config(getattr(args, "config", None))
    except FileNotFoundError as exc:
        _err(str(exc))
        return

    # ── List available prefixes ──────────────────────────────────────────────
    if getattr(args, "list_prefixes", False):
        all_groups = list_all_prefixes(config)
        for group, aliases in all_groups.items():
            print(f"  {group}: {', '.join(aliases)}")
        return

    # ── Collect names ────────────────────────────────────────────────────────
    names: list[str] = []
    if getattr(args, "names", None):
        raw = args.names if isinstance(args.names, str) else ",".join(args.names)
        names = [n.strip() for n in raw.split(",") if n.strip()]

    if getattr(args, "file", None):
        from wlf_modules.domain_users import collect_names_from_file
        try:
            names += collect_names_from_file(args.file)
        except FileNotFoundError as exc:
            _err(str(exc))
            return

    if not names:
        _warn("No names provided. Use --names or --file.")
        return

    # ── Resolve options ──────────────────────────────────────────────────────
    domain     = getattr(args, "domain", "") or ""
    sector     = getattr(args, "sector", None)
    categories = None
    if getattr(args, "categories", None):
        categories = [c.strip() for c in args.categories.split(",")]

    # Explicit prefix list
    prefixes = None
    if getattr(args, "prefixes", None):
        prefixes = [p.strip() for p in args.prefixes.split(",")]

    sep_raw = getattr(args, "separators", None)
    if sep_raw:
        separators = [s if s.lower() not in ("none", "empty") else "" for s in sep_raw.split(",")]
    else:
        separators = ["."]  # default

    with_numeric = not getattr(args, "no_numeric", False)

    # ── Generate ────────────────────────────────────────────────────────────
    def _generate() -> Generator[str, None, None]:
        for name in names:
            results = generate_from_name(
                full_name=name,
                domain=domain,
                prefixes=prefixes,
                categories=categories,
                separators=separators,
                sector=sector,
                with_numeric=with_numeric,
                config=config,
            )
            if domain and not getattr(args, "no_at", False):
                for r in results:
                    yield f"{r}@{domain}"
            else:
                yield from results

    count = _write_output(_generate(), args.output)
    _ok(f"Generated: {count:,} prefixed username entries")



def cmd_osint_perm(args: argparse.Namespace) -> None:
    """Generate OSINT-based password candidates from target profile."""
    from wlf_modules.osint_perm import OsintProfile, OsintPermGenerator

    profile = OsintProfile(
        first_name=getattr(args, "first_name", "") or "",
        last_name=getattr(args, "last_name", "") or "",
        nickname=getattr(args, "nick", "") or "",
        birth_date=getattr(args, "birth", "") or "",
        pet_name=getattr(args, "pet", "") or "",
        phone=getattr(args, "phone", "") or "",
        complexity=getattr(args, "complexity", 1),
        keywords=list(getattr(args, "keywords", None) or []),
    )
    gen = OsintPermGenerator()
    results = gen.generate(profile)
    output = getattr(args, "output", None)
    if output:
        from pathlib import Path
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(results), encoding="utf-8")
        _info(f"Saved {len(results)} candidates to: {output}")
    else:
        for r in results[:50]:
            print(r)
        if len(results) > 50:
            _info(f"... and {len(results)-50} more. Use -o FILE to save all.")
    _info(f"Generated {len(results)} OSINT-based candidates.")



def cmd_cupp(args: argparse.Namespace) -> None:
    """Generate target-specific passwords from user profile (CUPP-style)."""
    from wlf_modules.cupp_engine import CuppEngine, CuppProfile

    profile = CuppProfile(
        first_name=getattr(args, "first_name", "") or "",
        last_name=getattr(args, "last_name", "") or "",
        nickname=getattr(args, "nick", "") or "",
        birth_date=getattr(args, "birth", "") or "",
        pet_name=getattr(args, "pet", "") or "",
        company=getattr(args, "company", "") or "",
        extra_words=list(getattr(args, "words", None) or []),
    )
    engine = CuppEngine()
    results = engine.generate(profile, max_output=getattr(args, "max_output", 0))
    output = getattr(args, "output", None)
    if output:
        from pathlib import Path
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(results), encoding="utf-8")
        _info(f"Saved {len(results)} candidates to: {output}")
    else:
        for r in results[:50]:
            print(r)
        if len(results) > 50:
            _info(f"... and {len(results)-50} more. Use -o FILE to save all.")
    _info(f"Generated {len(results)} CUPP-style candidates.")



def cmd_scrape_target(args: argparse.Namespace) -> None:
    """Crawl a target URL and extract words for wordlist generation."""
    from wlf_modules.target_spider import TargetSpider

    url = getattr(args, "url", None)
    if not url:
        _warn("scrape-target requires --url")
        return
    depth = getattr(args, "depth", 2)
    min_len = getattr(args, "min_len", 4)
    output = getattr(args, "output", None)

    spider = TargetSpider(min_len=min_len, max_pages=getattr(args, "max_pages", 20))
    _info(f"Crawling {url} (depth={depth})...")

    try:
        words = spider.crawl(url, depth=depth)
    except ImportError as exc:
        _warn(f"requests/beautifulsoup4 required: {exc}")
        return

    if output:
        from pathlib import Path
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(words), encoding="utf-8")
        _info(f"Saved {len(words)} words to: {output}")
    else:
        for w in words[:40]:
            print(w)
        if len(words) > 40:
            _info(f"... and {len(words)-40} more. Use -o FILE to save all.")
    _info(f"Extracted {len(words)} words from {url}")



def cmd_osint(args: argparse.Namespace) -> None:
    """Handler for advanced OSINT wordlist collection."""
    from wlf_modules.osint_advanced import handle_osint

    gen = handle_osint(args, _GLOBAL_CTX)
    if gen is None:
        return
    count = _write_output(gen, getattr(args, "output", None))
    _ok(f"OSINT wordlist: {count:,} candidates")



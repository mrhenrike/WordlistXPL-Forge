def cmd_dns(args: argparse.Namespace) -> None:
    """Handler for DNS wordlist generation (alterx + DNSCewl parity)."""
    from itertools import chain

    from wlf_modules.dns_wordlist import (
        DEFAULT_PATTERNS,
        PAYLOAD_NUMBER,
        PAYLOAD_REGION,
        PAYLOAD_WORD,
        clusterbomb_generate,
        dnscewl_mutations,
        enrich_payloads,
        estimate_output,
        filter_dns_output,
        generate_from_template,
        generate_multi_domain,
        generate_subdomain_permutations,
        load_templates_from_yaml,
        load_words_from_file,
        parse_fqdn,
    )

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

        template_file = getattr(args, "template_file", None)
        if template_file:
            try:
                yaml_templates, yaml_payloads = load_templates_from_yaml(template_file)
                if yaml_templates:
                    patterns = yaml_templates  # type: ignore[assignment]
                if yaml_payloads:
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
        _expand_id_range,
        gen_both,
        gen_passwords,
        gen_usernames,
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
        generate_from_name,
        list_all_prefixes,
        load_prefix_config,
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
    from wlf_modules.osint_perm import OsintPermGenerator, OsintProfile

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



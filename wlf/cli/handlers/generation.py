"""Command handlers: generation."""
from __future__ import annotations

import argparse
from pathlib import Path

from typing import Any, Generator, Optional

from wlf.cli.context import (
    Fore, Style, _GLOBAL_CTX, _TQDM, _tqdm, logger, is_shutdown, VERSION,
)
from wlf.cli.utils import (
    _info, _ok, _warn, _err, _write_output,
    _effective_len_bounds, _format_bytes, _check_disk_space,
    _confirm_large, _count_generator_entries,
    _profile_preview_and_confirm, _resolve_path, _load_profile_file,
)


def cmd_charset(args: argparse.Namespace) -> None:
    """Handler for charset mode."""
    from wlf_modules.charset_gen import (
        get_charset, generate_by_charset, generate_by_pattern,
        estimate_size, create_charset_wizard, PLACEHOLDER_MAP,
        generate_by_mask, estimate_mask_size,
        generate_constrained, estimate_constrained_size,
    )

    if args.create_charset:
        create_charset_wizard(args.create_charset)
        return

    # ── Hashcat-style mask (?u?l?d?s?a) ──────────────────────
    if getattr(args, "mask", None):
        total, size = estimate_mask_size(args.mask, getattr(args, "custom_charset1", None))
        _info(f"Mask: {args.mask} | Estimated: {total:,} entries ~ {size}")
        if not _confirm_large(total):
            _warn("Operation cancelled.")
            return
        gen = generate_by_mask(args.mask, getattr(args, "custom_charset1", None))
        count = _write_output(gen, args.output, estimate=total)
        _ok(f"Generated: {count:,} entries")
        return

    # ── Constrained composition (--digits N --lower M --upper K --special P) ─
    n_digits = getattr(args, "n_digits", 0) or 0
    n_lower = getattr(args, "n_lower", 0) or 0
    n_upper = getattr(args, "n_upper", 0) or 0
    n_special = getattr(args, "n_special", 0) or 0
    if any([n_digits, n_lower, n_upper, n_special]):
        length = args.min_len  # for constrained mode use min_len as fixed length
        total, size = estimate_constrained_size(length, n_digits, n_lower, n_upper, n_special)
        _info(
            f"Constrained: len={length} | digits={n_digits} lower={n_lower} "
            f"upper={n_upper} special={n_special} | Est: {total:,} ~ {size}"
        )
        if not _confirm_large(total):
            _warn("Operation cancelled.")
            return
        try:
            gen = generate_constrained(length, n_digits, n_lower, n_upper, n_special)
        except ValueError as exc:
            _err(str(exc))
            return
        count = _write_output(gen, args.output, estimate=total)
        _ok(f"Generated: {count:,} entries")
        return

    # ── Crunch-style pattern (@,%,^) ──────────────────────────
    if args.pattern:
        _info(f"Generating by pattern: {args.pattern}")
        gen = generate_by_pattern(
            args.pattern,
            charset_file=args.charset_file,
            extra_charset=args.charset if args.charset else None,
        )
        count = _write_output(gen, args.output)
        _ok(f"Generated: {count:,} entries")
        return

    # ── Standard charset generation ───────────────────────────
    charset_str = get_charset(args.charset or "lalpha", args.charset_file)
    total, size = estimate_size(len(charset_str), args.min_len, args.max_len)
    _info(f"Charset: {len(charset_str)} chars | {args.min_len}..{args.max_len} | "
          f"Estimated: {total:,} entries ~ {size}")

    if not _confirm_large(total):
        _warn("Operation cancelled.")
        return

    gen = generate_by_charset(charset_str, args.min_len, args.max_len)
    count = _write_output(gen, args.output, estimate=total)
    _ok(f"Generated: {count:,} entries")



def cmd_pattern(args: argparse.Namespace) -> None:
    """Handler for pattern mode."""
    from wlf_modules.pattern_engine import (
        render_template, generate_from_template_file, expand_variable,
        generate_company_patterns,
    )

    variables: dict[str, list[str]] = {}
    for var_spec in (args.vars or []):
        if "=" in var_spec:
            name, val = var_spec.split("=", 1)
            variables[name.strip()] = expand_variable(name.strip(), val.strip())

    if args.template_file:
        gen = generate_from_template_file(args.template_file, variables)
    elif args.template:
        gen = render_template(args.template, variables)
    else:
        _err("Provide --template or --template-file")
        return

    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} entries")



def cmd_mutate(args: argparse.Namespace) -> None:
    """Handler for existing-password mutation generator."""
    from wlf_modules.profiler import password_variants

    password = getattr(args, "password", "") or ""
    if not password:
        _err("A password is required.")
        return

    extra_prefixes: Optional[list[str]] = None
    raw_pfx = getattr(args, "prefixes", None)
    if raw_pfx:
        extra_prefixes = ["" if p == "EMPTY" else p for p in raw_pfx.split(",")]

    extra_suffixes: Optional[list[str]] = None
    raw_sfx = getattr(args, "suffixes", None)
    if raw_sfx:
        extra_suffixes = ["" if s == "EMPTY" else s for s in raw_sfx.split(",")]

    leet_mode = getattr(args, "leet_mode", "all") or "all"
    min_len = getattr(args, "min_len", 1) or 1
    max_len = getattr(args, "max_len", 128) or 128

    _info(f"Password : {password}")
    _info(f"Leet     : {leet_mode}")

    # Base passwords to mutate. With --titlecase, also seed a per-token
    # CamelCase variant of the base (e.g. nerd_trilha -> Nerd_Trilha), a common
    # human pattern the mutation engine does not derive on its own.
    base_passwords = [password]
    if getattr(args, "titlecase", False):
        from wlf_modules.affix_engine import titlecase_word
        tc = titlecase_word(password)
        if tc and tc != password:
            base_passwords.append(tc)

    seen_variants: set[str] = set()

    def _gen() -> Generator[str, None, None]:
        for base in base_passwords:
            for v in password_variants(
                base,
                extra_prefixes=extra_prefixes,
                extra_suffixes=extra_suffixes,
                leet_mode=leet_mode,
                min_len=min_len,
                max_len=max_len,
            ):
                if v not in seen_variants:
                    seen_variants.add(v)
                    yield v

    count = _write_output(_gen(), args.output)
    _ok(f"Generated: {count:,} mutation variants")



def cmd_num2text(args: argparse.Namespace) -> None:
    """Convert digits to text words and generate case/leet/separator variations."""
    from wlf_modules.num2text import num2text_variants, num2text_range, _normalise_lang

    lang     = _normalise_lang(getattr(args, "lang", "en") or "en")
    raw_seps = getattr(args, "separators", None)
    seps     = [s for s in raw_seps.split(",")] if raw_seps else None
    no_leet  = getattr(args, "no_leet", False)
    min_len  = getattr(args, "min_len", 0) or 0
    max_len  = getattr(args, "max_len", 0) or 0

    raw_range  = getattr(args, "range", None)
    raw_number = getattr(args, "number", None)

    if raw_range:
        parts = raw_range.split("-", 1)
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            _err("--range must be in format START-END (e.g. 0-9999)")
            return
        start, end = int(parts[0]), int(parts[1])
        if end - start > 1_000_000:
            _err("Range too large (max 1,000,000 numbers at once)")
            return
        _info(f"num2text range {start}-{end}  lang={lang}")
        gen = num2text_range(start, end, lang, seps, not no_leet, min_len, max_len)
    elif raw_number:
        s = str(raw_number)
        if not s.isdigit():
            _err("--number must contain digits only")
            return
        if len(s) > 12:
            _err("--number exceeds 12 digits")
            return
        _info(f"num2text: {s}  lang={lang}")
        gen = num2text_variants(s, lang, seps, not no_leet, min_len, max_len)
    else:
        _err("Provide --number or --range")
        return

    count = _write_output(gen, args.output)
    _ok(f"num2text: {count:,} variants generated")



def cmd_phrase(args: argparse.Namespace) -> None:
    """Handler for phrase-initials password generation."""
    from wlf_modules.profiler import phrase_initials_variants

    phrase = getattr(args, "phrase", "") or ""
    if not phrase:
        _err("A phrase is required.")
        return

    extra_prefixes: Optional[list[str]] = None
    raw_pfx = getattr(args, "prefixes", None)
    if raw_pfx:
        parts = raw_pfx.split(",")
        extra_prefixes = ["" if p == "EMPTY" else p for p in parts]

    extra_suffixes: Optional[list[str]] = None
    raw_sfx = getattr(args, "suffixes", None)
    if raw_sfx:
        parts = raw_sfx.split(",")
        extra_suffixes = ["" if s == "EMPTY" else s for s in parts]

    _info(f"Phrase : {phrase}")

    variants = phrase_initials_variants(
        phrase,
        extra_prefixes=extra_prefixes,
        extra_suffixes=extra_suffixes,
    )

    def _gen() -> Generator[str, None, None]:
        yield from variants

    count = _write_output(_gen(), args.output)
    _ok(f"Generated: {count:,} phrase-initials variants")



def cmd_leet(args: argparse.Namespace) -> None:
    """Handler for leet speak mode."""
    use_gpu = bool(getattr(args, "gpu", False)) or (
        _GLOBAL_CTX.get("compute_mode", "auto") in ("gpu", "cuda", "hybrid")
    )
    _info(f"Generating leet variants [{args.mode}] for: {args.word}"
          + (" [gpu]" if use_gpu else ""))
    if use_gpu:
        from wlf_modules.gpu_expand import expand_leet_batch
        gen = expand_leet_batch(
            [args.word],
            mode=args.mode,
            max_per_word=args.max_results,
            use_gpu=True,
        )
    else:
        from wlf_modules.leet_permuter import generate_all_variations
        gen = generate_all_variations(
            args.word,
            leet_mode=args.mode,
            custom_mapping=getattr(args, "custom_map", "") or "",
            max_leet=args.max_results,
        )
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} variants")



def cmd_leet_perm(args: argparse.Namespace) -> None:
    """Handler for cartesian leet permutation over a wordlist (elpscrk-style)."""
    from wlf_modules.leet_permuter import leet_perm_wordlist, parse_custom_mapping, LEET_MEDIUM

    wordlist = getattr(args, "wordlist", None)
    if not wordlist:
        _err("Provide a wordlist file.")
        return
    path = Path(wordlist)
    if not path.exists():
        _err(f"File not found: {wordlist}")
        return

    leet_map = None
    custom = getattr(args, "custom_map", "") or ""
    if custom:
        parsed = parse_custom_mapping(custom)
        leet_map = {
            k: (v[0] if v else k)
            for k, v in parsed.items()
        }
    elif getattr(args, "mode", "medium") == "medium":
        leet_map = {
            k: (v[1] if len(v) > 1 else k)
            for k, v in LEET_MEDIUM.items()
        }

    max_per = getattr(args, "max_per_word", 512) or 512
    max_lines = getattr(args, "max_lines", 0) or 0

    def _gen() -> Generator[str, None, None]:
        count = 0
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                word = line.rstrip("\n\r")
                if not word:
                    continue
                count += 1
                if max_lines and count > max_lines:
                    break
                yield from leet_perm_wordlist([word], leet_map=leet_map, max_per_word=max_per)

    _info(f"Applying leet-perm to {wordlist} (max {max_per}/word)...")
    total = _write_output(_gen(), args.output)
    _ok(f"Generated: {total:,} leet-perm variants")



def cmd_combiner(args: argparse.Namespace) -> None:
    """Handler for keyword combiner wordlist generation."""
    from wlf_modules.combiner import handle_combiner
    gen = handle_combiner(args, {})  # type: ignore[func-returns-value]
    if gen:
        count = _write_output(gen, args.output)
        _ok(f"Generated: {count:,} combined entries")



def cmd_pcfg(args: argparse.Namespace) -> None:
    """Handler for PCFG grammar training and generation."""
    from wlf_modules.pcfg_engine import handle_pcfg
    gen = handle_pcfg(args, _GLOBAL_CTX)
    if gen:
        action = getattr(args, "pcfg_action", "generate")
        if action == "train":
            for line in gen:
                print(line)
        else:
            count = _write_output(
                gen, args.output,
                min_len=getattr(args, "min_len", 1),
                max_len=getattr(args, "max_len", 64),
            )
            _ok(f"PCFG generated: {count:,} candidates (probability-ordered)")



def cmd_markov(args: argparse.Namespace) -> None:
    """Handler for Markov model training and generation."""
    from wlf_modules.markov_engine import handle_markov
    gen = handle_markov(args, _GLOBAL_CTX)
    if gen:
        action = getattr(args, "markov_action", "generate")
        if action == "train":
            for line in gen:
                print(line)
        else:
            count = _write_output(
                gen, args.output,
                min_len=getattr(args, "min_len", 4),
                max_len=getattr(args, "max_len", 16),
            )
            _ok(f"Markov generated: {count:,} candidates (cost-ordered)")



def cmd_kwalk(args: argparse.Namespace) -> None:
    """Handler for keyboard walk generation."""
    from wlf_modules.kwalk_gen import handle_kwalk
    gen = handle_kwalk(args, _GLOBAL_CTX)
    if gen:
        if getattr(args, "list_layouts", False):
            for line in gen:
                print(line)
        else:
            count = _write_output(gen, args.output)
            _ok(f"Keyboard walks generated: {count:,} candidates")



def cmd_prince(args: argparse.Namespace) -> None:
    """Handler for PRINCE attack mode."""
    from wlf_modules.prince_engine import handle_prince
    gen = handle_prince(args, _GLOBAL_CTX)
    if gen:
        count = _write_output(gen, args.output)
        _ok(f"PRINCE generated: {count:,} chained candidates")



def cmd_br_names(args: argparse.Namespace) -> None:
    """Handler for the br-names subcommand.

    Generates a username list from BRWordList Brazilian name files.
    """
    from wlf_modules.brwordlist_loader import BRWordListLoader, generate_usernames_from_br_names
    from pathlib import Path as _Path

    explicit_path: Optional[str] = getattr(args, "brwordlist_path", None)
    base_path = _Path(explicit_path) if explicit_path else None

    category: str = getattr(args, "category", "names") or "names"
    include_leet: bool = bool(getattr(args, "leet", False))

    loader = BRWordListLoader(base_path)
    if not loader.is_available():
        _warn(
            "BRWordList not found. Provide --brwordlist-path or set "
            "WLF_BRWORDLIST_PATH to a BRWordList checkout."
        )
        return

    _info(f"Loading BRWordList names (category={category})...")
    usernames = generate_usernames_from_br_names(
        category=category,
        base_path=base_path,
        include_leet=include_leet,
    )

    if not usernames:
        _warn("No names loaded from BRWordList.")
        return

    count = _write_output(iter(usernames), args.output)  # type: ignore[arg-type]
    _ok(f"br-names: {count:,} username entries generated")



def cmd_iwlgen(args: argparse.Namespace) -> None:
    """Handler for the iwlgen subcommand.

    Generates keyword permutation wordlists using the IwlgenEngine.
    """
    from wlf_modules.iwlgen import IwlgenEngine

    raw_keywords: Optional[str] = getattr(args, "keywords", None)
    if not raw_keywords:
        _err("Provide at least one keyword with --keywords.")
        return

    keywords: list[str] = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    if not keywords:
        _err("No valid keywords found in --keywords input.")
        return

    raw_connectors: str = getattr(args, "connectors", "") or ""
    if raw_connectors:
        connectors = list(raw_connectors)
    else:
        connectors = ["", ".", "_", "-", "@"]

    do_leet: bool = bool(getattr(args, "leet", False))
    do_abbr: bool = bool(getattr(args, "abbreviation", False))
    do_reverse: bool = bool(getattr(args, "reverse", False))

    raw_num_tails: Optional[str] = getattr(args, "num_tails", None)
    num_tails: list[str] = [t.strip() for t in raw_num_tails.split(",") if t.strip()] if raw_num_tails else []

    min_len: int = int(getattr(args, "min_length", 4) or 4)
    max_len: int = int(getattr(args, "max_length", 64) or 64)

    config = {
        "connectors": connectors,
        "leet": do_leet,
        "abbreviation": do_abbr,
        "reverse": do_reverse,
        "num_tails": num_tails,
        "tails": [""],
        "min_length": min_len,
        "max_length": max_len,
        "to_lower": True,
    }

    _info(f"IwlgenEngine: keywords={keywords}, connectors={connectors}, leet={do_leet}")
    engine = IwlgenEngine()
    wordlist = engine.generate(keywords=keywords, config=config)

    count = _write_output(iter(wordlist), args.output)  # type: ignore[arg-type]
    _ok(f"iwlgen: {count:,} entries generated")


# ── Interactive menu ──────────────────────────────────────────────────────────


def cmd_neural(args: argparse.Namespace) -> None:
    """Handler for neural password generation (optional [neural] extra)."""
    from wlf_modules.neural_engine import handle_neural

    res = handle_neural(args, _GLOBAL_CTX)
    if not res:
        return
    kind, payload = res
    if kind == "status":
        for line in payload:
            print(line)
    else:
        count = _write_output(payload, getattr(args, "output", None))
        _ok(f"Neural generated: {count:,} candidates")



def cmd_passphrase(args: argparse.Namespace) -> None:
    """Handler for diceware/mnemonic passphrase generation."""
    from wlf_modules.passphrase_gen import handle_passphrase

    gen = handle_passphrase(args, _GLOBAL_CTX)
    if gen is None:
        return
    count = _write_output(gen, getattr(args, "output", None))
    _ok(f"Passphrases generated: {count:,}")



def cmd_br_deep(args: argparse.Namespace) -> None:
    """Brazilian deep profile wordlist generation."""
    try:
        from wlf_modules.br_deep_engine import BRDeepEngine
        profile: dict[str, Any] = {}
        profile_file = getattr(args, "profile_file", None)
        if profile_file:
            profile = _load_profile_file(profile_file)
        sector = getattr(args, "sector", None) or profile.get("sector", "generic")
        include_cpf = not getattr(args, "no_cpf", False)
        include_cnpj = not getattr(args, "no_cnpj", False)
        include_cep = not getattr(args, "no_cep", False)
        eng = BRDeepEngine(
            profile=profile,
            sector=sector,
            include_cpf_patterns=include_cpf,
            include_cnpj_patterns=include_cnpj,
            include_cep_patterns=include_cep,
            cep_prefix=getattr(args, "cep_prefix", None),
        )
        limit = int(_GLOBAL_CTX.get("limit") or 100_000)
        gen = (pw for pw, _ in eng.generate(max_candidates=limit))
        count = _write_output(gen, getattr(args, "output", None), stream=True)
        _ok(f"br-deep: {count:,} candidates")
    except Exception as exc:
        _err(f"br-deep error: {exc}")



def cmd_pbmp(args: argparse.Namespace) -> None:
    """Show PBMP strategy distribution for a profile."""
    try:
        from wlf_modules.pbmp_full import PBMPFull
        profile: dict[str, Any] = {}
        profile_file = getattr(args, "profile_file", None)
        if profile_file:
            profile = _load_profile_file(profile_file)
        n = int(getattr(args, "n_engines", None) or 5)
        controller = PBMPFull(profile=profile, sector=profile.get("sector"))
        print(controller.describe())
        plan = controller.plan(n_engines=n)
        print("\nGeneration plan:")
        for step in plan:
            print(f"  {step['strategy']:<22s}  weight={step['weight']:.3f}  limit={step['limit']:,}")
    except Exception as exc:
        _err(f"PBMP error: {exc}")



def cmd_evolve(args: argparse.Namespace) -> None:
    """Evolutionary password generation (genetic / MAP-Elites)."""
    try:
        mode = getattr(args, "mode", None) or "genetic"
        limit = _GLOBAL_CTX.get("limit") or 50_000
        seed_file = getattr(args, "seed_file", None)
        seed_words: list[str] = []
        if seed_file:
            with open(seed_file, encoding="utf-8", errors="replace") as f:
                seed_words = [line.strip() for line in f if line.strip()]

        if mode == "map-elites":
            from wlf_modules.map_elites import MAPElites
            eng = MAPElites()
            gen_raw = eng.generate(seed_passwords=seed_words or None, max_candidates=limit)
        else:
            from wlf_modules.genetic_engine import GeneticPasswordEngine
            eng = GeneticPasswordEngine()  # type: ignore[assignment]
            gen_raw = eng.generate(seed_passwords=seed_words or None, max_candidates=limit)

        gen = (pw for pw, _ in gen_raw)
        _write_output(gen, getattr(args, "output", None), stream=True)
    except Exception as exc:
        _err(f"evolve error: {exc}")



def cmd_graph_expand(args: argparse.Namespace) -> None:
    """Graph-based wordlist expansion from a seed corpus."""
    try:
        from wlf_modules.password_graph import PasswordGraphEngine
        corpus_file = getattr(args, "corpus_file", None) or (getattr(args, "args", [None])[0] if hasattr(args, "args") else None)
        if not corpus_file:
            _warn("Usage: wlf graph-expand <corpus.txt> [-o out.txt]")
            return
        with open(corpus_file, encoding="utf-8", errors="replace") as f:
            corpus = [line.strip() for line in f if line.strip()]
        limit = _GLOBAL_CTX.get("limit") or 100_000
        eng = PasswordGraphEngine()
        gen = (pw for pw, _ in eng.generate(seed_corpus=corpus, max_candidates=limit))
        _write_output(gen, getattr(args, "output", None), stream=True)
        _info(eng.describe())
    except Exception as exc:
        _err(f"graph-expand error: {exc}")



def cmd_temporal_model(args: argparse.Namespace) -> None:
    """Temporal drift wordlist — evolve seeds across years."""
    try:
        from wlf_modules.temporal_drift import TemporalDriftEngine
        seed_file = getattr(args, "seed_file", None)
        seed_words: list[str] = []
        if seed_file:
            with open(seed_file, encoding="utf-8", errors="replace") as f:
                seed_words = [line.strip() for line in f if line.strip()]
        base_year  = int(getattr(args, "base_year", None)   or 2019)
        target_year = int(getattr(args, "target_year", None) or 2026)
        limit = _GLOBAL_CTX.get("limit") or 200_000
        eng = TemporalDriftEngine(base_year=base_year, target_year=target_year)
        gen = (pw for pw, _ in eng.generate(seed_words=seed_words or None, max_candidates=limit))
        _write_output(gen, getattr(args, "output", None), stream=True)
        _info(eng.describe())
    except Exception as exc:
        _err(f"temporal-model error: {exc}")



def cmd_domain_pcfg(args: argparse.Namespace) -> None:
    """Domain-specific PCFG generation (corporate, healthcare, finance, etc.)."""
    try:
        from wlf_modules.domain_pcfg import DomainPCFG
        sector = getattr(args, "sector", None) or "generic"
        corpus_file = getattr(args, "corpus_file", None)
        corpus: list[str] = []
        if corpus_file:
            with open(corpus_file, encoding="utf-8", errors="replace") as f:
                corpus = [line.strip() for line in f if line.strip()]
        limit = _GLOBAL_CTX.get("limit") or 100_000
        eng = DomainPCFG(sector=sector)
        gen = (pw for pw, _ in eng.generate(corpus=corpus or None, max_candidates=limit))
        _write_output(gen, getattr(args, "output", None), stream=True)
        _info(eng.describe())
    except Exception as exc:
        _err(f"domain-pcfg error: {exc}")



def cmd_vae_interp(args: argparse.Namespace) -> None:
    """VAE latent space interpolation between two passwords."""
    try:
        from wlf_modules.vae_engine import VAEPasswordEngine
        pw_from = getattr(args, "pw_from", None) or (getattr(args, "args", [None])[0] if hasattr(args, "args") else None)
        pw_to   = getattr(args, "pw_to",   None) or (getattr(args, "args", [None, None])[1] if hasattr(args, "args") else None)
        if not pw_from or not pw_to:
            _warn("Usage: wlf vae-interp <pw_from> <pw_to> [--steps N]")
            return
        steps = int(getattr(args, "steps", None) or 10)
        eng = VAEPasswordEngine()
        gen = (pw for pw, _ in eng.interpolate(pw_from, pw_to, steps=steps))
        _write_output(gen, getattr(args, "output", None), stream=True)
    except Exception as exc:
        _err(f"vae-interp error: {exc}")


if __name__ == "__main__":
    main()  # type: ignore[name-defined]


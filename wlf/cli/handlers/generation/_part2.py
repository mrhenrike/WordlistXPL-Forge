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



def cmd_rule_mine(args: argparse.Namespace) -> None:
    """Handler for rule mining from cracked passwords."""
    from wlf_modules.rule_miner import handle_rule_mine
    gen = handle_rule_mine(args, _GLOBAL_CTX)
    if gen:
        count = 0
        for line in gen:
            print(line)
            count += 1
        _ok(f"Rule mining complete: {count} rules found")


def cmd_finetune_data(args: argparse.Namespace) -> None:
    """Handler for LLM fine-tune dataset generation."""
    from wlf_modules.finetune_engine import handle_finetune
    gen = handle_finetune(args, _GLOBAL_CTX)
    if gen:
        count = 0
        for line in gen:
            print(line)
            count += 1
        _ok(f"Fine-tune dataset: {count:,} samples generated")


def cmd_nflow(args: argparse.Namespace) -> None:
    """Handler for normalizing flow password generation."""
    from wlf_modules.nflow_engine import handle_nflow
    gen = handle_nflow(args, _GLOBAL_CTX)
    if gen:
        if getattr(args, "interpolate_a", None):
            for line in gen:
                print(line)
        else:
            count = _write_output(gen, args.output)
            _ok(f"NFlow generation complete: {count:,} candidates")


def cmd_combo(args: argparse.Namespace) -> None:
    """Handler for credential combo generation."""
    from wlf_modules.combo_engine import handle_combo
    gen = handle_combo(args, _GLOBAL_CTX)
    if gen:
        count = _write_output(gen, args.output)
        _ok(f"Combo generation complete: {count:,} pairs")


def cmd_corp_conv(args: argparse.Namespace) -> None:
    """Handler for corporate convention password generation."""
    from wlf_modules.corp_convention import handle_corp_conv
    gen = handle_corp_conv(args, _GLOBAL_CTX)
    if gen:
        count = _write_output(gen, args.output)
        _ok(f"Corporate convention: {count:,} candidates generated")


def cmd_phonetic(args: argparse.Namespace) -> None:
    """Handler for phonetic similarity generation."""
    from wlf_modules.phonetic_engine import handle_phonetic
    gen = handle_phonetic(args, _GLOBAL_CTX)
    if gen:
        if getattr(args, "analyze", False):
            for line in gen:
                print(line)
        else:
            count = _write_output(gen, args.output)
            _ok(f"Phonetic variants generated: {count:,} candidates")


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
    from pathlib import Path as _Path

    from wlf_modules.brwordlist_loader import (
        BRWordListLoader,
        generate_usernames_from_br_names,
    )

    explicit_path: str | None = getattr(args, "brwordlist_path", None)
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

    raw_keywords: str | None = getattr(args, "keywords", None)
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

    raw_num_tails: str | None = getattr(args, "num_tails", None)
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



def cmd_locale(args: argparse.Namespace) -> None:
    """Regional/cultural password generation by locale."""
    try:
        from wlf_modules.locales import get_engine, list_locales
        if getattr(args, "list_locales", False):
            for lc in list_locales():
                eng = get_engine(lc)
                name = eng.locale_name if eng else lc
                _ok(f"  {lc:8s}  {name}")
            return
        code = getattr(args, "code", None)
        if not code:
            _err("locale: --code or --list required")
            return
        profile: dict[str, Any] = {}
        profile_file = getattr(args, "profile_file", None)
        if profile_file:
            profile = _load_profile_file(profile_file)
        limit = int(_GLOBAL_CTX.get("limit") or 100_000)
        eng = get_engine(code, profile=profile, max_candidates=limit)
        if eng is None:
            _err(f"locale: unknown code '{code}'. Use --list to see available locales")
            return
        gen = (pw for pw, _ in eng.generate())
        count = _write_output(gen, getattr(args, "output", None))
        _ok(f"locale[{code}]: {count:,} candidates")
    except Exception as exc:
        _err(f"locale error: {exc}")


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
    """Temporal drift wordlist  - evolve seeds across years."""
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




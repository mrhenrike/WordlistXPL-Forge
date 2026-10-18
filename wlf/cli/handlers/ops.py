"""Command handlers: ops."""
from __future__ import annotations

import argparse

from pathlib import Path

from wlf.cli.context import (
    Fore, Style, _GLOBAL_CTX, _TQDM, _tqdm, logger, is_shutdown, VERSION,
)
from wlf.cli.utils import (
    _info, _ok, _warn, _err, _write_output,
    _effective_len_bounds, _format_bytes, _check_disk_space,
    _confirm_large, _count_generator_entries,
    _profile_preview_and_confirm, _resolve_path, _load_profile_file,
)


def cmd_xor(args: argparse.Namespace) -> None:
    """Handler for XOR mode."""
    from wlf_modules.xor_crypto import (
        brute_force_display, xor_encrypt_str, xor_decrypt_str,
    )

    if args.brute:
        brute_force_display(args.brute)
    elif args.encrypt and args.key:
        import binascii
        enc = xor_encrypt_str(args.encrypt, args.key)
        _ok(f"Encrypted (hex): {binascii.hexlify(enc).decode()}")
    elif args.decrypt and args.key:
        import binascii
        data = bytes.fromhex(args.decrypt)
        result = xor_decrypt_str(data, args.key)
        _ok(f"Decrypted: {result!r}")
    else:
        _err("Provide --brute, --encrypt or --decrypt with --key")



def cmd_merge(args: argparse.Namespace) -> None:
    """Handler for wordlist merge."""
    from wlf_modules.merger import merge_to_file, stream_merged

    if not args.output:
        gen = stream_merged(
            args.files,
            min_len=args.min_len,
            max_len=args.max_len,
            no_numeric=args.no_numeric,
            filter_pattern=args.filter,
            dedupe=not args.no_dedupe,
            sort_mode=args.sort,
        )
        count = _write_output(gen, None)
    else:
        count = merge_to_file(
            args.files,
            args.output,
            min_len=args.min_len,
            max_len=args.max_len,
            no_numeric=args.no_numeric,
            filter_pattern=args.filter,
            dedupe=not args.no_dedupe,
            sort_mode=args.sort,
        )
    _ok(f"Total: {count:,} entries")



def cmd_sanitize(args: argparse.Namespace) -> None:
    """Handler for wordlist sanitization."""
    from wlf_modules.sanitizer import sanitize, format_sanitize_stats

    inplace = getattr(args, "inplace", False)
    output = getattr(args, "output", None)

    try:
        stats = sanitize(
            filepath=args.wordlist,
            output=output,
            no_blank=not getattr(args, "keep_blank", False),
            no_comments=not getattr(args, "keep_comments", False),
            dedupe=not getattr(args, "no_dedupe", False),
            sort_mode=getattr(args, "sort", None),
            min_len=getattr(args, "min_len", None),
            max_len=getattr(args, "max_len", None),
            filter_pattern=getattr(args, "filter", None),
            exclude_pattern=getattr(args, "exclude", None),
            inplace=inplace,
            strip_control=getattr(args, "strip_control", False),
        )
    except FileNotFoundError as exc:
        _err(str(exc))
        return

    _ok(format_sanitize_stats(stats, args.wordlist))
    if output:
        _ok(f"Saved to: {output}")
    elif inplace:
        _ok(f"File updated in-place: {args.wordlist}")



def cmd_reverse(args: argparse.Namespace) -> None:
    """Handler for wordlist line reversal (tac)."""
    from wlf_modules.sanitizer import reverse_file

    inplace = getattr(args, "inplace", False)
    output = getattr(args, "output", None)

    try:
        count = reverse_file(args.wordlist, output=output, inplace=inplace)
    except FileNotFoundError as exc:
        _err(str(exc))
        return

    _ok(f"Reversed: {count:,} lines")
    if output:
        _ok(f"Saved to: {output}")
    elif inplace:
        _ok(f"File updated in-place: {args.wordlist}")



def cmd_emit(args: argparse.Namespace) -> None:
    """Stream ordered candidates from a named engine to stdout/file."""
    engine = (getattr(args, "engine", "pcfg") or "pcfg").lower()
    limit = int(getattr(args, "limit", 0) or _GLOBAL_CTX.get("limit") or 0)
    _GLOBAL_CTX["stream"] = True
    gen = None
    if engine == "markov":
        from wlf_modules.markov_engine import MarkovModel
        m = MarkovModel()
        path = getattr(args, "model", None) or ".model/markov_model.json"
        if not Path(path).exists():
            _err(f"Model not found: {path}")
            return
        m.load(path)
        gen = m.generate(
            max_candidates=limit,
            min_length=getattr(args, "min_len", 4),
            max_length=getattr(args, "max_len", 16),
            beam_width=getattr(args, "beam_width", 0) or 100_000,
        )
    elif engine == "pcfg":
        from wlf_modules.pcfg_engine import PCFGGrammar
        g = PCFGGrammar()
        path = getattr(args, "model", None) or ".model/pcfg_grammar.json"
        if not Path(path).exists():
            _err(f"Grammar not found: {path}")
            return
        g.load(path)
        gen = g.generate(
            max_candidates=limit,
            top_structures=getattr(args, "top_structures", 50) or 50,
            top_terminals=getattr(args, "top_terminals", 80) or 80,
            beam_width=getattr(args, "beam_width", 0) or 250_000,
            zipf_s=float(getattr(args, "zipf_s", 0) or 0),
        )
    elif engine == "mask":
        from wlf_modules.gpu_expand import iter_mask
        from wlf_modules.resource_governor import governor_from_ctx
        gov = governor_from_ctx(_GLOBAL_CTX)
        chunk = gov.gpu_batch_size(65536)
        gen = iter_mask(
            getattr(args, "mask", "?l?l?l?d?d") or "?l?l?l?d?d",
            chunk_size=chunk,
            max_candidates=limit or 100_000,
        )
    elif engine == "semantic":
        from wlf_modules.profiler import load_profile_yaml
        from wlf_modules.semantic_pcfg import generate_semantic
        pf = getattr(args, "profile_file", None)
        if not pf:
            _err("semantic emit requires --profile-file")
            return
        profile = load_profile_yaml(pf)
        gen = generate_semantic(profile, max_candidates=limit or 50_000)
    else:
        _err(f"Unknown engine: {engine}")
        return
    count = _write_output(gen, getattr(args, "output", None), stream=True)
    _ok(f"Emitted: {count:,} candidates via {engine}")



def cmd_replay(args: argparse.Namespace) -> None:
    """Replay generated candidates against a bloom sample of the corpus."""
    from wlf_modules.coverage_analyzer import handle_replay
    handle_replay(args, {})



def cmd_rulegen(args: argparse.Namespace) -> None:
    """Handler for hashcat rule auto-generation."""
    from wlf_modules.rulegen_engine import handle_rulegen
    gen = handle_rulegen(args, _GLOBAL_CTX)
    if gen:
        output = getattr(args, "output", None)
        if output and output.endswith(".rule"):
            for line in gen:
                print(line)
        else:
            count = _write_output(gen, output)
            _ok(f"Rules generated: {count:,} hashcat-compatible rules")



def cmd_mangle(args: argparse.Namespace) -> None:
    """Handler for hashcat-style mangling rules on wordlists."""
    from wlf_modules.mangler import apply_rules, BUILTIN_RULES

    list_rules = getattr(args, "list_rules", False)
    if list_rules:
        _info("Available mangling rules:")
        for name, desc in BUILTIN_RULES.items():
            print(f"  {name:20s} - {desc}")
        return

    wordlist_path = getattr(args, "wordlist", None)
    if not wordlist_path:
        _err("Provide a wordlist to mangle.")
        return

    path = Path(wordlist_path)
    if not path.exists():
        _err(f"File not found: {wordlist_path}")
        return

    lines: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\n\r") for ln in f if ln.strip()]

    if getattr(args, "overseer", False):
        from wlf_modules.mangler import overseer_expand, OverseerConfig
        cfg = OverseerConfig(
            pps=int(getattr(args, "pps", 0) or 0),
            target_time_hrs=float(getattr(args, "time_budget", 1.0) or 1.0),
            use_gpu=bool(getattr(args, "use_gpu", False)),
            use_capswap=bool(getattr(args, "capswap", False)),
        )
        masks_raw = getattr(args, "masks", None)
        if masks_raw:
            cfg.masks = [m.strip() for m in masks_raw.split(",") if m.strip()]
        _info(
            f"PyMangler Overseer: {len(lines)} base words, "
            f"budget={cfg.target_time_hrs}h, gpu={cfg.use_gpu}"
        )
        gen = overseer_expand(lines[:50], cfg)
    else:
        rules = getattr(args, "rules", "all") or "all"
        if rules == "all":
            active_rules = list(BUILTIN_RULES.keys())
        else:
            active_rules = [r.strip() for r in rules.split(",") if r.strip()]
        _info(f"Mangling: {wordlist_path} with rules: {', '.join(active_rules)}")
        gen = apply_rules(lines, active_rules)

    count = _write_output(gen, args.output)
    _ok(f"Mangled output: {count:,} entries")



def cmd_improve(args: argparse.Namespace) -> None:
    """Enrich an existing wordlist (CUPP -w parity)."""
    from wlf_modules.profiler import improve_wordlist

    source = getattr(args, "wordlist", None)
    if not source:
        _err("Provide a wordlist to improve.")
        return
    if not Path(source).is_file():
        _err(f"File not found: {source}")
        return

    output = args.output or str(
        Path(source).with_name(Path(source).stem + ".improved.lst")
    )
    count = improve_wordlist(
        source_path=source,
        output_path=output,
        leet_mode=getattr(args, "leet", "basic") or "basic",
        append_years=not getattr(args, "no_years", False),
        append_specials=not getattr(args, "no_specials", False),
        year_start=int(getattr(args, "year_start", 2020)),
        year_end=int(getattr(args, "year_end", 2027)),
        min_len=int(getattr(args, "min_len", 6)),
        max_len=int(getattr(args, "max_len", 32)),
    )
    _ok(f"Improved wordlist: {count:,} entries -> {output}")



def cmd_rules(args: argparse.Namespace) -> None:
    """Handler for the rule engine (apply, convert, optimize)."""
    from wlf_modules.rule_engine import handle_rules

    gen = handle_rules(args, _GLOBAL_CTX)
    if gen is None:
        return
    action = getattr(args, "rules_action", "apply")
    if action == "apply":
        count = _write_output(gen, getattr(args, "output", None))
        _ok(f"Rules applied: {count:,} candidates")
    else:
        count = _write_output(gen, getattr(args, "output", None))
        _ok(f"Rules {action}: {count:,} rule line(s)")



def cmd_affix(args: argparse.Namespace) -> None:
    """Handler for the composite-affix mutation layer."""
    from wlf_modules.affix_engine import handle_affix

    gen = handle_affix(args, _GLOBAL_CTX)
    if gen is None:
        # Either an error was logged or a ruleset file was written.
        if getattr(args, "emit_ruleset", None):
            _ok(f"Composite affix ruleset written to: {args.emit_ruleset}")
        return
    count = _write_output(gen, getattr(args, "output", None))
    _ok(f"Generated: {count:,} composite-affix candidates")



def cmd_dedup(args: argparse.Namespace) -> None:
    """Handler for order-preserving deduplication."""
    from wlf_modules.list_ops import handle_dedup
    gen = handle_dedup(args, _GLOBAL_CTX)
    if gen is None:
        return
    count = _write_output(gen, getattr(args, "output", None))
    _ok(f"Dedup complete: {count:,} unique entries")



def cmd_subtract(args: argparse.Namespace) -> None:
    """Handler for set subtraction between wordlists."""
    from wlf_modules.list_ops import handle_subtract

    gen = handle_subtract(args, _GLOBAL_CTX)
    if gen is None:
        return
    count = _write_output(gen, getattr(args, "output", None))
    _ok(f"Subtract complete: {count:,} remaining entries")



def cmd_split(args: argparse.Namespace) -> None:
    """Handler for splitting a wordlist by count, size or entry length."""
    from wlf_modules.list_ops import split_file

    wordlist = getattr(args, "wordlist", None)
    if not wordlist:
        _err("split requires a wordlist")
        return
    out_prefix = getattr(args, "output", None) or wordlist
    try:
        stats = split_file(
            wordlist,
            out_prefix,
            by_lines=int(getattr(args, "lines", 0) or 0),
            by_size=getattr(args, "size", "") or "",
            by_length=bool(getattr(args, "by_length", False)),
        )
    except FileNotFoundError as exc:
        _err(str(exc))
        return
    _ok(
        f"Split ({stats['mode']}): {stats['total']:,} entries into "
        f"{stats['parts']} file(s)"
    )
    for fp in stats["files"][:20]:
        print(f"  {fp}")
    if len(stats["files"]) > 20:
        print(f"  ... and {len(stats['files']) - 20} more")



def cmd_keyspace(args: argparse.Namespace) -> None:
    """Handler for keyspace and time-to-exhaust estimation."""
    from wlf_modules.list_ops import (
        mask_keyspace, charset_keyspace, keyspace_report, _count_lines,
    )

    pps = float(getattr(args, "pps", 0) or 1_000_000_000)
    mask = getattr(args, "mask", None)
    charset = getattr(args, "charset", None)
    wordlist = getattr(args, "wordlist", None)
    rules = getattr(args, "rules", None)

    if mask:
        total = mask_keyspace(mask)
    elif charset:
        min_len = int(getattr(args, "min_len", 1) or 1)
        max_len = int(getattr(args, "max_len", min_len) or min_len)
        total = charset_keyspace(len(charset), min_len, max_len)
    elif wordlist:
        words = _count_lines(wordlist)
        mult = 1
        if rules:
            mult = max(1, _count_lines(rules))
        total = words * mult
    else:
        _err("keyspace requires --mask, --charset or --wordlist")
        return

    for line in keyspace_report(total, pps):
        print(line)



def cmd_curate(args: argparse.Namespace) -> None:
    """Handler for crack-rate list curation and merging."""
    from wlf_modules.eval_harness import handle_curate

    res = handle_curate(args, _GLOBAL_CTX)
    if not res:
        return
    _kind, payload = res
    lines, merge_gen = payload
    for line in lines:
        print(line)
    output = getattr(args, "output", None)
    if output:
        count = _write_output(merge_gen, output)
        _ok(f"Curated wordlist: {count:,} entries -> {output}")



def cmd_test(args: argparse.Namespace) -> None:
    """Credential testing pipeline — generate wordlist + hashcat cracking."""
    from wlf_modules.credential_tester import run_test, HASH_MODES

    hash_mode = None
    if args.mode:
        if args.mode.isdigit():
            hash_mode = int(args.mode)
        else:
            hash_mode = HASH_MODES.get(args.mode.lower())
            if hash_mode is None:
                _err(f"Unknown hash mode: {args.mode}")
                _info(f"Available: {', '.join(sorted(HASH_MODES.keys()))}")
                return

    run_test(
        hash_file=args.target,
        model=args.model,
        hash_mode=hash_mode,
        output_dir=args.output,
        timeout=args.timeout,
        max_words=args.max_words,
    )



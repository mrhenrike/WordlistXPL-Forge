"""Command handlers: generation."""
from __future__ import annotations

import argparse
from collections.abc import Generator
from pathlib import Path
from typing import Any

from wlf.cli.context import (
    _GLOBAL_CTX,
)
from wlf.cli.utils import (
    _confirm_large,
    _err,
    _info,
    _load_profile_file,
    _ok,
    _warn,
    _write_output,
)


def cmd_charset(args: argparse.Namespace) -> None:
    """Handler for charset mode."""
    from wlf_modules.charset_gen import (
        create_charset_wizard,
        estimate_constrained_size,
        estimate_mask_size,
        estimate_size,
        generate_by_charset,
        generate_by_mask,
        generate_by_pattern,
        generate_constrained,
        get_charset,
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
        expand_variable,
        generate_from_template_file,
        render_template,
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

    extra_prefixes: list[str] | None = None
    raw_pfx = getattr(args, "prefixes", None)
    if raw_pfx:
        extra_prefixes = ["" if p == "EMPTY" else p for p in raw_pfx.split(",")]

    extra_suffixes: list[str] | None = None
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
    from wlf_modules.num2text import _normalise_lang, num2text_range, num2text_variants

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

    extra_prefixes: list[str] | None = None
    raw_pfx = getattr(args, "prefixes", None)
    if raw_pfx:
        parts = raw_pfx.split(",")
        extra_prefixes = ["" if p == "EMPTY" else p for p in parts]

    extra_suffixes: list[str] | None = None
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
    from wlf_modules.leet_permuter import (
        LEET_MEDIUM,
        leet_perm_wordlist,
        parse_custom_mapping,
    )

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




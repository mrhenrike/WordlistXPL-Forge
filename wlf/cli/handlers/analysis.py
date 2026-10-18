"""Command handlers: analysis."""
from __future__ import annotations

import argparse

from pathlib import Path

from wlf.cli.context import (
    Fore, Style, _GLOBAL_CTX, _TQDM, _tqdm, logger, is_shutdown, VERSION,
)
from typing import Optional, Any

from wlf.cli.utils import (
    _info, _ok, _warn, _err, _write_output,
    _effective_len_bounds, _format_bytes, _check_disk_space,
    _confirm_large, _count_generator_entries,
    _profile_preview_and_confirm, _resolve_path, _load_profile_file,
)


def cmd_analyze(args: argparse.Namespace) -> None:
    """Handler for wordlist analysis."""
    from wlf_modules.analyzer import (
        analyze_wordlist, format_report,
        analyze_masks, format_mask_report,
        export_stats_json, export_stats_csv,
        export_stats_markdown,
        extract_base_words,
    )

    _info(f"Analyzing: {args.wordlist}")
    try:
        metrics = analyze_wordlist(args.wordlist, top_n=args.top)
    except FileNotFoundError as e:
        _err(str(e))
        return

    mask_data: Optional[dict[str, Any]] = None
    do_masks = getattr(args, "masks", False)
    if do_masks:
        _info("Running Hashcat mask analysis...")
        try:
            mask_data = analyze_masks(args.wordlist, top_n=args.top)
        except Exception as exc:
            _warn(f"Mask analysis failed: {exc}")

    if getattr(args, "mask_optindex", False):
        from wlf_modules.analyzer import (
            maskgen_optindex,
            format_maskgen_report,
            export_masks_csv_pack,
        )
        _info("Running PACK maskgen optindex ranking...")
        try:
            if mask_data is None:
                mask_data = analyze_masks(args.wordlist, top_n=args.top)
            opt_rows = maskgen_optindex(
                mask_data,
                pps=int(getattr(args, "pps", 0) or 0),
                target_time_hrs=float(getattr(args, "time_budget", 1.0) or 1.0),
                use_gpu=bool(getattr(args, "use_gpu", False)),
            )
            print(format_maskgen_report(opt_rows))
            opt_out = getattr(args, "mask_csv", None)
            if opt_out:
                export_masks_csv_pack(opt_rows, opt_out)
                _ok(f"PACK mask CSV saved: {opt_out}")
        except Exception as exc:
            _warn(f"Mask optindex failed: {exc}")

    do_base = getattr(args, "base_words", False)
    base_output = getattr(args, "base_output", None)

    # ── Output format ──────────────────────────────────────────
    fmt = getattr(args, "format", "text") or "text"

    if fmt == "json":
        content = export_stats_json(metrics, args.wordlist, mask_data)
        print(content)
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            _ok(f"JSON report saved to: {args.output}")
    elif fmt == "csv":
        content = export_stats_csv(metrics, mask_data)
        print(content)
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            _ok(f"CSV report saved to: {args.output}")
    elif fmt == "markdown":
        content = export_stats_markdown(metrics, args.wordlist, mask_data)
        print(content)
        if args.output:
            Path(args.output).write_text(content, encoding="utf-8")
            _ok(f"Markdown report saved to: {args.output}")
    else:
        report = format_report(metrics, args.wordlist)
        print(report)
        if mask_data:
            print(format_mask_report(mask_data))
        if args.output:
            out_parts = [report]
            if mask_data:
                out_parts.append(format_mask_report(mask_data))
            Path(args.output).write_text("\n".join(out_parts), encoding="utf-8")
            _ok(f"Report saved to: {args.output}")

    # ── Base word extraction ───────────────────────────────────
    if do_base:
        _info("Extracting base words...")
        try:
            bases = extract_base_words(args.wordlist)
            _ok(f"Unique base words found: {len(bases):,}")
            if base_output:
                Path(base_output).write_text(
                    "\n".join(bases), encoding="utf-8"
                )
                _ok(f"Base words saved to: {base_output}")
            else:
                for b in bases[:50]:
                    print(f"  {b}")
                if len(bases) > 50:
                    print(f"  ... and {len(bases)-50} more")
        except Exception as exc:
            _warn(f"Base word extraction failed: {exc}")



def cmd_maskgen(args: argparse.Namespace) -> None:
    """Hashcat-style mask generation with chunked/GPU-aware batching."""
    from wlf_modules.gpu_expand import iter_mask, mask_keyspace, parse_mask
    from wlf_modules.resource_governor import governor_from_ctx

    mask = getattr(args, "mask", None) or "?l?l?d?d"
    slots = parse_mask(mask, getattr(args, "custom_charset1", None))
    total = mask_keyspace(slots)
    _info(f"Mask {mask} keyspace≈{total:,}")
    gov = governor_from_ctx(_GLOBAL_CTX)
    chunk = gov.gpu_batch_size(int(getattr(args, "chunk", 65536) or 65536))
    limit = int(getattr(args, "limit", 0) or _GLOBAL_CTX.get("limit") or 0)
    if not limit and total > 5_000_000 and not getattr(args, "force", False):
        _warn("Keyspace >5M — capping at 5M (pass --force or --limit).")
        limit = 5_000_000
    gen = iter_mask(mask, getattr(args, "custom_charset1", None), chunk, limit)
    count = _write_output(gen, getattr(args, "output", None), stream=True)
    _ok(f"Maskgen wrote {count:,} entries")



def cmd_password_dna(args: argparse.Namespace) -> None:
    """Handler for password DNA analysis and variant generation."""
    from wlf_modules.password_dna import handle_password_dna

    dna, gen = handle_password_dna(args, {})
    if not dna or not gen:
        _err("No passwords provided. Pass them as arguments or via --file.")
        return

    _info(f"Analyzing {dna.n} password(s)...")
    if getattr(args, "show_dna", False):
        print()
        print(dna.describe())
        print()

    depth = getattr(args, "depth", "normal")
    _info(f"Generating variants [depth={depth}]...")
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} candidates from {dna.n} password DNA(s)")



def cmd_dna_extract(args: argparse.Namespace) -> None:
    """Extract DNA profile + hashcat masks without full candidate explosion."""
    from wlf_modules.password_dna import PasswordDNA
    from wlf_modules.coverage_analyzer import hashcat_mask, structure_mask

    passwords: list[str] = list(getattr(args, "passwords", None) or [])
    if getattr(args, "file", None):
        try:
            with open(args.file, encoding="utf-8") as fh:
                for line in fh:
                    pw = line.strip()
                    if pw and not pw.startswith("#") and len(passwords) < 10:
                        passwords.append(pw)
        except FileNotFoundError:
            _err(f"File not found: {args.file}")
            return
    if not passwords:
        _err("No passwords provided.")
        return

    dna = PasswordDNA(passwords[:10])
    print(dna.describe())
    print()
    print("=== Per-sample masks ===")
    for pw in passwords[:10]:
        print(f"  {pw}")
        print(f"    structure={structure_mask(pw)}")
        print(f"    hcmask={hashcat_mask(pw)}")
    out = getattr(args, "output", None)
    if out:
        lines = [dna.describe(), ""]
        for pw in passwords[:10]:
            lines.append(f"{pw}\t{structure_mask(pw)}\t{hashcat_mask(pw)}")
        Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
        _ok(f"Wrote DNA extract: {out}")



def cmd_cover(args: argparse.Namespace) -> None:
    """Sample local corpus and report structural coverage / engine hints."""
    from wlf_modules.coverage_analyzer import handle_cover
    handle_cover(args, {})



def cmd_benchmark(args: argparse.Namespace) -> None:
    """Handler for wordlist quality benchmarking."""
    from wlf_modules.benchmark_suite import handle_benchmark
    gen = handle_benchmark(args, _GLOBAL_CTX)
    if gen:
        output = getattr(args, "output", None)
        if output:
            with open(output, "w", encoding="utf-8") as fh:
                for line in gen:
                    fh.write(line + "\n")
            _ok(f"Benchmark report saved: {output}")
        else:
            for line in gen:
                print(line)



def cmd_maya_rank(args: argparse.Namespace) -> None:
    """Rank a wordlist by MAYA-inspired cracking probability."""
    from wlf_modules.maya_ranker import rank_wordlist, format_rank_report

    source = getattr(args, "wordlist", None)
    if not source:
        _err("Provide a wordlist to rank.")
        return
    if not Path(source).is_file():
        _err(f"File not found: {source}")
        return

    output = args.output or str(Path(source).with_suffix(".ranked.lst"))
    backend = getattr(args, "backend", "auto") or "auto"
    result = rank_wordlist(
        input_path=source,
        output_path=output,
        use_gpu=bool(getattr(args, "use_gpu", False)),
        top_n=int(getattr(args, "top", 0) or 0),
        backend=backend,
        min_score=float(getattr(args, "min_score", 0.0) or 0.0),
    )
    print(format_rank_report(result))
    if args.output:
        _ok(f"Ranked wordlist saved: {output}")



def cmd_pattern_rank(args: argparse.Namespace) -> None:
    """Analyze wordlist patterns: keyboard walks, Hashcat masks, PTBR months."""
    from wlf_modules.pattern_ranker import analyze_wordlist, score_keyboard_walk, build_hashcat_mask

    path = getattr(args, "wordlist", None)
    if not path:
        _warn("pattern-rank requires a wordlist path.")
        return
    layout = getattr(args, "layout", "qwerty") or "qwerty"
    max_l = getattr(args, "max_lines", 500_000)

    _info(f"Analyzing {path} (layout={layout})...")
    result = analyze_wordlist(path, max_lines=max_l, layout=layout)

    print(f"\n  Pattern Analysis: {path}")
    print(f"  Total analyzed  : {result['total_analyzed']:,}")
    print(f"  Unique masks    : {result['unique_masks']:,}")
    print(f"  Keyboard walk   : {result['keyboard_walk_pct']:.1f}% of passwords")
    print(f"  PTBR months     : {result['ptbr_month_pct']:.1f}% of passwords")
    print("\n  Top 10 Hashcat masks:")
    for mask, count, pct in result["top_masks"][:10]:
        print(f"    {mask:<30} {count:>8}  ({pct:.1f}%)")
    print()



def cmd_anomaly_score(args: argparse.Namespace) -> None:
    """Rank passwords in a wordlist by anomaly score (most unusual first).

    Uses a native ensemble of IsolationForest-lite and HBOS-lite algorithms
    reimplemented without any external ML dependency.

    Example:
        wlf anomaly-score wordlist.lst --top 50
        wlf anomaly-score leak.txt --top 100 --output rare_passwords.txt
    """
    from wlf_modules.anomaly_scorer import score_wordlist

    path = getattr(args, "wordlist", None)
    if not path:
        _warn("anomaly-score requires a wordlist path as argument.")
        return

    top_n = getattr(args, "top", 0)
    max_lines = getattr(args, "max_lines", 100_000)
    output = getattr(args, "output", None)

    try:
        results = score_wordlist(path, top_n=top_n, max_lines=max_lines)
    except FileNotFoundError as exc:
        _warn(str(exc))
        return

    lines_out = [f"{score:.4f}\t{pw}" for pw, score in results]

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(pw for pw, _ in results), encoding="utf-8")
        _info(f"Saved {len(results)} entries to: {out_path}")
    else:
        print(f"{'Score':>8}  Password")
        print("-" * 40)
        for pw, score in results:
            print(f"{score:>8.4f}  {pw}")

    _info(f"Scored {len(results)} password(s). Higher score = more anomalous.")



def cmd_strength(args: argparse.Namespace) -> None:
    """Handler for zxcvbn-style password strength estimation."""
    from wlf_modules.entropy_strength import handle_strength

    res = handle_strength(args, _GLOBAL_CTX)
    if not res:
        return
    _kind, lines = res
    output = getattr(args, "output", None)
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")
        _ok(f"Strength report saved: {output}")
    else:
        for line in lines:
            print(line)



def cmd_hash_id(args: argparse.Namespace) -> None:
    """Handler for hash identification."""
    from wlf_modules.hash_tools import handle_hash_id

    gen = handle_hash_id(args, _GLOBAL_CTX)
    if gen is None:
        return
    output = getattr(args, "output", None)
    if output:
        Path(output).write_text("\n".join(gen) + "\n", encoding="utf-8")
        _ok(f"Saved: {output}")
    else:
        for line in gen:
            print(line)



def cmd_hash_gen(args: argparse.Namespace) -> None:
    """Handler for hash generation over a wordlist."""
    from wlf_modules.hash_tools import handle_hash_gen

    gen = handle_hash_gen(args, _GLOBAL_CTX)
    if gen is None:
        return
    count = _write_output(gen, getattr(args, "output", None))
    _ok(f"Hashes generated: {count:,}")



def cmd_hcmask(args: argparse.Namespace) -> None:
    """Handler for hashcat .hcmask export."""
    from wlf_modules.hash_tools import export_hcmask

    wordlist = getattr(args, "wordlist", None)
    output = getattr(args, "output", None)
    if not wordlist or not output:
        _err("hcmask requires a wordlist and -o OUTPUT.hcmask")
        return
    try:
        stats = export_hcmask(
            wordlist, output,
            top_n=int(getattr(args, "top", 0) or 0),
            min_count=int(getattr(args, "min_count", 1) or 1),
        )
    except FileNotFoundError as exc:
        _err(str(exc))
        return
    _ok(
        f"hcmask export: {stats['written']} mask(s) from {stats['total']:,} "
        f"entries ({stats['unique_masks']} unique) -> {stats['output']}"
    )



def cmd_evaluate(args: argparse.Namespace) -> None:
    """Handler for guess-number and coverage evaluation."""
    from wlf_modules.eval_harness import handle_evaluate

    res = handle_evaluate(args, _GLOBAL_CTX)
    if not res:
        return
    _kind, lines = res
    output = getattr(args, "output", None)
    if output:
        Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")
        _ok(f"Evaluation report saved: {output}")
    else:
        for line in lines:
            print(line)



def cmd_score(args: argparse.Namespace) -> None:
    """Score and explain a password."""
    pw = getattr(args, "password", None) or (getattr(args, "args", [None])[0] if hasattr(args, "args") else None)
    if not pw:
        _warn("Usage: wlf score <password>")
        return
    from wlf_modules.explainer import explain
    exp = explain(pw, engine="heuristic", raw_score=0.0)
    print(exp.format(verbose=True))



def cmd_explain_cmd(args: argparse.Namespace) -> None:
    """Alias for score — explain a password."""
    cmd_score(args)


def cmd_compare(args: argparse.Namespace) -> None:
    """Handler for wordlist comparison / overlap metrics."""
    from wlf_modules.compare_engine import handle_compare

    file_a = getattr(args, "file_a", None)
    file_b = getattr(args, "file_b", None)

    if not file_a or not file_b:
        _warn("Usage: wlf compare <file_a> <file_b>")
        return

    _info(f"Comparing: {file_a} vs {file_b}")
    gen = handle_compare(args, _GLOBAL_CTX)
    if gen is None:
        _err("Comparison failed.")
        return

    output = getattr(args, "output", None)
    if output:
        count = _write_output(gen, output)
        _ok(f"Report saved to {output}")
    else:
        for line in gen:
            print(line)


def cmd_hibp(args: argparse.Namespace) -> None:
    """Handler for HIBP breach checking."""
    from wlf_modules.hibp_checker import handle_hibp

    wordlist = getattr(args, "wordlist", None)
    if not wordlist:
        _warn("Usage: wlf hibp <wordlist>")
        return

    offline = getattr(args, "offline", None)
    mode = "offline" if offline else "online (HIBP API)"
    _info(f"HIBP check ({mode}): {wordlist}")
    gen = handle_hibp(args, _GLOBAL_CTX)
    if gen is None:
        _err("HIBP check failed.")
        return

    output = getattr(args, "output", None)
    if output:
        count = _write_output(gen, output)
        _ok(f"Report saved to {output}")
    else:
        for line in gen:
            print(line)


def cmd_intelx(args: argparse.Namespace) -> None:
    """Handler for IntelX leak/breach search."""
    from wlf_modules.intelx_checker import handle_intelx

    query = getattr(args, "query", None)
    query_file = getattr(args, "query_file", None)
    if not query and not query_file:
        _warn("Usage: wlf intelx --query <term> or --query-file <file>")
        return

    _info("IntelX search")
    gen = handle_intelx(args, _GLOBAL_CTX)
    if gen is None:
        _err("IntelX search failed.")
        return

    output = getattr(args, "output", None)
    if output:
        count = _write_output(gen, output)
        _ok(f"Report saved to {output}")
    else:
        for line in gen:
            print(line)


def cmd_hcmon(args: argparse.Namespace) -> None:
    """Handler for Hashcat/JtR cracking session monitoring."""
    from wlf_modules.hashcat_monitor import handle_hcmon

    tool = getattr(args, "tool", "hashcat")
    _info(f"Cracker monitor ({tool})")
    gen = handle_hcmon(args, _GLOBAL_CTX)
    if gen is None:
        _err("No status data found. Provide --session, --status-file, or --restore-file.")
        return

    output = getattr(args, "output", None)
    if output:
        count = _write_output(gen, output)
        _ok(f"Report saved to {output}")
    else:
        for line in gen:
            print(line)


def cmd_entropy(args: argparse.Namespace) -> None:
    """Handler for entropy distribution visualization."""
    from wlf_modules.entropy_viz import handle_entropy

    wordlist = getattr(args, "wordlist", None)
    if not wordlist:
        _warn("Usage: wlf entropy <wordlist>")
        return

    _info(f"Entropy analysis: {wordlist}")
    gen = handle_entropy(args, _GLOBAL_CTX)
    if gen is None:
        _err("Entropy analysis failed.")
        return

    output = getattr(args, "output", None)
    if output:
        count = _write_output(gen, output)
        _ok(f"Report saved to {output}")
    else:
        for line in gen:
            print(line)


def cmd_cluster(args: argparse.Namespace) -> None:
    """Handler for password clustering / classification."""
    from wlf_modules.cluster_engine import handle_cluster

    wordlist = getattr(args, "wordlist", None)
    if not wordlist:
        _warn("Usage: wlf cluster <wordlist>")
        return

    _info(f"Clustering: {wordlist}")
    gen = handle_cluster(args, _GLOBAL_CTX)
    if gen is None:
        _err("Clustering failed.")
        return

    output = getattr(args, "output", None)
    if output:
        count = _write_output(gen, output)
        _ok(f"Report saved to {output}")
    else:
        for line in gen:
            print(line)


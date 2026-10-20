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

    [f"{score:.4f}\t{pw}" for pw, score in results]

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
    """Alias for score  - explain a password."""
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
        _write_output(gen, output)
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
        _write_output(gen, output)
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
        _write_output(gen, output)
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
        _write_output(gen, output)
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
        _write_output(gen, output)
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
        _write_output(gen, output)
        _ok(f"Report saved to {output}")
    else:
        for line in gen:
            print(line)


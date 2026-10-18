"""Command handlers: infra."""
from __future__ import annotations

import argparse

from pathlib import Path

from wlf.cli.context import (
    Fore, Style, _GLOBAL_CTX, _TQDM, _tqdm, logger, is_shutdown, VERSION,
)
from typing import Any, Generator

from wlf.cli.utils import (
    _info, _ok, _warn, _err, _write_output,
    _effective_len_bounds, _format_bytes, _check_disk_space,
    _confirm_large, _count_generator_entries,
    _profile_preview_and_confirm, _resolve_path, _load_profile_file,
)


def cmd_strategy(args: argparse.Namespace) -> None:
    """Plan mutation strategies (PBMP-lite) from a profile."""
    from wlf_modules.profiler import load_profile_yaml
    from wlf_modules.strategy_engine import (
        bayesian_structure_priors,
        format_plan,
        models_on_disk,
        plan_from_profile,
    )

    pf = getattr(args, "profile_file", None)
    if not pf:
        _err("--profile-file required")
        return
    profile = load_profile_yaml(pf)
    mods = models_on_disk(Path("."))
    plan = plan_from_profile(
        profile,
        has_model_markov=mods["markov"],
        has_model_pcfg=mods["pcfg"],
        has_neural=mods["neural"],
    )
    priors = bayesian_structure_priors(profile)
    text = format_plan(plan, priors)
    print(text)
    out = getattr(args, "output", None)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
        _ok(f"Wrote plan: {out}")

    if getattr(args, "run", False):
        # Execute top engines that we can without heavy deps
        from wlf_modules.semantic_pcfg import generate_semantic
        from wlf_modules.pattern_engine import expand_variable, render_template

        for eng in plan.engines[:3]:
            name = eng["strategy"]
            lim = int(eng.get("limit", 10_000))
            _info(f"Running strategy={name} limit={lim}")
            if name == "semantic_pcfg":
                gen = generate_semantic(profile, max_candidates=lim)
                n = _write_output(gen, getattr(args, "output_wordlist", None), stream=True)
                _ok(f"{name}: {n:,}")
            elif name == "pattern_templates":
                vars_ = eng.get("vars") or {}
                tmpls = eng.get("templates") or ["{company}#{pet}{yy}"]

                def _g() -> Generator[str, None, None]:
                    for t in tmpls:
                        mapping = {
                            k: expand_variable(k, str(v))
                            for k, v in vars_.items()
                        }
                        mapping = {
                            k: (v if isinstance(v, list) else [str(v)])
                            for k, v in mapping.items()
                        }
                        yield from render_template(t, mapping)

                n = _write_output(_g(), getattr(args, "output_wordlist", None), stream=True)
                _ok(f"{name}: {n:,}")



def cmd_bandit(args: argparse.Namespace) -> None:
    """UCB1 router over engines with proxy rewards."""
    from wlf_modules.bandit_router import BanditRouter, proxy_reward
    from wlf_modules.gpu_expand import expand_leet_batch
    from wlf_modules.semantic_pcfg import generate_semantic

    rounds = int(getattr(args, "rounds", 5) or 5)
    seeds = list(getattr(args, "seeds", None) or ["BrandX", "OzZY", "2026"])
    router = BanditRouter(c=float(getattr(args, "ucb_c", 1.414) or 1.414))
    profile = {
        "company_name": seeds[0] if seeds else "BrandX",
        "pets": [{"name": seeds[1] if len(seeds) > 1 else "PetX", "year": 2026}],
        "keywords": seeds,
        "special_dates": ["2026", "2025"],
        "leet_mode": "medium",
    }
    for r in range(rounds):
        arm = router.select()
        cands: list[str] = []
        if arm in ("pcfg", "pattern", "rules"):
            cands = list(generate_semantic(profile, max_candidates=2000))
            if arm == "rules":
                cands = list(expand_leet_batch(cands[:200], mode="basic", max_per_word=8))
        elif arm == "markov":
            cands = [s + str(i) for i, s in enumerate(seeds * 100)]
        elif arm == "prince":
            from itertools import product
            cands = ["".join(p) for p in product(seeds, ["@", "#", ""], ["2024", "2025", "2026"])]
        reward = proxy_reward(cands, seeds)
        router.update(arm, reward)
        _info(f"round {r+1}/{rounds} arm={arm} reward={reward:.4f} n={len(cands)}")
    print(router.describe())
    best = max(router.stats.items(), key=lambda kv: kv[1].mean)
    _ok(f"Preferred arm: {best[0]} (mean={best[1].mean:.4f})")



def cmd_sysinfo(args: argparse.Namespace) -> None:
    """Show hardware profile and compute backend status."""
    from wlf_modules.hw_profiler import get_hw_profile
    from wlf_modules.compute_backend import auto_select_backend
    from wlf_modules.thread_pool import (
        DEFAULT_THREADS, MIN_THREADS, MAX_THREADS,
        WARN_THRESHOLD, ALERT_THRESHOLD,
    )

    compute_mode = _GLOBAL_CTX.get("compute_mode", "auto")

    _info("Detecting hardware profile...")
    hw = get_hw_profile(force=True)

    print()
    print(f"  CPU   : {hw.cpu_model}")
    print(f"  Cores : {hw.cpu_cores} physical / {hw.cpu_threads} logical")
    print(f"  RAM   : {hw.ram_total_mb:,} MB total / {hw.ram_avail_mb:,} MB available")

    if hw.has_gpu():
        for gpu in hw.gpus:
            print(f"  GPU   : {gpu.one_liner()}")  # type: ignore[attr-defined]
    else:
        print("  GPU   : None detected (CPU-only mode)")

    print()
    backend = auto_select_backend(compute_mode, hw)
    print(f"  Compute backend : {backend.name.upper()}")
    print(f"  Device info     : {backend.device_info}")
    print(f"  ML enabled      : {_GLOBAL_CTX.get('use_ml', True)}")

    cur_threads = _GLOBAL_CTX.get("threads", DEFAULT_THREADS)
    rec_threads = hw.recommended_threads()
    print()
    print(f"  Threads (active) : {cur_threads}  [range: {MIN_THREADS}-{MAX_THREADS}, recommended: {rec_threads}]")
    if cur_threads >= ALERT_THRESHOLD:
        print(f"  {Fore.RED}[ALERT]{Style.RESET_ALL} Thread count {cur_threads} is very high - monitor system resources.")
    elif cur_threads >= WARN_THRESHOLD:
        print(f"  {Fore.YELLOW}[WARN]{Style.RESET_ALL} Thread count {cur_threads} exceeds recommended limit.")
    print()

    stress_n = getattr(args, "crc32_stress", 0) or 0
    if stress_n > 0:
        from wlf_modules.benchmark_suite import stress_crc32_dedup, format_crc32_stress_report
        _info(f"Running CRC32 dedup stress test ({stress_n:,} lines)...")
        result = stress_crc32_dedup(stress_n)
        print(format_crc32_stress_report(result))



def cmd_train(args: argparse.Namespace) -> None:
    """
    Train the ML pattern model from available data sources.

    Privacy: only structural patterns are extracted - no raw usernames,
    passwords, company names, or personal data are ever stored in the model.
    """
    from wlf_modules.ml_patterns import PatternModel, DEFAULT_MODEL_FILE

    model = PatternModel()
    trained_any = False

    # ── CSV sources ────────────────────────────────────────────────────────────
    for csv_path in (getattr(args, "csv", None) or []):
        p = _resolve_path(csv_path)
        if not p or not p.exists():
            _warn(f"CSV not found: {csv_path}")
            continue
        _info(f"Training from CSV: {p.name}")
        stats = model.train_from_csv(
            str(p),
            userid_col     = getattr(args, "uid_col",  "userid"),
            employeeid_col = getattr(args, "eid_col",  "employeeid"),
            workemail_col  = getattr(args, "mail_col", "workemail"),
            max_rows       = getattr(args, "max_rows", 0),
        )
        _info(f"  → {stats['uid_samples']:,} uid samples from {stats['processed_rows']:,} rows")
        trained_any = True

    # ── Password wordlists ────────────────────────────────────────────────────
    for wl_path in (getattr(args, "wordlist", None) or []):
        p = _resolve_path(wl_path)
        if not p or not p.exists():
            _warn(f"Wordlist not found: {wl_path}")
            continue
        _info(f"Training from password wordlist: {p.name}")
        stats = model.train_from_wordlist(
            str(p), mode="password",
            max_lines=getattr(args, "max_lines", 500_000),
            source_label=p.name,
        )
        _info(f"  → {stats['processed']:,} samples")
        trained_any = True

    # ── Username lists ────────────────────────────────────────────────────────
    for ul_path in (getattr(args, "usernames", None) or []):
        p = _resolve_path(ul_path)
        if not p or not p.exists():
            _warn(f"Username list not found: {ul_path}")
            continue
        _info(f"Training from username list: {p.name}")
        stats = model.train_from_wordlist(
            str(p), mode="username",
            max_lines=getattr(args, "max_lines", 200_000),
            source_label=p.name,
        )
        _info(f"  → {stats['processed']:,} samples")
        trained_any = True

    # ── Auto-discover local wordlists if --auto flag is set ───────────────────
    if getattr(args, "auto", False):
        wfh_root = _resolve_path(".")
        auto_sources = [
            ("generated/passwords.lst", "password", 300_000),
            ("generated/users.lst", "username", 50_000),
        ]
        for rel, mode, limit in auto_sources:
            p = wfh_root / rel if wfh_root else None
            if p and p.exists():
                _info(f"Auto-training from {p.name} (mode={mode})")
                stats = model.train_from_wordlist(
                    str(p), mode=mode,
                    max_lines=limit,
                    source_label=p.name,
                )
                _info(f"  → {stats['processed']:,} samples")
                trained_any = True

    # ── SecLists corpus ──────────────────────────────────────────────────────────
    seclists_flag = getattr(args, "seclists", None)
    if seclists_flag:
        from wlf_modules.seclists_trainer import find_seclists_root, train_from_seclists

        hint = None if seclists_flag == "auto" else seclists_flag
        sl_root = find_seclists_root(hint)
        if sl_root:
            _info(f"SecLists root: {sl_root}")
            sl_cats = getattr(args, "seclists_categories", None)
            sl_summary = train_from_seclists(
                model, sl_root, categories=sl_cats,
            )
            pw_f = sl_summary.get("password_files", 0)
            pw_s = sl_summary.get("password_samples", 0)
            un_f = sl_summary.get("username_files", 0)
            un_s = sl_summary.get("username_samples", 0)
            fr_f = sl_summary.get("frequency_files", 0)
            fr_s = sl_summary.get("frequency_samples", 0)
            skipped = sl_summary.get("skipped", [])

            _info(f"  SecLists passwords:  {pw_f} files, {pw_s:,} samples")
            _info(f"  SecLists usernames:  {un_f} files, {un_s:,} samples")
            _info(f"  SecLists frequency:  {fr_f} files, {fr_s:,} samples")
            if skipped:
                _warn(f"  Skipped (not found): {', '.join(skipped)}")
            if pw_f + un_f + fr_f > 0:
                trained_any = True
        else:
            _warn("SecLists not found. Use --seclists PATH or place SecLists alongside WFH.")

    if not trained_any:
        _warn("No training data provided. Use --csv, --wordlist, --usernames, --auto, or --seclists.")
        return

    # ── Save model ─────────────────────────────────────────────────────────────
    out_path = getattr(args, "output", None) or str(DEFAULT_MODEL_FILE)
    saved = model.save(out_path)
    print()
    _info(f"Model saved: {saved}")
    print(model.describe())



def cmd_pipeline(args: argparse.Namespace) -> None:
    """Run a YAML pipeline spec file."""
    pipeline_file = getattr(args, "pipeline_file", None)
    if not pipeline_file:
        _warn("Usage: wlf pipeline <pipeline.yaml> [-o output.txt]")
        return
    try:
        from wlf_modules.pipeline_dsl import execute_pipeline
        gen = execute_pipeline(pipeline_file, _GLOBAL_CTX)
        count = _write_output(gen, getattr(args, "output", None), stream=True)
        _ok(f"Pipeline wrote {count:,} candidates")
    except Exception as exc:
        _err(f"Pipeline error: {exc}")



def cmd_session(args: argparse.Namespace) -> None:
    """Manage sessions: list / show / resume."""
    from wlf_modules.session_manager import SessionManager
    import time as _time

    mgr = SessionManager()
    sub = getattr(args, "session_sub", None) or "list"
    if sub == "list":
        sessions = mgr.list_sessions()
        if not sessions:
            _info("No saved sessions.")
            return
        for s in sessions:
            updated = getattr(s, "updated_at", 0) or 0
            try:
                stamp = _time.strftime("%Y-%m-%dT%H:%M:%S", _time.localtime(float(updated)))
            except (TypeError, ValueError, OSError):
                stamp = str(updated)
            print(f"  {s.session_id}  emitted={s.emitted:,}  updated={stamp}")
    elif sub == "show":
        sid = getattr(args, "session_id", None)
        if not sid:
            _warn("Usage: wlf session show <session_id>")
            return
        try:
            st = mgr.load(sid)
            print(f"session_id : {st.session_id}")
            print(f"label      : {st.label!r}")
            print(f"emitted    : {st.emitted:,}")
            print(f"bytes      : {st.bytes_written:,}")
            print(f"chunk      : {st.chunk_index}")
            print(f"created_at : {st.created_at}")
            print(f"updated_at : {st.updated_at}")
            if st.pipeline_config:
                print(f"pipeline   : {st.pipeline_config}")
            if st.pbmp_weights:
                print(f"pbmp       : {st.pbmp_weights}")
        except FileNotFoundError as exc:
            _err(str(exc))
    elif sub == "resume":
        sid = getattr(args, "session_id", None)
        if not sid:
            _warn("Usage: wlf session resume <session_id>")
            return
        try:
            ctx = mgr.resume_ctx(sid)
            _GLOBAL_CTX.update(ctx)
            _info(
                f"Session {sid} resumed "
                f"({ctx.get('_resume_emitted', ctx.get('emitted', 0)):,} candidates previously emitted)"
            )
        except FileNotFoundError as exc:
            _err(str(exc))
    else:
        _warn(f"Unknown session sub-command: {sub}. Use list, show, or resume.")



def cmd_serve(args: argparse.Namespace) -> None:
    """Start the REST API server."""
    host = getattr(args, "host", None) or "127.0.0.1"
    port = int(getattr(args, "port", None) or 8771)
    api_key = getattr(args, "api_key", None) or ""
    _info(f"WordlistXPL-Forge API starting on http://{host}:{port}")
    _info("AUTHORIZED USE ONLY")
    try:
        from wlf_modules.api_server import run_server
        run_server(host=host, port=port, api_key=api_key)
    except Exception as exc:
        _err(f"API server error: {exc}")



def cmd_plugin(args: argparse.Namespace) -> None:
    """Plugin management: list, run, discover."""
    from wlf_modules.plugin_manager import auto_discover, describe_all, run_plugin, list_plugins
    sub = getattr(args, "plugin_sub", None) or "list"
    if sub == "list":
        auto_discover()
        desc = describe_all()
        print(desc if desc else "No plugins loaded.")
    elif sub == "run":
        name = getattr(args, "plugin_name", None)
        if not name:
            _warn("Usage: wlf plugin run <name>")
            return
        auto_discover()
        profile: dict[str, Any] = {}
        limit = _GLOBAL_CTX.get("limit") or 10_000
        gen = (pw for pw, _ in run_plugin(name, profile, {**_GLOBAL_CTX, "limit": limit}))
        _write_output(gen, getattr(args, "output", None), stream=True)
    else:
        _warn(f"Unknown plugin sub-command: {sub}. Use list or run.")



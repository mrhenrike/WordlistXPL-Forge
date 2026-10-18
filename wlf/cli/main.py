"""Main entry point and command dispatch."""
from __future__ import annotations

import logging
import time

from wlf.cli.context import (
    Fore, Style, _GLOBAL_CTX, BANNER, logger,
)
from wlf.cli.utils import _info, _warn
from wlf.cli.config import load_config, apply_config_to_ctx
from wlf.cli.parser import build_parser
from wlf.cli.menu import interactive_menu
from wlf.cli.handlers import (
    cmd_charset, cmd_pattern, cmd_profile, cmd_corp, cmd_corp_users,
    cmd_phone, cmd_scrape, cmd_ocr, cmd_extract, cmd_leet, cmd_leet_perm,
    cmd_xor, cmd_analyze, cmd_merge, cmd_dns, cmd_pharma, cmd_sanitize,
    cmd_reverse, cmd_train, cmd_corp_prefixes, cmd_sysinfo, cmd_mangle,
    cmd_improve, cmd_maya_rank, cmd_default_creds, cmd_isp_keygen,
    cmd_password_dna, cmd_dna_extract, cmd_cover, cmd_replay, cmd_emit,
    cmd_maskgen, cmd_strategy, cmd_bandit, cmd_combiner, cmd_pcfg,
    cmd_markov, cmd_kwalk, cmd_phonetic, cmd_rulegen, cmd_benchmark, cmd_prince,
    cmd_anomaly_score, cmd_osint_perm, cmd_cupp, cmd_pattern_rank,
    cmd_scrape_target, cmd_br_names, cmd_iwlgen, cmd_phrase, cmd_mutate,
    cmd_num2text, cmd_rules, cmd_affix, cmd_dedup, cmd_subtract,
    cmd_split, cmd_keyspace, cmd_neural, cmd_strength, cmd_hash_id,
    cmd_hash_gen, cmd_hcmask, cmd_osint, cmd_passphrase, cmd_evaluate,
    cmd_curate, cmd_pipeline, cmd_session, cmd_score, cmd_explain_cmd,
    cmd_serve, cmd_br_deep, cmd_pbmp, cmd_evolve, cmd_graph_expand,
    cmd_temporal_model, cmd_domain_pcfg, cmd_plugin, cmd_vae_interp,
    cmd_test,
)


def main() -> None:
    """Main entry point for wlf.py."""
    print(BANNER)

    # ── Load persistent config (CLI flags override) ───────────────────────────
    _cfg = load_config()
    apply_config_to_ctx(_GLOBAL_CTX, _cfg)

    parser = build_parser()
    args = parser.parse_args()

    if args.verbose if hasattr(args, "verbose") else False:
        logging.getLogger().setLevel(logging.DEBUG)

    # ── Apply locale ──────────────────────────────────────────────────────────
    _raw_lang = getattr(args, "lang", None)
    if _raw_lang:
        from wlf_modules.i18n import set_session_locale as _set_locale
        _active_locale = _set_locale(_raw_lang)
        _GLOBAL_CTX["locale"] = _active_locale
    else:
        _GLOBAL_CTX["locale"] = _cfg.get("locale", "en")

    # ── Apply global execution context (CLI overrides config) ─────────────────
    from wlf_modules.thread_pool import validate_thread_count, DEFAULT_THREADS
    from wlf_modules.compute_backend import set_backend

    raw_threads    = getattr(args, "threads", None) or _cfg.get("threads", DEFAULT_THREADS)
    compute_mode   = getattr(args, "compute", "auto") or "auto"
    global_use_ml  = not getattr(args, "no_ml_global", False)
    global_limit   = getattr(args, "limit", 0) or 0
    global_timeout = getattr(args, "timeout", 0) or 0
    global_min_len = getattr(args, "global_min_len", 0) or 0
    global_max_len = getattr(args, "global_max_len", 0) or 0

    # Validate and store thread count
    threads = validate_thread_count(raw_threads, clamp=True)
    _GLOBAL_CTX["threads"]      = threads
    _GLOBAL_CTX["compute_mode"] = compute_mode
    _GLOBAL_CTX["use_ml"]       = global_use_ml
    _GLOBAL_CTX["limit"]        = global_limit
    _GLOBAL_CTX["timeout"]      = global_timeout
    _GLOBAL_CTX["start_time"]   = time.time()
    _GLOBAL_CTX["min_len"]      = global_min_len
    _GLOBAL_CTX["max_len"]      = global_max_len
    _GLOBAL_CTX["ram_budget_pct"] = float(getattr(args, "ram_budget_pct", 50) or 50)
    _GLOBAL_CTX["vram_budget_mb"] = int(getattr(args, "vram_budget_mb", 4096) or 4096)
    _GLOBAL_CTX["chunk_lines"] = int(getattr(args, "chunk_lines", 0) or 0)
    _GLOBAL_CTX["chunk_bytes"] = int(getattr(args, "chunk_bytes", 0) or 0)
    _GLOBAL_CTX["stream"] = bool(getattr(args, "stream_global", False))
    _GLOBAL_CTX["enforce_safe_default"] = bool(getattr(args, "safe_default_limit", False))

    if global_min_len or global_max_len:
        parts = []
        if global_min_len:
            parts.append(f"min={global_min_len}")
        if global_max_len:
            parts.append(f"max={global_max_len}")
        _info(f"Length filter active: {', '.join(parts)} (global)")

    # Initialize compute backend (lazy - only if any module uses it)
    if compute_mode != "auto" or threads > 1:
        try:
            backend = set_backend(compute_mode)
            if compute_mode != "auto":
                _info(f"Compute: {backend.name.upper()} | {backend.device_info}")
        except Exception:
            pass

    # No subcommand → interactive menu
    if not args.command:
        try:
            while True:
                interactive_menu()
                print()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            _info("Exiting.")
        return

    # Dispatch to subcommand handler
    handlers = {
        "charset":    cmd_charset,
        "pattern":    cmd_pattern,
        "profile":    cmd_profile,
        "corp":       cmd_corp,
        "corp-users": cmd_corp_users,
        "phone":      cmd_phone,
        "scrape":   cmd_scrape,
        "ocr":      cmd_ocr,
        "extract":  cmd_extract,
        "leet":       cmd_leet,
        "leet-perm":  cmd_leet_perm,
        "xor":      cmd_xor,
        "analyze":  cmd_analyze,
        "merge":    cmd_merge,
        "dns":      cmd_dns,
        "pharma":   cmd_pharma,
        "sanitize": cmd_sanitize,
        "reverse":  cmd_reverse,
        "train":         cmd_train,
        "corp-prefixes": cmd_corp_prefixes,
        "sysinfo":       cmd_sysinfo,
        "mangle":        cmd_mangle,
        "improve":       cmd_improve,
        "maya-rank":     cmd_maya_rank,
        "default-creds": cmd_default_creds,
        "isp-keygen":    cmd_isp_keygen,
        "password-dna":  cmd_password_dna,
        "dna-extract":   cmd_dna_extract,
        "cover":         cmd_cover,
        "replay":        cmd_replay,
        "emit":          cmd_emit,
        "maskgen":       cmd_maskgen,
        "strategy":      cmd_strategy,
        "bandit":        cmd_bandit,
        "combiner":      cmd_combiner,
        "pcfg":          cmd_pcfg,
        "markov":        cmd_markov,
        "kwalk":         cmd_kwalk,
        "phonetic":      cmd_phonetic,
        "rulegen":       cmd_rulegen,
        "benchmark":     cmd_benchmark,
        "prince":        cmd_prince,
        "anomaly-score": cmd_anomaly_score,
        "osint-perm":    cmd_osint_perm,
        "cupp":          cmd_cupp,
        "pattern-rank":  cmd_pattern_rank,
        "scrape-target": cmd_scrape_target,
        "br-names":      cmd_br_names,
        "iwlgen":        cmd_iwlgen,
        "phrase":        cmd_phrase,
        "mutate":        cmd_mutate,
        "num2text":      cmd_num2text,
        "rules":         cmd_rules,
        "affix":         cmd_affix,
        "dedup":         cmd_dedup,
        "subtract":      cmd_subtract,
        "split":         cmd_split,
        "keyspace":      cmd_keyspace,
        "neural":        cmd_neural,
        "strength":      cmd_strength,
        "hash-id":       cmd_hash_id,
        "hash-gen":      cmd_hash_gen,
        "hcmask":        cmd_hcmask,
        "osint":         cmd_osint,
        "passphrase":    cmd_passphrase,
        "evaluate":      cmd_evaluate,
        "curate":        cmd_curate,
    }

    # ── v2.0 new commands ──────────────────────────────────────────────────
    handlers["pipeline"]      = cmd_pipeline
    handlers["session"]       = cmd_session
    handlers["score"]         = cmd_score
    handlers["explain"]       = cmd_explain_cmd
    handlers["serve"]         = cmd_serve
    handlers["br-deep"]       = cmd_br_deep
    handlers["pbmp"]          = cmd_pbmp
    handlers["evolve"]        = cmd_evolve
    handlers["graph-expand"]  = cmd_graph_expand
    handlers["temporal-model"] = cmd_temporal_model
    handlers["domain-pcfg"]   = cmd_domain_pcfg
    handlers["plugin"]        = cmd_plugin
    handlers["vae-interp"]    = cmd_vae_interp
    handlers["test"]          = cmd_test

    handler = handlers.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            print("\n")
            _warn("Interrupted by user.")
    else:
        parser.print_help()


# ── v2.0 command handlers ─────────────────────────────────────────────────────


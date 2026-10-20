"""Main entry point and command dispatch."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable

from wlf.cli.config import apply_config_to_ctx, load_config
from wlf.cli.context import (
    _GLOBAL_CTX,
    BANNER,
)
from wlf.cli.handlers import (
    cmd_affix,
    cmd_analyze,
    cmd_anomaly_score,
    cmd_bandit,
    cmd_benchmark,
    cmd_br_deep,
    cmd_br_names,
    cmd_charset,
    cmd_cluster,
    cmd_combiner,
    cmd_combo,
    cmd_compare,
    cmd_corp,
    cmd_corp_conv,
    cmd_corp_prefixes,
    cmd_corp_users,
    cmd_cover,
    cmd_cupp,
    cmd_curate,
    cmd_dedup,
    cmd_default_creds,
    cmd_dna_extract,
    cmd_dns,
    cmd_domain_pcfg,
    cmd_emit,
    cmd_entropy,
    cmd_evaluate,
    cmd_evolve,
    cmd_explain_cmd,
    cmd_extract,
    cmd_finetune_data,
    cmd_graph_expand,
    cmd_hash_gen,
    cmd_hash_id,
    cmd_hcmask,
    cmd_hcmon,
    cmd_hibp,
    cmd_improve,
    cmd_intelx,
    cmd_isp_keygen,
    cmd_iwlgen,
    cmd_keyspace,
    cmd_kwalk,
    cmd_leet,
    cmd_leet_perm,
    cmd_locale,
    cmd_mangle,
    cmd_markov,
    cmd_maskgen,
    cmd_maya_rank,
    cmd_merge,
    cmd_mutate,
    cmd_neural,
    cmd_nflow,
    cmd_num2text,
    cmd_ocr,
    cmd_osint,
    cmd_osint_perm,
    cmd_passphrase,
    cmd_password_dna,
    cmd_pattern,
    cmd_pattern_rank,
    cmd_pbmp,
    cmd_pcfg,
    cmd_pharma,
    cmd_phone,
    cmd_phonetic,
    cmd_phrase,
    cmd_pipeline,
    cmd_plugin,
    cmd_prince,
    cmd_profile,
    cmd_replay,
    cmd_reverse,
    cmd_rule_mine,
    cmd_rulegen,
    cmd_rules,
    cmd_sanitize,
    cmd_score,
    cmd_scrape,
    cmd_scrape_target,
    cmd_serve,
    cmd_session,
    cmd_split,
    cmd_strategy,
    cmd_strength,
    cmd_subtract,
    cmd_sysinfo,
    cmd_temporal_model,
    cmd_test,
    cmd_train,
    cmd_vae_interp,
    cmd_xor,
)
from wlf.cli.menu import interactive_menu
from wlf.cli.parser import build_parser
from wlf.cli.utils import _err, _info, _warn


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
    from wlf_modules.compute_backend import set_backend
    from wlf_modules.thread_pool import DEFAULT_THREADS, validate_thread_count

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
    _GLOBAL_CTX["checkpoint"] = bool(getattr(args, "checkpoint", False))

    resume_id = getattr(args, "resume_id", None)
    if resume_id:
        from wlf_modules.session_manager import get_manager
        try:
            ctx = get_manager().resume_ctx(resume_id)
            _GLOBAL_CTX.update(ctx)
            _info(f"Resuming session {resume_id} (skipping {ctx.get('_resume_emitted', 0):,} entries)")
        except FileNotFoundError:
            _err(f"Session not found: {resume_id}")
            return

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

    _handlers = _build_dispatch_table()
    fn = _handlers.get(args.command)
    if fn is not None:
        try:
            fn(args)
        except KeyboardInterrupt:
            print("\n")
            _warn("Interrupted by user.")
    else:
        parser.print_help()


_HandlerFn = Callable[..., object]


def _build_dispatch_table() -> dict[str, _HandlerFn]:
    """Build the full command -> handler dispatch table."""
    handlers: dict[str, _HandlerFn] = {
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
        "compare":  cmd_compare,
        "cluster":  cmd_cluster,
        "entropy":  cmd_entropy,
        "hcmon":    cmd_hcmon,
        "hibp":     cmd_hibp,
        "intelx":   cmd_intelx,
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
        "rule-mine":     cmd_rule_mine,
        "finetune-data": cmd_finetune_data,
        "nflow":         cmd_nflow,
        "combo":         cmd_combo,
        "corp-conv":     cmd_corp_conv,
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
    handlers["locale"]        = cmd_locale
    handlers["pbmp"]          = cmd_pbmp
    handlers["evolve"]        = cmd_evolve
    handlers["graph-expand"]  = cmd_graph_expand
    handlers["temporal-model"] = cmd_temporal_model
    handlers["domain-pcfg"]   = cmd_domain_pcfg
    handlers["plugin"]        = cmd_plugin
    handlers["vae-interp"]    = cmd_vae_interp
    handlers["test"]          = cmd_test

    return handlers


# ── v2.0 command handlers ─────────────────────────────────────────────────────


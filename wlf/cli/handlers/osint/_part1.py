"""Command handlers: osint."""
from __future__ import annotations

import argparse
from collections.abc import Generator
from typing import Any

from wlf.cli.context import (
    _GLOBAL_CTX,
    is_shutdown,
)
from wlf.cli.utils import (
    _err,
    _info,
    _ok,
    _profile_preview_and_confirm,
    _warn,
    _write_output,
)


def cmd_profile(args: argparse.Namespace) -> None:
    """Handler for personal profiling mode."""
    # ── Resolve locale: CLI --lang > YAML locale > session default ────────────
    from wlf_modules.i18n import set_session_locale as _set_locale
    from wlf_modules.profiler import interactive_profile, resolve_profile_output
    _cli_lang = getattr(args, "lang", None)
    if _cli_lang:
        _set_locale(_cli_lang)

    # ── Load from YAML file ──────────────────────────────────────────────────
    if getattr(args, "profile_file", None):
        from wlf_modules.profiler import load_profile_yaml
        try:
            profile = load_profile_yaml(args.profile_file)
            if not _cli_lang and profile.get("locale"):
                _set_locale(profile["locale"])
            _info(f"Profile loaded from: {args.profile_file}")
        except (FileNotFoundError, ImportError) as exc:
            _err(str(exc))
            return
    elif hasattr(args, "name") and args.name:
        from wlf_modules.profiler import parse_date_input
        birth_parsed = parse_date_input(getattr(args, "birth", "") or "") or (0, 0, 0)
        profile = {
            "full_name": args.name,
            "short_name": "",
            "nicknames": [],
            "birth_day": birth_parsed[0],
            "birth_month": birth_parsed[1],
            "birth_year": birth_parsed[2],
            "national_id": "",
            "phones": [],
            "location_city": "",
            "location_state": "",
            "location_country": "",
            "children": [],
            "pets": [],
            "social_handles": [],
            "keywords": [],
            "special_dates": [],
            "leet_mode": getattr(args, "leet", None) or "basic",
            "with_spaces": False,
            "min_len": 6,
            "max_len": 32,
            "include_specials": False,
        }
        if getattr(args, "nick", ""):
            profile["nicknames"] = [args.nick]
    else:
        profile = interactive_profile(
            preset_leet=getattr(args, "leet", None),
            preset_output=getattr(args, "output", None),
        )

    # ── Inject year-range / suffix-range from CLI ────────────────────────────
    if getattr(args, "year_start", None) and getattr(args, "year_end", None):
        profile["year_start"] = args.year_start
        profile["year_end"] = args.year_end
    if getattr(args, "suffix_range", None):
        try:
            parts = args.suffix_range.split("-")
            profile["suffix_range_start"] = int(parts[0])
            profile["suffix_range_end"] = int(parts[1])
            profile["suffix_range_zero_pad"] = len(parts[0]) if parts[0].startswith("0") else 0
        except (ValueError, IndexError):
            _warn(f"Invalid --suffix-range format '{args.suffix_range}', expected START-END (e.g. 00-99)")

    # ── Inject CUPP/elpscrk/BEWGor fields from CLI ──────────────────────────
    if getattr(args, "surname", None):
        profile["surname"] = args.surname
    if getattr(args, "old_passwords", None):
        profile["old_passwords"] = args.old_passwords
    if getattr(args, "depth", None):
        profile["depth"] = args.depth
    if getattr(args, "parents", None):
        profile["parents"] = args.parents
    if getattr(args, "siblings", None):
        profile["siblings"] = args.siblings

    # ── Inject engine/pipeline flags from CLI ───────────────────────────────
    _cli_engines = getattr(args, "engines", None)
    if _cli_engines:
        profile["engines"] = _cli_engines
    elif profile.get("_engine_ids"):
        # Promote interactive wizard selection to pipeline-compatible format
        profile["engines"] = ",".join(str(i) for i in profile["_engine_ids"])

    _max_cand = getattr(args, "max_candidates", 0)
    if _max_cand:
        profile["max_candidates"] = _max_cand
    _timeout = getattr(args, "timeout_secs", 0.0)
    if _timeout:
        profile["timeout_secs"] = _timeout

    leet_mode = getattr(args, "leet", None) or profile.get("leet_mode", "basic")
    profile["leet_mode"] = leet_mode

    output = resolve_profile_output(getattr(args, "output", None), profile)

    # Validate engine selection before expensive preview/pipeline
    if profile.get("engines") or profile.get("_engine_ids"):
        try:
            from wlf_modules.generation_engines import resolve_engines
            raw_eng = profile.get("engines") or ",".join(
                str(i) for i in profile.get("_engine_ids", [])
            )
            resolve_engines(str(raw_eng))
        except MemoryError as exc:
            _err(str(exc))
            return
        except ValueError as exc:
            _err(f"Invalid engine selection: {exc}")
            return

    # ── Pipeline execution ───────────────────────────────────────────────────
    try:
        from wlf_modules.pipeline_engine import (
            PipelineConfig,
            ProfilePipeline,
            run_profile_pipeline,
        )
        _use_pipeline = True
    except ImportError:
        _use_pipeline = False

    if _use_pipeline:
        if output:
            profile["output_path"] = output
            # Quick preview using legacy generator before the heavy pipeline runs
            _preview_ok = True
            if profile.get("interactive_mode"):
                from wlf_modules.profiler import generate_from_profile
                preview = _profile_preview_and_confirm(profile, leet_mode, output)
                if preview is None:
                    return
            _info(f"Running generation pipeline [leet={leet_mode}, engines={profile.get('engines', 'default')}]...")
            try:
                result = run_profile_pipeline(profile, output_path=output)
                count = result.get("lines_written", 0)
                elapsed = result.get("elapsed_secs", 0)
                archive = result.get("archive", {})
                feedback = result.get("feedback", {})
                if count:
                    dest = archive.get("output_path") or output
                    _ok(f"Generated: {count:,} entries → {dest} [{elapsed}s]")
                    if feedback:
                        hit_rate = feedback.get("hit_rate", 0)
                        hits = feedback.get("hits", 0)
                        total = feedback.get("total", 0)
                        _info(f"Feedback: {hits}/{total} known targets found ({hit_rate:.1%} hit rate)")
                else:
                    _warn("No entries written.")
            except Exception as exc:
                _err(f"Pipeline error: {exc}")
        else:
            _info(f"Running generation pipeline [leet={leet_mode}] → stdout...")
            try:
                config = PipelineConfig.from_profile(profile)
                pipeline = ProfilePipeline(profile, config)
                count = _write_output(pipeline.run(), None)
                _ok(f"Generated: {count:,} entries (stdout - use -o or interactive output prompt to save)")
            except Exception as exc:
                _err(f"Pipeline error: {exc}")
    else:
        # Fallback to legacy generator when pipeline_engine is unavailable
        from wlf_modules.profiler import generate_from_profile
        if output:
            preview = _profile_preview_and_confirm(profile, leet_mode, output)
            if preview is None:
                return
            est_count, avg_len = preview
            _info(f"Generating wordlist from profile [leet={leet_mode}]...")
            gen = generate_from_profile(profile, leet_mode=leet_mode)
            count = _write_output(
                gen, output,
                estimate=est_count,
                min_len=int(profile.get("min_len", 0) or 0),
                max_len=int(profile.get("max_len", 0) or 0),
                avg_entry_len=max(1, int(avg_len)),
            )
            if count:
                _ok(f"Generated: {count:,} entries → {output}")
            else:
                _warn("No entries written.")
        else:
            _info(f"Generating wordlist from profile [leet={leet_mode}]...")
            gen = generate_from_profile(profile, leet_mode=leet_mode)
            count = _write_output(gen, None)
            _ok(f"Generated: {count:,} entries (stdout - use -o or interactive output prompt to save)")



def cmd_corp(args: argparse.Namespace) -> None:
    """Handler for corporate profiling mode."""
    from wlf_modules.corp_profiler import (
        generate_from_corp_profile,
        interactive_corp_profile,
    )

    profile = interactive_corp_profile()
    leet_mode = getattr(args, "leet", "basic") or profile.get("leet_mode", "basic")
    _info(f"Generating corporate wordlist [leet={leet_mode}]...")
    gen = generate_from_corp_profile(profile, leet_mode=leet_mode)
    count = _write_output(gen, args.output)
    _ok(f"Generated: {count:,} entries")



def cmd_corp_users(args: argparse.Namespace) -> None:
    """Handler for corporate domain user/password generation."""
    from wlf_modules.domain_users import (
        ALL_DOMAIN_SEPARATORS,
        DOMAIN_SEPARATORS,
        collect_names_from_file,
        collect_names_online,
        interactive_domain_users_wizard,
        run_domain_users,
    )

    params: dict[str, Any] = {}

    # ── Interactive mode (no --domain provided) ────────────────────────────
    if not getattr(args, "domain", None):
        params = interactive_domain_users_wizard()
    else:
        domain = args.domain
        company_name = getattr(args, "company", None) or domain.split(".")[0]
        names: list[str] = []

        # Collect names from file
        if getattr(args, "file", None):
            _info(f"Loading names from: {args.file}")
            try:
                names = collect_names_from_file(args.file)
                _ok(f"Loaded {len(names)} name(s) from file")
            except FileNotFoundError as exc:
                _err(str(exc))
                return

        # Collect names online (Google dorks + optional LinkedIn API)
        if getattr(args, "search", None):
            _info(f"Searching online for employees of '{args.search}'...")
            online = collect_names_online(
                args.search,
                domain=domain,
                max_results=getattr(args, "max_results", 50),
                use_linkedin_api=not getattr(args, "no_api", False),
            )
            _ok(f"Found {len(online)} name(s) online")
            names.extend(online)

        # Manual name list (args.names is a single string)
        if getattr(args, "names", None):
            raw_names = args.names if isinstance(args.names, str) else ",".join(args.names)
            names.extend([n.strip() for n in raw_names.split(",") if n.strip()])

        # Parse separators - default is "." only; user can supply custom list or "all"
        sep_raw = getattr(args, "separators", None)
        if sep_raw:
            if sep_raw.strip().lower() == "all":
                separators = ALL_DOMAIN_SEPARATORS
            elif sep_raw.strip().lower() == "none":
                separators = [""]
            else:
                separators = []
                for token in sep_raw.split(","):
                    t = token.strip()
                    if t.lower() in ("none", "empty", "''", '""'):
                        if "" not in separators:
                            separators.append("")
                    elif t:
                        if t not in separators:
                            separators.append(t)
                if not separators:
                    separators = DOMAIN_SEPARATORS
        else:
            separators = DOMAIN_SEPARATORS  # default: ["."]

        subdomains = []
        if getattr(args, "subdomain", None):
            subdomains = [s.strip() for s in args.subdomain.split(",") if s.strip()]

        year_start = int(getattr(args, "year_start", None) or 2020)
        year_end = int(getattr(args, "year_end", None) or 2026)

        params = {
            "domain": domain,
            "company_name": company_name,
            "names": names,
            "separators": separators,
            "subdomains": subdomains,
            "gen_users": not getattr(args, "no_users", False),
            "gen_passwords": getattr(args, "passwords", False),
            "gen_combo": getattr(args, "combo", False),
            "year_start": year_start,
            "year_end": year_end,
            "with_at_domain": not getattr(args, "no_at", False),
        }

    if not params.get("names") and not params.get("subdomains"):
        _warn("No names or subdomains provided. Use --file, --search, --names, or --subdomain.")
        return

    _info(
        f"Generating for domain: {params.get('domain')} | "
        f"names: {len(params.get('names', []))} | "
        f"subdomains: {len(params.get('subdomains', []))}"
    )

    # ── Threads ────────────────────────────────────────────────────────────────
    threads = _GLOBAL_CTX.get("threads", 5)

    # ── ML ranking ─────────────────────────────────────────────────────────────
    # Respects both per-command --no-ml and global --no-ml
    cmd_use_ml = getattr(args, "use_ml", True)
    global_ml  = _GLOBAL_CTX.get("use_ml", True)
    use_ml     = cmd_use_ml and global_ml

    ml_model = None
    if use_ml:
        try:
            from wlf_modules.ml_patterns import DEFAULT_MODEL_FILE, get_model
            if DEFAULT_MODEL_FILE.exists():
                ml_model = get_model()
                if ml_model.is_trained():
                    _info(f"ML model loaded ({ml_model._total_uid_samples:,} samples) - ranking by probability")
                else:
                    ml_model = None
        except Exception:
            ml_model = None

    # ── Parallel generation across multiple names ──────────────────────────────
    names_list = params.get("names", [])
    if threads > 1 and len(names_list) > 1:
        from wlf_modules.thread_pool import parallel_generate

        _info(f"Parallel generation: {threads} threads × {len(names_list)} names")

        single_name_params = []
        for name in names_list:
            p = dict(params)
            p["names"] = [name]
            single_name_params.append(p)

        def _gen_for_params(p: dict[str, Any]) -> Generator[Any, None, None]:
            return run_domain_users(p)

        gen = parallel_generate(_gen_for_params, single_name_params, threads=threads)
    else:
        gen = run_domain_users(params)

    if ml_model:
        domain = params.get("domain", "")
        candidates = list(gen)
        ranked     = ml_model.rank_and_yield(candidates, domain)
        count      = _write_output(ranked, args.output)
    else:
        count = _write_output(gen, args.output)

    _ok(f"Generated: {count:,} entries")




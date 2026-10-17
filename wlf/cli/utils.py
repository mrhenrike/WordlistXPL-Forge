"""Shared CLI utility functions."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Generator, Optional

from wlf.cli.context import (
    Fore, Style, _TQDM, _tqdm, _GLOBAL_CTX, is_shutdown, logger,
)

def _info(msg: str) -> None:
    print(f"{Fore.CYAN}[*]{Style.RESET_ALL} {msg}")


def _ok(msg: str) -> None:
    print(f"{Fore.GREEN}[+]{Style.RESET_ALL} {msg}")


def _warn(msg: str) -> None:
    print(f"{Fore.YELLOW}[!]{Style.RESET_ALL} {msg}")


def _err(msg: str) -> None:
    print(f"{Fore.RED}[-]{Style.RESET_ALL} {msg}", file=sys.stderr)

def _write_output(
    generator: Generator[str, None, None],
    output: Optional[str],
    estimate: Optional[int] = None,
    min_len: int = 0,
    max_len: int = 9999,
    append: bool = False,
    stream: bool = False,
    avg_entry_len: int = 14,
) -> int:
    """
    Write generator output to file or stdout with optional progress bar.

    Respects global --limit / --timeout / ResourceGovernor (RAM/chunk),
    and graceful Ctrl+C shutdown.
    """
    from wlf_modules.resource_governor import (
        STOP_OK,
        STOP_LIMIT,
        STOP_TIMEOUT,
        STOP_RAM,
        STOP_SHUTDOWN,
        governor_from_ctx,
    )

    count = 0
    stream = stream or bool(_GLOBAL_CTX.get("stream"))
    gov = governor_from_ctx(_GLOBAL_CTX)

    g_min = _GLOBAL_CTX.get("min_len", 0) or 0
    g_max = _GLOBAL_CTX.get("max_len", 0) or 0
    if g_min > 0:
        min_len = max(min_len, g_min)
    if g_max > 0:
        max_len = min(max_len, g_max) if max_len > 0 else g_max

    base_output = output
    current_output = output
    f = None
    if current_output:
        out_path = Path(current_output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if not _check_disk_space(current_output, estimate=estimate, avg_entry_len=avg_entry_len):
            _warn("Cancelled by user - no file written.")
            return 0
        mode = "a" if append else "w"
        f = out_path.open(mode, encoding="utf-8")
        _info(f"Writing to: {current_output}" + (" (append)" if append else ""))

    def _open_chunk() -> None:
        nonlocal f, current_output
        if f:
            f.close()
        current_output = gov.next_chunk_path(base_output or "out.lst")
        Path(current_output).parent.mkdir(parents=True, exist_ok=True)
        f = Path(current_output).open("w", encoding="utf-8")
        _info(f"Chunk rotate → {current_output}")

    try:
        if _TQDM and estimate and estimate > 0:
            pbar = _tqdm(total=estimate, unit="words", ncols=80)
        else:
            pbar = None

        for word in generator:
            reason = gov.check(shutdown_flag=_SHUTDOWN_REQUESTED)
            if reason != STOP_OK:
                if reason == STOP_SHUTDOWN:
                    _warn(f"Graceful shutdown - wrote {count:,} entries before stopping.")
                elif reason == STOP_LIMIT:
                    _warn(f"Reached --limit {gov.cfg.max_candidates:,}. Stopping.")
                elif reason == STOP_TIMEOUT:
                    _warn(f"Reached --timeout {gov.cfg.timeout_secs}s. Stopping at {count:,} entries.")
                elif reason == STOP_RAM:
                    _warn(
                        f"RAM guard tripped (available≈{gov.state.last_ram_mb}MB). "
                        f"Stopped at {count:,} entries to protect the host."
                    )
                break

            if not word:
                continue
            if min_len and len(word) < min_len:
                continue
            if max_len and len(word) > max_len:
                continue

            if base_output and gov.need_chunk_rotate() and count > 0:
                _open_chunk()

            line = word + "\n"
            nbytes = len(line.encode("utf-8"))
            if f:
                f.write(line)
                if stream:
                    f.flush()
            else:
                sys.stdout.write(line)
                if stream:
                    sys.stdout.flush()
            count += 1
            gov.note_emit(1, nbytes)
            if pbar:
                pbar.update(1)

        if pbar:
            pbar.close()

    finally:
        if f:
            f.close()

    return count


def _effective_len_bounds(min_len: int = 0, max_len: int = 9999) -> tuple[int, int]:
    """Merge profile/command bounds with global --min-len / --max-len."""
    g_min = _GLOBAL_CTX.get("min_len", 0) or 0
    g_max = _GLOBAL_CTX.get("max_len", 0) or 0
    if g_min > 0:
        min_len = max(min_len, g_min)
    if g_max > 0:
        max_len = min(max_len, g_max) if max_len > 0 else g_max
    return min_len, max_len

def _count_generator_entries(
    generator: Generator[str, None, None],
    min_len: int = 0,
    max_len: int = 9999,
) -> tuple[int, int, float]:
    """
    Count filtered generator output without writing.

    Returns:
        (entry_count, total_bytes_including_newlines, avg_line_length)
    """
    min_len, max_len = _effective_len_bounds(min_len, max_len)
    count = 0
    total_bytes = 0
    for word in generator:
        if not word:
            continue
        if min_len and len(word) < min_len:
            continue
        if max_len and len(word) > max_len:
            continue
        count += 1
        total_bytes += len(word.encode("utf-8")) + 1
    avg = total_bytes / count if count else 0.0
    return count, total_bytes, avg


def _profile_preview_and_confirm(
    profile: dict,
    leet_mode: str,
    output_path: str,
) -> Optional[tuple[int, float]]:
    """
    Count profile entries, show size summary, optionally ask to proceed.

    Returns:
        (count, avg_line_bytes) if user proceeds, None if cancelled.
    """
    from wlf_modules.profiler import generate_from_profile

    min_len = int(profile.get("min_len", 6) or 0)
    max_len = int(profile.get("max_len", 32) or 0) or 9999

    _info("Estimating wordlist - counting entries (this may take a moment)...")
    gen = generate_from_profile(profile, leet_mode=leet_mode)
    count, total_bytes, avg_len = _count_generator_entries(gen, min_len, max_len)

    print()
    print("  ┌─ Wordlist preview ─────────────────────────")
    print(f"  │  Entries (lines) : {count:,}")
    print(f"  │  Est. file size  : {_format_bytes(total_bytes)}")
    print(f"  │  Avg line length : {avg_len:.1f} chars")
    print(f"  │  Output file     : {output_path}")
    if profile.get("location_country") and not profile.get("include_country_variations", True):
        print("  │  Country mode    : minimal (ISO + name only)")
    elif profile.get("location_country"):
        print("  │  Country mode    : full variations (ISO, names, DDI, leet, combos)")
    print("  └────────────────────────────────────────────")
    print()

    ask = profile.get("interactive_mode", False)
    if ask:
        try:
            resp = input("  Generate and save this wordlist? [Y/n]: ").strip().lower()
            if resp in ("n", "no"):
                _warn("Cancelled by user - no file written.")
                return None
        except (KeyboardInterrupt, EOFError):
            _warn("Cancelled - no file written.")
            return None
    elif count == 0:
        _warn("No entries matched the current filters - nothing to write.")
        return None

    return count, avg_len


def _format_bytes(n: int) -> str:
    """Format byte count as human-readable string (B → KB → MB → GB → TB)."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n = int(n / 1024)
    return f"{n:.1f} PB"


def _check_disk_space(
    output: str,
    estimate: Optional[int] = None,
    avg_entry_len: int = 14,
) -> bool:
    """
    Check available disk space before writing an output file.

    Warns and requests confirmation when:
    - Estimated file size >= 50 MB, OR
    - Estimated file size > 60 %% of free space, OR
    - Free disk space < 300 MB regardless of estimate.

    Args:
        output: Destination file path.
        estimate: Expected number of entries (None = unknown).
        avg_entry_len: Average bytes per entry (including newline) for size estimation.

    Returns:
        True to proceed, False to cancel.
    """
    import shutil

    try:
        target_dir = Path(output).resolve().parent
        usage = shutil.disk_usage(str(target_dir))
        free_bytes = usage.free
    except Exception:
        return True  # can't check → proceed silently

    warn_parts: list[str] = []
    needs_confirm = False

    est_bytes: Optional[int] = None
    if estimate is not None and estimate > 0:
        est_bytes = estimate * avg_entry_len

    if est_bytes is not None:
        if est_bytes >= 50 * 1024 * 1024:          # >= 50 MB
            warn_parts.append(f"Estimated file size : {_format_bytes(est_bytes)}")
            needs_confirm = True
        if est_bytes > free_bytes * 0.6:            # > 60%% of free space
            warn_parts.append(
                f"File may use {est_bytes / free_bytes * 100:.0f}%% of available disk space"
            )
            needs_confirm = True

    if free_bytes < 300 * 1024 * 1024:             # < 300 MB free (always warn)
        warn_parts.insert(0, "Low disk space!")
        needs_confirm = True

    warn_parts.append(
        f"Free disk space     : {_format_bytes(free_bytes)}  "
        f"[{Path(output).resolve().parent}]"
    )

    if not needs_confirm:
        if est_bytes is not None:
            _info(f"Output size estimate: {_format_bytes(est_bytes)} | "
                  f"Free: {_format_bytes(free_bytes)}")
        return True

    print()
    for line in warn_parts:
        _warn(line)
    print()

    try:
        resp = input("  Continue writing to file? [y/N]: ").strip().lower()
        return resp in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


def _confirm_large(estimate: int, threshold: int = 10_000_000) -> bool:
    """
    Prompt user for confirmation before generating very large lists.

    Args:
        estimate: Estimated number of entries to generate.
        threshold: Threshold above which to ask for confirmation.

    Returns:
        True if user confirms.
    """
    if estimate <= threshold:
        return True
    _warn(f"Estimated: {estimate:,} entries. This may take a long time.")
    try:
        resp = input("  Continue? [y/N]: ").strip().lower()
        return resp in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


# ── Command handlers ─────────────────────────────────────────────────────────


def _resolve_path(p: str):
    """Resolve a path relative to wlf.py location or cwd."""
    from pathlib import Path
    pp = Path(p)
    if pp.exists():
        return pp
    # Try relative to wlf.py location
    wfh_dir = Path(__file__).parent
    alt = wfh_dir / p
    if alt.exists():
        return alt
    return pp  # return as-is (may not exist)



def _load_profile_file(path: str) -> dict:
    """Load a profile from JSON or YAML."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(text) or {}
        except ImportError:
            from wlf_modules.profiler import load_profile_yaml
            data = load_profile_yaml(path)
    else:
        import json as _json
        data = _json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Profile must be a mapping: {path}")
    return data



"""Global execution context, constants, and terminal output setup."""
from __future__ import annotations

import logging
import signal
import sys
from pathlib import Path

# ── Colorama ─────────────────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    _COLOR = True
except ImportError:
    _COLOR = False
    class Fore:  # type: ignore[no-redef]
        CYAN = GREEN = YELLOW = RED = MAGENTA = WHITE = RESET = ""
    class Style:  # type: ignore[no-redef]
        BRIGHT = RESET_ALL = ""

# ── tqdm ─────────────────────────────────────────────────────────────────────
try:
    from tqdm import tqdm as _tqdm
    _TQDM = True
except ImportError:
    _TQDM = False
    _tqdm = None  # type: ignore[assignment]

# ── Path setup ───────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_HERE))

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("wlf")

VERSION = "2.0.0"

# ── Graceful shutdown ────────────────────────────────────────────────────────
_SHUTDOWN_REQUESTED = False


def _signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global _SHUTDOWN_REQUESTED
    _SHUTDOWN_REQUESTED = True
    print(f"\n{Fore.YELLOW}[!]{Style.RESET_ALL} Shutdown requested - finishing current batch...")


signal.signal(signal.SIGINT, _signal_handler)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, _signal_handler)


def is_shutdown() -> bool:
    """Check if a graceful shutdown has been requested."""
    return _SHUTDOWN_REQUESTED


# ── Global execution context ─────────────────────────────────────────────────
_GLOBAL_CTX: dict = {
    "threads":      5,      # thread count (1-300)
    "compute_mode": "auto", # cpu | gpu | cuda | rocm | mps | auto | hybrid
    "use_ml":       True,   # ML enabled globally
    "limit":        0,      # global line limit (0=unlimited)
    "timeout":      0,      # global timeout in seconds (0=unlimited)
    "start_time":   0.0,    # epoch when execution started
    "min_len":      0,      # global minimum entry length (0=no filter)
    "max_len":      0,      # global maximum entry length (0=no filter)
    "ram_budget_pct": 50.0,
    "min_available_ram_mb": 512,
    "vram_budget_mb": 4096,
    "chunk_lines": 0,
    "chunk_bytes": 0,
    "gov_poll_every": 10_000,
    "enforce_safe_default": False,
    "safe_default_max": 5_000_000,
    "stream": False,
}


_BANNER_ART = (
    " __          _______ _    _         \n"
    r" \ \        / /  ____| |  | |        " + "\n"
    r"  \ \  /\  / /| |__  | |__| |       " + "\n"
    r"   \ \/  \/ / |  __| |  __  |       " + "\n"
    r"    \  /\  /  | |    | |  | |       " + "\n"
    r"     \/  \/   |_|    |_|  |_|       " + "\n"
)
BANNER = (
    f"\n{Fore.CYAN}{Style.BRIGHT}\n"
    + _BANNER_ART
    + f"\n  WordlistXPL-Forge  v{VERSION}\n"
    + "  Author: André Henrique (@mrhenrike)\n"
    + "  Unified wordlist generation for pentest & red team\n"
    + f"{Style.RESET_ALL}"
)

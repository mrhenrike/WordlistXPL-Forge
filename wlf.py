#!/usr/bin/env python3
"""
wlf.py - WordlistXPL-Forge v2.0.0

Backward-compatible entrypoint.  The actual code lives in the ``wlf``
package (wlf/cli/).  This file exists so that ``python wlf.py`` still
works exactly as before.

Usage:
  python wlf.py                  # interactive menu
  python wlf.py charset 6 8 abc  # CLI subcommand
"""
VERSION = "2.0.0"

from wlf.cli.main import main

if __name__ == "__main__":
    main()

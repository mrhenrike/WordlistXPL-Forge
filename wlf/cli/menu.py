"""Interactive menu for wlf — categorized with submenus."""
from __future__ import annotations

import argparse
import sys
from typing import Any, Optional

from wlf.cli.context import Fore, Style
from wlf.cli.utils import _info, _warn


_CATEGORIES: list[dict[str, Any]] = [
    {
        "key": "G",
        "title": "Generation",
        "commands": [
            ("charset", "Generate by charset and length"),
            ("pattern", "Generate by template with variables"),
            ("phrase", "Phrase-initials password generator"),
            ("mutate", "Mutate an existing password"),
            ("num2text", "Convert digits to text words"),
            ("leet", "Leet speak variants"),
            ("leet-perm", "Full leet permutation generator"),
            ("combiner", "Combine multiple wordlists (cartesian)"),
            ("pcfg", "PCFG-based password generation"),
            ("markov", "Markov chain password generation"),
            ("kwalk", "Keyboard walk pattern generation"),
            ("phonetic", "Phonetic/Soundex password variants"),
            ("prince", "PRINCE attack wordlist generation"),
            ("passphrase", "Diceware-style passphrase generator"),
            ("nflow", "Normalizing flow password generation"),
            ("combo", "Credential combo (user:pass) generation"),
            ("corp-conv", "Corporate convention patterns"),
            ("evolve", "Evolutionary password generation"),
            ("graph-expand", "Graph-based token expansion"),
            ("temporal-model", "Temporal pattern generation"),
            ("domain-pcfg", "Domain-specific PCFG generation"),
            ("vae-interp", "VAE latent interpolation generation"),
            ("pbmp", "Probability-based mask permutation"),
            ("br-deep", "Brazilian deep cultural patterns"),
            ("br-names", "Brazilian name-based generation"),
            ("iwlgen", "Intelligent wordlist generation"),
            ("neural", "Neural network password generation"),
            ("finetune-data", "LLM fine-tune dataset generation"),
        ],
    },
    {
        "key": "A",
        "title": "Analysis & Detection",
        "commands": [
            ("analyze", "Statistical analysis of wordlist"),
            ("compare", "Compare two wordlists (overlap metrics)"),
            ("cluster", "Password clustering/classification"),
            ("entropy", "Entropy distribution visualization"),
            ("strength", "Password strength estimation"),
            ("score", "Score passwords against models"),
            ("evaluate", "Evaluate wordlist quality"),
            ("anomaly-score", "Anomaly scoring for passwords"),
            ("pattern-rank", "Pattern frequency ranking"),
            ("maya-rank", "MAYA probabilistic ranking"),
            ("password-dna", "Password DNA structural analysis"),
            ("dna-extract", "Extract DNA patterns from wordlist"),
            ("cover", "Coverage analysis against target set"),
            ("benchmark", "Benchmark engine performance"),
            ("hash-id", "Identify hash type"),
            ("hash-gen", "Generate hashes from passwords"),
            ("hcmask", "Generate hashcat mask files"),
            ("maskgen", "Mask generation from wordlist"),
            ("explain", "Explain a wlf command or pipeline"),
        ],
    },
    {
        "key": "B",
        "title": "Breach & External Integration",
        "commands": [
            ("hibp", "HIBP breach check (k-Anonymity)"),
            ("intelx", "IntelX breach/leak search"),
            ("hcmon", "Hashcat / John the Ripper monitor"),
            ("default-creds", "Default credentials database"),
            ("isp-keygen", "ISP default WiFi key generator"),
        ],
    },
    {
        "key": "O",
        "title": "OSINT & Profiling",
        "commands": [
            ("profile", "Interactive personal target profiling"),
            ("corp", "Interactive corporate target profiling"),
            ("corp-users", "Corporate domain user/pass generation"),
            ("corp-prefixes", "Corporate prefix username generation"),
            ("phone", "Phone number wordlist generation"),
            ("scrape", "Web scraping wordlist extraction"),
            ("scrape-target", "Targeted web scraping"),
            ("ocr", "Extract text from image via OCR"),
            ("extract", "Extract wordlist from files"),
            ("dns", "DNS/subdomain fuzzing wordlist"),
            ("pharma", "Brazilian pharmacy/health patterns"),
            ("cupp", "Common User Passwords Profiler"),
            ("osint", "OSINT-based wordlist generation"),
            ("osint-perm", "OSINT permutation engine"),
        ],
    },
    {
        "key": "P",
        "title": "Operations & Processing",
        "commands": [
            ("merge", "Merge and deduplicate wordlists"),
            ("sanitize", "Clean wordlist (dedupe/sort/filter)"),
            ("dedup", "Deduplicate wordlist"),
            ("subtract", "Subtract one wordlist from another"),
            ("split", "Split wordlist into parts"),
            ("reverse", "Reverse line order"),
            ("affix", "Add prefix/suffix to wordlist"),
            ("mangle", "Apply hashcat-style mangling rules"),
            ("rules", "Apply rule file to wordlist"),
            ("rulegen", "Generate rules from wordlist"),
            ("rule-mine", "Mine hashcat rules from pairs"),
            ("xor", "XOR encryption / brute-force"),
            ("curate", "Curate and filter wordlist"),
            ("improve", "Improve wordlist quality"),
            ("replay", "Replay a recorded session"),
            ("emit", "Emit raw candidates to stdout"),
            ("keyspace", "Calculate keyspace size"),
        ],
    },
    {
        "key": "I",
        "title": "Infrastructure & ML",
        "commands": [
            ("train", "Train ML pattern model"),
            ("strategy", "Generate cracking strategy"),
            ("bandit", "Multi-armed bandit engine routing"),
            ("pipeline", "Run pipeline DSL script"),
            ("session", "Manage sessions"),
            ("serve", "Start API server"),
            ("plugin", "Manage plugins"),
            ("sysinfo", "Show hardware profile and compute"),
            ("test", "Run built-in tests"),
        ],
    },
]


def _print_main_menu() -> None:
    """Print categorized main menu."""
    print(f"\n{Fore.CYAN}=== MAIN MENU ==={Style.RESET_ALL}\n")
    for cat in _CATEGORIES:
        count = len(cat["commands"])
        print(
            f"  {Fore.GREEN}[{cat['key']}]{Style.RESET_ALL}  "
            f"{cat['title']:<35s} ({count} commands)"
        )
    print(f"\n  {Fore.GREEN}[Q]{Style.RESET_ALL}  Quit")
    print(
        f"\n  {Fore.YELLOW}Tip:{Style.RESET_ALL} Type a command name directly "
        f"(e.g. 'charset') to run it, or a category letter for submenu.\n"
    )


def _print_category_menu(cat: dict[str, Any]) -> None:
    """Print commands within a category."""
    print(f"\n{Fore.CYAN}=== {cat['title'].upper()} ==={Style.RESET_ALL}\n")
    for i, (cmd, desc) in enumerate(cat["commands"], 1):
        print(f"  {Fore.GREEN}[{i:2d}]{Style.RESET_ALL}  {cmd:<20s} {desc}")
    print(f"\n  {Fore.GREEN}[B]{Style.RESET_ALL}   Back to main menu")
    print()


def _find_command(name: str) -> Optional[str]:
    """Find a command by name across all categories."""
    name_lower = name.lower().strip()
    for cat in _CATEGORIES:
        cmds: list[tuple[str, str]] = cat["commands"]
        for cmd, _ in cmds:
            if cmd == name_lower:
                return cmd
    return None


def _run_command(cmd_name: str) -> None:
    """Import and run a command handler by name."""
    from wlf.cli.main import _build_dispatch_table
    dispatch = _build_dispatch_table()

    fn = dispatch.get(cmd_name)
    if fn is None:
        _warn(f"Command '{cmd_name}' not found in dispatch table.")
        return

    ns = argparse.Namespace(output=None, command=cmd_name)

    out_path = input("  Output file (Enter for stdout): ").strip() or None
    ns.output = out_path

    try:
        fn(ns)
    except (TypeError, AttributeError):
        _warn(
            f"Interactive mode for '{cmd_name}' needs CLI flags. "
            f"Run: python wlf.py {cmd_name} --help"
        )
    except KeyboardInterrupt:
        print("\n")
        _warn("Interrupted.")


def interactive_menu() -> None:
    """Display and process the categorized interactive menu."""
    _print_main_menu()
    choice = input(f"{Fore.CYAN}Select: {Style.RESET_ALL}").strip()

    if not choice:
        return

    if choice.upper() in ("Q", "0"):
        _info("Exiting wlf.")
        sys.exit(0)

    direct = _find_command(choice)
    if direct:
        _run_command(direct)
        return

    cat_match = None
    for cat in _CATEGORIES:
        if choice.upper() == cat["key"]:
            cat_match = cat
            break

    if not cat_match:
        _warn(f"Invalid option: {choice}")
        return

    while True:
        _print_category_menu(cat_match)
        sub = input(f"{Fore.CYAN}Select: {Style.RESET_ALL}").strip()

        if not sub or sub.upper() == "B":
            break

        if sub.isdigit():
            idx = int(sub) - 1
            if 0 <= idx < len(cat_match["commands"]):
                cmd_name = cat_match["commands"][idx][0]
                _run_command(cmd_name)
                break
            else:
                _warn("Invalid number.")
        else:
            direct2 = _find_command(sub)
            if direct2:
                _run_command(direct2)
                break
            _warn(f"Invalid option: {sub}")

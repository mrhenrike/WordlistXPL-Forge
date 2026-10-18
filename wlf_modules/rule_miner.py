"""rule_miner.py - Automatic hashcat rule derivation from plaintext pairs.

Given pairs of (base_word, plaintext), infers the hashcat rules that
transform the base into the plaintext.  This is the inverse of
rule_engine.py: observation -> rule instead of rule -> transformation.

Supports: case changes, append/prepend, insert, delete, replace, reverse,
duplicate, toggle, truncate.

Output format: one hashcat-compatible rule per line.

Author: André Henrique (@mrhenrike)
Version: 2.0.0
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


# ── Hashcat rule helpers ─────────────────────────────────────────────────────

def _pos_char(n: int) -> str:
    """Encode position as hashcat position character (0-9, A-Z)."""
    if 0 <= n <= 9:
        return str(n)
    if 10 <= n <= 35:
        return chr(ord("A") + n - 10)
    return str(n)


def _detect_case_rule(base: str, target: str) -> Optional[str]:
    """Detect if the transformation is a pure case change."""
    if base.lower() == target.lower() and base != target:
        if target == base.lower():
            return "l"
        if target == base.upper():
            return "u"
        if target == base.capitalize():
            return "c"
        if target == base.lower().capitalize():
            return "c"
        if target == base.swapcase():
            return "t" * len(base)
        if len(base) == len(target):
            toggles: list[str] = []
            for i, (b, t) in enumerate(zip(base, target)):
                if b != t and b.swapcase() == t:
                    toggles.append(f"T{_pos_char(i)}")
            if toggles and "".join(
                b.swapcase() if f"T{_pos_char(i)}" in toggles else b
                for i, b in enumerate(base)
            ) == target:
                return " ".join(toggles)
    return None


def _detect_append(base: str, target: str) -> Optional[str]:
    """Detect append operations (target = base + suffix)."""
    bl = base.lower()
    tl = target.lower()
    if tl.startswith(bl) and len(target) > len(base):
        suffix = target[len(base):]
        case_rule = _detect_case_rule(base, target[:len(base)])
        prefix_rules = case_rule + " " if case_rule else ""
        append_rules = " ".join(f"${c}" for c in suffix)
        return prefix_rules + append_rules
    if bl != tl and tl.startswith(bl):
        suffix = target[len(base):]
        append_rules = " ".join(f"${c}" for c in suffix)
        return "l " + append_rules
    return None


def _detect_prepend(base: str, target: str) -> Optional[str]:
    """Detect prepend operations (target = prefix + base)."""
    bl = base.lower()
    tl = target.lower()
    if tl.endswith(bl) and len(target) > len(base):
        prefix = target[:len(target) - len(base)]
        case_rule = _detect_case_rule(base, target[len(prefix):])
        suffix_rules = case_rule + " " if case_rule else ""
        prepend_rules = " ".join(f"^{c}" for c in reversed(prefix))
        return suffix_rules + prepend_rules
    return None


def _detect_replace(base: str, target: str) -> Optional[str]:
    """Detect character replacement rules."""
    if len(base) != len(target):
        return None
    replacements: list[str] = []
    for i, (b, t) in enumerate(zip(base, target)):
        if b != t:
            if b.lower() == t.lower():
                replacements.append(f"T{_pos_char(i)}")
            else:
                replacements.append(f"s{b}{t}")
    if replacements and len(replacements) <= 4:
        return " ".join(replacements)
    return None


def _detect_reverse(base: str, target: str) -> Optional[str]:
    """Detect if target is the reverse of base."""
    if base[::-1] == target:
        return "r"
    if base[::-1].lower() == target.lower():
        case_rule = _detect_case_rule(base[::-1], target) or ""
        return "r " + case_rule if case_rule else "r"
    return None


def _detect_duplicate(base: str, target: str) -> Optional[str]:
    """Detect if target is base doubled."""
    if target == base + base:
        return "d"
    if target == base + base[::-1]:
        return "d r"
    return None


def _detect_truncate(base: str, target: str) -> Optional[str]:
    """Detect truncation rules."""
    if base.startswith(target) and len(target) < len(base):
        n_cut = len(base) - len(target)
        return " ".join(["]"] * n_cut)
    if base.endswith(target) and len(target) < len(base):
        n_cut = len(base) - len(target)
        return " ".join(["["] * n_cut)
    return None


# ── Main mining function ─────────────────────────────────────────────────────

def mine_rule(base: str, plaintext: str) -> list[str]:
    """Infer hashcat rules that transform base into plaintext.

    Returns a list of candidate rules, most likely first.
    """
    if base == plaintext:
        return [":"]

    rules: list[str] = []

    case = _detect_case_rule(base, plaintext)
    if case:
        rules.append(case)

    rev = _detect_reverse(base, plaintext)
    if rev:
        rules.append(rev)

    dup = _detect_duplicate(base, plaintext)
    if dup:
        rules.append(dup)

    append = _detect_append(base, plaintext)
    if append:
        rules.append(append)

    prepend = _detect_prepend(base, plaintext)
    if prepend:
        rules.append(prepend)

    replace = _detect_replace(base, plaintext)
    if replace:
        rules.append(replace)

    trunc = _detect_truncate(base, plaintext)
    if trunc:
        rules.append(trunc)

    bl = base.lower()
    tl = plaintext.lower()

    if tl.startswith(bl):
        suffix = plaintext[len(base):]
        case_part = _detect_case_rule(base, plaintext[:len(base)]) or ""
        if case_part:
            rules.append(f"{case_part} " + " ".join(f"${c}" for c in suffix))
    elif tl.endswith(bl):
        prefix = plaintext[:len(plaintext) - len(base)]
        case_part = _detect_case_rule(base, plaintext[len(prefix):]) or ""
        prepend_part = " ".join(f"^{c}" for c in reversed(prefix))
        if case_part:
            rules.append(f"{case_part} {prepend_part}")

    return list(dict.fromkeys(rules))


def mine_rules_from_pairs(
    pairs: list[tuple[str, str]],
    min_confidence: int = 2,
) -> list[tuple[str, int]]:
    """Mine rules from multiple (base, plaintext) pairs.

    Returns rules sorted by frequency (most common first).
    """
    rule_counter: Counter[str] = Counter()
    for base, plaintext in pairs:
        for rule in mine_rule(base, plaintext):
            rule_counter[rule] += 1
    return [
        (rule, count)
        for rule, count in rule_counter.most_common()
        if count >= min_confidence
    ]


# ── File I/O ─────────────────────────────────────────────────────────────────

def mine_from_file(
    plaintext_file: str,
    dictionary_file: Optional[str] = None,
    max_rules: int = 200,
    min_confidence: int = 2,
) -> list[tuple[str, int]]:
    """Mine rules from a plaintext file.

    If dictionary_file is provided, each plaintext is compared against
    every dictionary word.  Otherwise, each plaintext is compared against
    common base transformations of itself (lowercase, no digits, etc).
    """
    import re

    plaintexts = [
        line.strip()
        for line in Path(plaintext_file).read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip()
    ]

    bases: list[str]
    if dictionary_file:
        bases = [
            line.strip()
            for line in Path(dictionary_file).read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip()
        ]
    else:
        bases = []

    pairs: list[tuple[str, str]] = []

    if bases:
        base_set = set(b.lower() for b in bases)
        for pw in plaintexts:
            pwl = pw.lower()
            for base in bases:
                bl = base.lower()
                if bl in pwl or pwl.startswith(bl) or pwl.endswith(bl):
                    pairs.append((base, pw))
                    break
    else:
        for pw in plaintexts:
            base = re.sub(r"[^a-zA-Z]", "", pw)
            if base and base != pw:
                pairs.append((base, pw))
            base_low = pw.lower()
            if base_low != pw:
                pairs.append((base_low, pw))

    return mine_rules_from_pairs(pairs, min_confidence=min_confidence)[:max_rules]


def write_rules(rules: list[tuple[str, int]], output: str) -> int:
    """Write rules to a hashcat .rule file."""
    lines: list[str] = []
    for rule, count in rules:
        lines.append(f"# count={count}")
        lines.append(rule)
    Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rules)


# ── CLI handler ──────────────────────────────────────────────────────────────

def handle_rule_mine(args: Any, ctx: dict[str, Any]) -> Optional[Generator[str, None, None]]:
    """CLI handler for rule mining."""
    wordlist = getattr(args, "wordlist", None)
    dictionary = getattr(args, "dictionary", None)
    output = getattr(args, "output", None)
    max_rules = getattr(args, "max_rules", 200)
    min_conf = getattr(args, "min_confidence", 2)

    if not wordlist:
        logger.warning("No wordlist provided. Use --wordlist.")
        return None

    rules = mine_from_file(
        wordlist,
        dictionary_file=dictionary,
        max_rules=max_rules,
        min_confidence=min_conf,
    )

    if output:
        count = write_rules(rules, output)
        return iter([f"Wrote {count} rules to {output}"])  # type: ignore[return-value]

    def _gen() -> Generator[str, None, None]:
        for rule, count in rules:
            yield f"{rule}  # x{count}"

    return _gen()

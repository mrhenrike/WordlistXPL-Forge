"""
hashcat_rules_db.py: Curated hashcat rule collection manager.

Manages rule sets from well-known sources (Hob0Rules, PACK, d3ad0ne,
OneRuleToRuleThemAll, etc.) with metadata, deduplication, optimization,
coverage analysis and format conversion between hashcat and John the Ripper.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
Version: 1.0.0
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from collections import Counter
from collections.abc import Generator, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

_COMMENT_RE = re.compile(r"^\s*#|^\s*$")
_NOOP_RULES = frozenset({":", ""})
_HASHCAT_POS_RANGE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass
class RuleSetMeta:
    """Metadata for a named rule collection."""

    name: str
    author: str
    description: str
    source_url: str = ""
    target: str = "general"
    format: str = "hashcat"
    tags: list[str] = field(default_factory=list)


BUILTIN_COLLECTIONS: dict[str, RuleSetMeta] = {
    "hob064": RuleSetMeta(
        name="Hob064",
        author="Praetorian",
        description="64 optimized rules from Praetorian Hob0Rules for fast attacks",
        source_url="https://github.com/praetorian-inc/Hob0Rules",
        target="general",
        tags=["fast", "optimized"],
    ),
    "d3ad0ne": RuleSetMeta(
        name="d3ad0ne",
        author="d3ad0ne",
        description="Classic comprehensive rule set, 34k+ rules",
        source_url="https://github.com/hashcat/hashcat/tree/master/rules",
        target="general",
        tags=["comprehensive", "legacy"],
    ),
    "onerule": RuleSetMeta(
        name="OneRuleToRuleThemAll",
        author="NotSoSecure",
        description="Curated best-of rules from multiple sources",
        source_url="https://github.com/NotSoSecure/password_cracking_rules",
        target="general",
        tags=["curated", "recommended"],
    ),
    "dive": RuleSetMeta(
        name="dive",
        author="hashcat",
        description="Hashcat built-in dive.rule, moderate depth",
        source_url="https://github.com/hashcat/hashcat/tree/master/rules",
        target="general",
        tags=["builtin", "moderate"],
    ),
    "toggles": RuleSetMeta(
        name="toggles",
        author="hashcat",
        description="Toggle case at every position, up to 15 chars",
        source_url="https://github.com/hashcat/hashcat/tree/master/rules",
        target="case-focused",
        tags=["toggle", "position"],
    ),
    "corporate": RuleSetMeta(
        name="corporate",
        author="XPL-Suite",
        description="Rules targeting corporate password policies (length 8+, mixed case, special, digit)",
        target="corporate",
        tags=["policy", "corporate"],
    ),
    "brazilian": RuleSetMeta(
        name="brazilian",
        author="XPL-Suite",
        description="Rules targeting common Brazilian password patterns",
        target="pt-BR",
        tags=["locale", "br"],
    ),
}


HOB064_RULES = [
    ":", "l", "u", "c", "C", "t", "r", "d", "f",
    "$1", "$!", "$.", "$2", "$3", "$0", "$@", "$#",
    "$1$2$3", "$!", "$@", "$#", "$1$2$3$4",
    "^1", "^!", "^.", "^2",
    "sa@", "se3", "si1", "so0", "ss$", "st7",
    "sa@se3si1so0ss$st7",
    "$1$2$3$!", "$!$@$#",
    "c$1", "c$!", "c$1$2$3", "c$2$0$2$4", "c$2$0$2$5",
    "l$1", "l$!", "u$1",
    "csa@", "cse3", "csi1", "cso0",
    "csa@se3si1so0ss$st7",
    "c$1sa@se3si1so0", "c$!sa@se3si1so0",
    "^1^2^3", "^!^@^#",
    "c^1", "c^!",
    "T0", "T1", "T2", "T3", "T4",
    "r$1", "rd", "rf",
    "D0", "D1", "DA",
    "i0!", "i0@", "i01",
    "o0!", "o0@",
]

CORPORATE_RULES = [
    "c$1", "c$!", "c$1$!", "c$2$0$2$4$!",
    "c$2$0$2$5$!", "c$2$0$2$6$!",
    "c$@$1", "c$#$1", "c$.$1",
    "csa@se3si1so0$1", "csa@se3si1so0$!",
    "c$1$2$3", "c$1$2$3$!",
    "c$!$@$#", "c$P$@$s$s$1",
    "u$1$!", "u$1$2$3",
    "t$1", "t$!",
    "c$2$0$2$4", "c$2$0$2$5", "c$2$0$2$6",
    "c$J$a$n", "c$F$e$b", "c$M$a$r",
    "c$A$p$r", "c$M$a$y", "c$J$u$n",
    "c$J$u$l", "c$A$u$g", "c$S$e$p",
    "c$O$c$t", "c$N$o$v", "c$D$e$c",
]

BRAZILIAN_RULES = [
    ":", "l", "c",
    "$1", "$1$2$3", "$1$2$3$4",
    "$@", "$!", "$#",
    "$2$0$2$4", "$2$0$2$5", "$2$0$2$6",
    "c$1", "c$!", "c$@",
    "c$2$0$2$4", "c$2$0$2$5", "c$2$0$2$6",
    "sa@", "se3", "si1", "so0",
    "sa@se3si1so0", "csa@se3si1so0",
    "c$1$2$3$!", "c$!$@",
    "$B$R", "$b$r",
    "d", "r",
]


@dataclass
class RuleSet:
    """A collection of hashcat rules with metadata."""

    meta: RuleSetMeta
    rules: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.rules)

    def deduplicate(self) -> int:
        """Remove duplicate rules in-place. Returns number removed."""
        before = len(self.rules)
        seen: set[str] = set()
        unique: list[str] = []
        for rule in self.rules:
            if rule not in seen:
                seen.add(rule)
                unique.append(rule)
        self.rules = unique
        removed = before - len(self.rules)
        if removed:
            logger.info("Removed %d duplicate rules from %s", removed, self.meta.name)
        return removed

    def remove_noops(self) -> int:
        """Remove no-op rules (empty string and ':' alone). Returns removed count."""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r not in _NOOP_RULES]
        return before - len(self.rules)

    def optimize(self) -> dict[str, int]:
        """Deduplicate and remove no-ops. Returns stats."""
        noops = self.remove_noops()
        dupes = self.deduplicate()
        return {"noops_removed": noops, "duplicates_removed": dupes, "final_count": self.count}

    def apply_to_word(self, word: str) -> Generator[str, None, None]:
        """Apply all rules to a single word, yielding candidates."""
        for rule in self.rules:
            try:
                result = _execute_rule(word, rule)
                if result is not None:
                    yield result
            except Exception:
                continue

    def apply_to_wordlist(self, words: Iterable[str]) -> Generator[str, None, None]:
        """Apply all rules to each word in a wordlist."""
        for word in words:
            word = word.rstrip("\n\r")
            if not word:
                continue
            yield from self.apply_to_word(word)

    def coverage_against(self, targets: set[str], base_words: Iterable[str]) -> dict[str, Any]:
        """Measure how many targets this ruleset can crack from base words."""
        hits: set[str] = set()
        total_candidates = 0
        for word in base_words:
            word = word.rstrip("\n\r")
            if not word:
                continue
            for candidate in self.apply_to_word(word):
                total_candidates += 1
                if candidate in targets:
                    hits.add(candidate)
        return {
            "total_targets": len(targets),
            "hits": len(hits),
            "coverage_pct": round(len(hits) / len(targets) * 100, 2) if targets else 0.0,
            "total_candidates": total_candidates,
            "efficiency": round(len(hits) / total_candidates * 100, 6) if total_candidates else 0.0,
        }

    def export_hashcat(self, path: Path) -> None:
        """Write rules in hashcat format."""
        path.write_text("\n".join(self.rules) + "\n", encoding="utf-8")

    def export_jtr(self, path: Path) -> None:
        """Write rules in John the Ripper format (basic conversion)."""
        lines = ["[List.Rules:Generated]"]
        for rule in self.rules:
            jtr = _hashcat_to_jtr(rule)
            if jtr is not None:
                lines.append(jtr)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_builtin(name: str) -> RuleSet:
    """Load a built-in rule collection by name."""
    name_lower = name.lower()
    if name_lower not in BUILTIN_COLLECTIONS:
        available = ", ".join(sorted(BUILTIN_COLLECTIONS.keys()))
        raise ValueError(f"Unknown built-in collection: {name}. Available: {available}")

    meta = BUILTIN_COLLECTIONS[name_lower]

    if name_lower == "hob064":
        rules = list(HOB064_RULES)
    elif name_lower == "corporate":
        rules = list(CORPORATE_RULES)
    elif name_lower == "brazilian":
        rules = list(BRAZILIAN_RULES)
    else:
        rules = []
        logger.warning(
            "Collection %s metadata is registered but rules are not bundled. "
            "Use load_from_file() with the downloaded .rule file.",
            name,
        )

    return RuleSet(meta=meta, rules=rules)


def load_from_file(path: Path, meta: RuleSetMeta | None = None) -> RuleSet:
    """Load rules from a hashcat .rule file."""
    if meta is None:
        meta = RuleSetMeta(
            name=path.stem,
            author="unknown",
            description=f"Loaded from {path.name}",
        )
    rules: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n\r")
            if _COMMENT_RE.match(line):
                continue
            rules.append(line)
    return RuleSet(meta=meta, rules=rules)


def merge_rulesets(*rulesets: RuleSet, name: str = "merged") -> RuleSet:
    """Merge multiple rule sets with deduplication."""
    meta = RuleSetMeta(
        name=name,
        author="merged",
        description=f"Merged from {len(rulesets)} rule sets",
        tags=["merged"],
    )
    merged = RuleSet(meta=meta)
    seen: set[str] = set()
    for rs in rulesets:
        for rule in rs.rules:
            if rule not in seen:
                seen.add(rule)
                merged.rules.append(rule)
    return merged


def _execute_rule(word: str, rule_str: str) -> str | None:
    """Execute a hashcat rule string on a word.

    Returns the transformed word, or None if a rejection rule fires.
    Supports the core hashcat rule functions.
    """
    if not rule_str or rule_str == ":":
        return word

    result = list(word)
    i = 0
    ops = rule_str

    while i < len(ops):
        op = ops[i]

        if op == " " or op == "\t":
            i += 1
            continue

        if op == "l":
            result = [c.lower() for c in result]
        elif op == "u":
            result = [c.upper() for c in result]
        elif op == "c":
            if result:
                result[0] = result[0].upper()
                result[1:] = [c.lower() for c in result[1:]]
        elif op == "C":
            if result:
                result[0] = result[0].lower()
                result[1:] = [c.upper() for c in result[1:]]
        elif op == "t":
            result = [c.swapcase() for c in result]
        elif op == "r":
            result.reverse()
        elif op == "d":
            result = result + result[:]
        elif op == "f":
            result = result + result[::-1]
        elif op == "{":
            if result:
                result.append(result.pop(0))
        elif op == "}":
            if result:
                result.insert(0, result.pop())
        elif op == "$":
            i += 1
            if i < len(ops):
                result.append(ops[i])
        elif op == "^":
            i += 1
            if i < len(ops):
                result.insert(0, ops[i])
        elif op == "s":
            i += 1
            if i + 1 < len(ops):
                old, new = ops[i], ops[i + 1]
                result = [new if c == old else c for c in result]
                i += 1
        elif op == "@":
            i += 1
            if i < len(ops):
                ch = ops[i]
                result = [c for c in result if c != ch]
        elif op == "T":
            i += 1
            if i < len(ops):
                pos = _decode_pos(ops[i])
                if pos is not None and 0 <= pos < len(result):
                    result[pos] = result[pos].swapcase()
        elif op == "D":
            i += 1
            if i < len(ops):
                pos = _decode_pos(ops[i])
                if pos is not None and 0 <= pos < len(result):
                    result.pop(pos)
        elif op == "i":
            i += 1
            if i + 1 < len(ops):
                pos = _decode_pos(ops[i])
                i += 1
                ch = ops[i]
                if pos is not None and 0 <= pos <= len(result):
                    result.insert(pos, ch)
        elif op == "o":
            i += 1
            if i + 1 < len(ops):
                pos = _decode_pos(ops[i])
                i += 1
                ch = ops[i]
                if pos is not None and 0 <= pos < len(result):
                    result[pos] = ch
        elif op == "<":
            i += 1
            if i < len(ops):
                n = _decode_pos(ops[i])
                if n is not None and len(result) >= n:
                    return None
        elif op == ">":
            i += 1
            if i < len(ops):
                n = _decode_pos(ops[i])
                if n is not None and len(result) <= n:
                    return None
        elif op == "x":
            i += 1
            if i + 1 < len(ops):
                start = _decode_pos(ops[i])
                i += 1
                length = _decode_pos(ops[i])
                if start is not None and length is not None:
                    result = result[start : start + length]
        elif op == "'":
            i += 1
            if i < len(ops):
                n = _decode_pos(ops[i])
                if n is not None:
                    result = result[:n]
        elif op == "q":
            new_result: list[str] = []
            for c in result:
                new_result.append(c)
                new_result.append(c)
            result = new_result
        elif op == "k":
            if len(result) >= 2:
                result[0], result[1] = result[1], result[0]
        elif op == "K":
            if len(result) >= 2:
                result[-2], result[-1] = result[-1], result[-2]
        elif op == "!":
            i += 1
            if i < len(ops):
                ch = ops[i]
                if ch not in result:
                    return None
        elif op == "/":
            i += 1
            if i < len(ops):
                ch = ops[i]
                if ch in result:
                    return None

        i += 1

    return "".join(result)


def _decode_pos(ch: str) -> int | None:
    """Decode hashcat position char to int."""
    idx = _HASHCAT_POS_RANGE.find(ch.upper() if ch.isalpha() else ch)
    return idx if idx >= 0 else None


def _hashcat_to_jtr(rule: str) -> str | None:
    """Basic hashcat-to-JtR rule conversion.

    Only converts the most common shared functions. Returns None
    for rules that have no direct JtR equivalent.
    """
    if not rule or rule == ":":
        return ":"

    jtr_parts: list[str] = []
    i = 0

    while i < len(rule):
        op = rule[i]
        if op in ("l", "u", "c", "C", "t", "r", "d", "f", "{", "}", "q", "k", "K"):
            jtr_parts.append(op)
        elif op == "$":
            i += 1
            if i < len(rule):
                jtr_parts.append(f"${rule[i]}")
        elif op == "^":
            i += 1
            if i < len(rule):
                jtr_parts.append(f"^{rule[i]}")
        elif op == "s":
            i += 1
            if i + 1 < len(rule):
                jtr_parts.append(f"s{rule[i]}{rule[i+1]}")
                i += 1
        elif op == "T":
            i += 1
            if i < len(rule):
                jtr_parts.append(f"T{rule[i]}")
        elif op == "D":
            i += 1
            if i < len(rule):
                jtr_parts.append(f"D{rule[i]}")
        elif op == "i":
            i += 1
            if i + 1 < len(rule):
                jtr_parts.append(f"i{rule[i]}{rule[i+1]}")
                i += 1
        elif op == "@":
            i += 1
            if i < len(rule):
                jtr_parts.append(f"@{rule[i]}")
        else:
            return None
        i += 1

    return "".join(jtr_parts) if jtr_parts else ":"

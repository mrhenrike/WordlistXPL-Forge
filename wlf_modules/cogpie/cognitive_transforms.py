"""
cognitive_transforms.py - Layer 2: Cognitive transformation rules.

Models the measurable cognitive biases humans exhibit when creating passwords:
  1. Anchoring bias: base word stays recognizable
  2. Serial position effect: modifications cluster at start/end
  3. Familiarity heuristic: common substitution patterns (leet, case toggle)
  4. Minimal effort principle: shortest mutation that satisfies policy

Transform categories:
  - Capitalization patterns (first, last, alternating, all-caps)
  - Numeric suffixes/prefixes (birth years, sequences, lucky numbers)
  - Special character insertion (boundary positions preferred)
  - Leetspeak substitution (partial, never full word replacement in practice)
  - Keyboard-adjacent mutations
  - Concatenation patterns (word+separator+word)

Each transform T maps a token set S to an expanded candidate set C:
    C = Union_{t in S} Union_{T_j in Transforms} T_j(t)

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

from collections.abc import Generator

_COMMON_SUFFIXES: list[str] = [
    "1", "2", "3", "12", "13", "21", "23", "123", "1234", "12345",
    "!", "@", "#", "!!", "!@", "@#", "!@#", "!1", "@1",
    "01", "07", "10", "11", "00", "99", "69", "77", "88",
    "*", ".", "_", "$",
    "abc", "321", "007", "666", "777", "000",
]

_COMMON_PREFIXES: list[str] = [
    "!", "@", "#", "1", "123", ".", "_", "$", "a", "x",
]

_YEAR_RANGE = list(range(1950, 2028))

_SEPARATORS: list[str] = ["", ".", "_", "-", "@", "#", "!", "+", "*"]

_LEET_PARTIAL: dict[str, str] = {
    "a": "4", "e": "3", "i": "1", "o": "0",
    "s": "5", "t": "7", "b": "8", "g": "9", "l": "1", "z": "2",
}

_KEYBOARD_WALKS: list[str] = [
    "qwerty", "qwert", "qwer", "asdf", "asdfgh", "zxcvbn", "zxcvb",
    "1qaz", "2wsx", "3edc", "1qaz2wsx", "1q2w3e", "1q2w3e4r",
    "qazwsx", "qazwsxedc", "!qaz", "1qaz!",
    "asdfjkl", "qwertyuiop",
]

_KB_ADJACENT: dict[str, list[str]] = {
    "q": ["w", "a", "1"], "w": ["q", "e", "s", "2"], "e": ["w", "r", "d", "3"],
    "r": ["e", "t", "f", "4"], "t": ["r", "y", "g", "5"], "y": ["t", "u", "h", "6"],
    "a": ["q", "w", "s", "z"], "s": ["a", "w", "d", "x"], "d": ["s", "e", "f", "c"],
    "1": ["2", "q"], "2": ["1", "3", "w"], "3": ["2", "4", "e"],
}


def apply_capitalization(token: str) -> list[str]:
    """Apply cognitive capitalization patterns to a token.

    Humans overwhelmingly capitalize only the first letter (>60% of cases in
    breach data per Wang et al. 2017), followed by all-caps and last-letter.
    """
    results = [token]
    if not token:
        return results
    results.append(token.lower())
    results.append(token.upper())
    results.append(token.capitalize())
    results.append(token[0].lower() + token[1:].upper() if len(token) > 1 else token)
    if len(token) > 1:
        results.append(token[:-1].lower() + token[-1].upper())
        results.append("".join(
            c.upper() if i % 2 == 0 else c.lower()
            for i, c in enumerate(token)
        ))
    return list(set(results))


def apply_numeric_suffixes(token: str) -> Generator[str, None, None]:
    """Append common numeric suffixes mimicking cognitive number choices.

    Covers: single digits, birth year ranges, sequences, and lucky numbers.
    Serial position effect: numbers placed at end >85% of the time.
    """
    for suffix in _COMMON_SUFFIXES:
        yield token + suffix

    for year in _YEAR_RANGE:
        yield token + str(year)
        yield token + str(year)[-2:]


def apply_prefix_transforms(token: str) -> Generator[str, None, None]:
    """Prepend common prefixes. Rarer than suffixes (~15% of modified passwords)."""
    for prefix in _COMMON_PREFIXES:
        yield prefix + token


def apply_leet_partial(token: str) -> list[str]:
    """Apply partial leetspeak: replace only the first occurrence of one char.

    Cognitive research shows users rarely apply full leet substitution;
    the most common pattern is a single substitution (e.g., 'p4ssword').
    """
    results = []
    low = token.lower()
    for orig, repl in _LEET_PARTIAL.items():
        if orig in low:
            results.append(low.replace(orig, repl, 1))
            cap = low.replace(orig, repl, 1)
            results.append(cap[0].upper() + cap[1:] if len(cap) > 1 else cap)
    return results


def apply_separator_concat(
    token_a: str,
    token_b: str,
) -> Generator[str, None, None]:
    """Concatenate two tokens with common separators.

    Models the cognitive pattern of combining two meaningful words with a
    minimal separator to satisfy complexity requirements.
    """
    for sep in _SEPARATORS:
        yield token_a + sep + token_b
        yield token_b + sep + token_a


def apply_keyboard_walk_mutation(token: str, max_mutations: int = 2) -> list[str]:
    """Replace characters with keyboard-adjacent keys (typo-style mutation).

    Models the cognitive shortcut of using nearby keys as 'random' variation.
    Limited to max_mutations per token to stay realistic.
    """
    results = []
    low = token.lower()
    for i, ch in enumerate(low):
        if ch in _KB_ADJACENT and max_mutations > 0:
            for adj in _KB_ADJACENT[ch][:2]:
                mutated = low[:i] + adj + low[i + 1:]
                results.append(mutated)
    return results


def apply_year_increment(token: str) -> list[str]:
    """Detect trailing year patterns and generate incremented variants.

    Models the cognitive pattern of incrementing year when forced to change
    passwords periodically: "pass2024" -> "pass2025", "pass2026".
    """
    import re
    results = []
    m = re.search(r"(.*?)((?:19|20)\d{2})(.*)$", token)
    if m:
        prefix, year_str, suffix = m.group(1), m.group(2), m.group(3)
        year = int(year_str)
        for delta in range(-2, 4):
            if delta != 0:
                results.append(prefix + str(year + delta) + suffix)
        results.append(prefix + year_str[-2:] + suffix)
        for delta in range(-2, 4):
            results.append(prefix + str(year + delta)[-2:] + suffix)
    return results


def apply_credential_mutation(old_pw: str) -> set[str]:
    """Generate mutations of a known old password.

    Models credential reuse: users modify old passwords minimally when forced.
    Patterns from Pearman et al. (2019) and Das et al. (2014).
    """
    import re
    candidates: set[str] = set()
    candidates.add(old_pw)
    candidates.add(old_pw[::-1])

    for cap in apply_capitalization(old_pw):
        candidates.add(cap)

    for s in ["1", "!", "2", "3", "12", "123", "!!", "@", "#", "1!", "!1"]:
        candidates.add(old_pw + s)
        candidates.add(s + old_pw)

    for leet in apply_leet_partial(old_pw):
        candidates.add(leet)

    m = re.search(r"^(.*?)(\d+)$", old_pw)
    if m:
        base, num_str = m.group(1), m.group(2)
        num = int(num_str)
        width = len(num_str)
        for delta in [-1, 1, 2, 10, 100]:
            candidates.add(base + str(num + delta).zfill(width))

    candidates.update(apply_year_increment(old_pw))

    if len(old_pw) > 4:
        candidates.add(old_pw[:-1])
        candidates.add(old_pw[1:])
        candidates.add(old_pw + old_pw[-1])

    return candidates


def transform_token(token: str) -> set[str]:
    """Apply all Layer 2 transforms to a single token.

    Returns the complete cognitive transform set C(t) for token t.
    """
    candidates: set[str] = set()

    for cap in apply_capitalization(token):
        candidates.add(cap)
        for suffixed in apply_numeric_suffixes(cap):
            candidates.add(suffixed)

    for prefixed in apply_prefix_transforms(token):
        candidates.add(prefixed)

    for leet in apply_leet_partial(token):
        candidates.add(leet)
        candidates.add(leet + "!")
        candidates.add(leet + "1")
        for s in ["123", "@", "#"]:
            candidates.add(leet + s)

    for kb in apply_keyboard_walk_mutation(token):
        candidates.add(kb)

    candidates.update(apply_year_increment(token))

    return candidates


def transform_pair(token_a: str, token_b: str) -> set[str]:
    """Apply concatenation transforms to a pair of tokens."""
    candidates: set[str] = set()
    variants_a = [token_a, token_a.lower(), token_a.capitalize(), token_a.upper()]
    variants_b = [token_b, token_b.lower(), token_b.capitalize(), token_b.upper()]
    for va in set(variants_a):
        for vb in set(variants_b):
            for sep in _SEPARATORS:
                candidates.add(va + sep + vb)
                candidates.add(vb + sep + va)
            for suffix in ["1", "!", "123", "12", "@", "#", "!!", "1!", "$"]:
                candidates.add(va + vb + suffix)
                candidates.add(vb + va + suffix)
    return candidates


def transform_triple(token_a: str, token_b: str, token_c: str) -> set[str]:
    """Concatenate three tokens with common separators.

    Models the cognitive pattern of building passwords from 3 fragments:
    name + date + symbol, keyword + number + suffix, etc.
    """
    candidates: set[str] = set()
    short_seps = ["", ".", "_", "-", "@"]
    for sep in short_seps:
        candidates.add(token_a + sep + token_b + sep + token_c)
        candidates.add(token_a + sep + token_c + sep + token_b)
        candidates.add(token_b + sep + token_a + sep + token_c)
    candidates.add(token_a + token_b + token_c)
    candidates.add(token_a.capitalize() + token_b + token_c)
    return candidates

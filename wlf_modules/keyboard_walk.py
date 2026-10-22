"""
keyboard_walk.py - Geracao de candidatos a senha baseados em keyboard walk patterns.

Gera combinacoes de teclas adjacentes percorridas em sequencia no teclado,
um padrao extremamente comum em senhas reais (qwerty, asdfgh, zxcvbn, etc.).
Suporta layouts QWERTY (US International) e ABNT2 (Portugues Brasileiro).

Funcionalidades:
  - Grafos de adjacencia para QWERTY e ABNT2
  - Walks conhecidos (hardcoded) comuns em dicionarios de cracking
  - Geracao por travessia do grafo de adjacencia
  - Variantes com Shift (maiusculas e simbolos)
  - Deteccao de keyboard walks em strings existentes
  - Deduplicacao automatica

Exemplos:
  from wlf_modules.keyboard_walk import generate_keyboard_walks, is_keyboard_walk

  for walk in generate_keyboard_walks(max_results=100):
      print(walk)

  if is_keyboard_walk("qwerty"):
      print("Keyboard walk detectado")

Autor: Andre Henrique (@mrhenrike) | Uniao Geek
Versao: 1.0.0
"""
from __future__ import annotations

import logging
from collections.abc import Generator

logger = logging.getLogger(__name__)

# ── Shift mappings ──────────────────────────────────────────────────────────

_SHIFT_MAP: dict[str, str] = {
    "`": "~", "1": "!", "2": "@", "3": "#", "4": "$", "5": "%",
    "6": "^", "7": "&", "8": "*", "9": "(", "0": ")",
    "-": "_", "=": "+", "[": "{", "]": "}", "\\": "|",
    ";": ":", "'": '"', ",": "<", ".": ">", "/": "?",
    "q": "Q", "w": "W", "e": "E", "r": "R", "t": "T",
    "y": "Y", "u": "U", "i": "I", "o": "O", "p": "P",
    "a": "A", "s": "S", "d": "D", "f": "F", "g": "G",
    "h": "H", "j": "J", "k": "K", "l": "L",
    "z": "Z", "x": "X", "c": "C", "v": "V", "b": "B",
    "n": "N", "m": "M",
}

# ── QWERTY US International adjacency graph ─────────────────────────────────
#
# Layout reference:
#   ` 1 2 3 4 5 6 7 8 9 0 - =
#     q w e r t y u i o p [ ] \
#      a s d f g h j k l ; '
#       z x c v b n m , . /

_QWERTY_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "`": ["1"],
    "1": ["`", "2", "q"],
    "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "e"],
    "4": ["3", "5", "e", "r"],
    "5": ["4", "6", "r", "t"],
    "6": ["5", "7", "t", "y"],
    "7": ["6", "8", "y", "u"],
    "8": ["7", "9", "u", "i"],
    "9": ["8", "0", "i", "o"],
    "0": ["9", "-", "o", "p"],
    "-": ["0", "=", "p", "["],
    "=": ["-", "[", "]"],
    # Top letter row
    "q": ["1", "2", "w", "a"],
    "w": ["2", "3", "q", "e", "a", "s"],
    "e": ["3", "4", "w", "r", "s", "d"],
    "r": ["4", "5", "e", "t", "d", "f"],
    "t": ["5", "6", "r", "y", "f", "g"],
    "y": ["6", "7", "t", "u", "g", "h"],
    "u": ["7", "8", "y", "i", "h", "j"],
    "i": ["8", "9", "u", "o", "j", "k"],
    "o": ["9", "0", "i", "p", "k", "l"],
    "p": ["0", "-", "o", "[", "l", ";"],
    "[": ["-", "=", "p", "]", ";", "'"],
    "]": ["=", "[", "\\", "'"],
    "\\": ["]"],
    # Home row
    "a": ["q", "w", "s", "z"],
    "s": ["w", "e", "a", "d", "z", "x"],
    "d": ["e", "r", "s", "f", "x", "c"],
    "f": ["r", "t", "d", "g", "c", "v"],
    "g": ["t", "y", "f", "h", "v", "b"],
    "h": ["y", "u", "g", "j", "b", "n"],
    "j": ["u", "i", "h", "k", "n", "m"],
    "k": ["i", "o", "j", "l", "m", ","],
    "l": ["o", "p", "k", ";", ",", "."],
    ";": ["p", "[", "l", "'", ".", "/"],
    "'": ["[", "]", ";", "/"],
    # Bottom row
    "z": ["a", "s", "x"],
    "x": ["s", "d", "z", "c"],
    "c": ["d", "f", "x", "v"],
    "v": ["f", "g", "c", "b"],
    "b": ["g", "h", "v", "n"],
    "n": ["h", "j", "b", "m"],
    "m": ["j", "k", "n", ","],
    ",": ["k", "l", "m", "."],
    ".": ["l", ";", ",", "/"],
    "/": [";", "'", "."],
}

# ── ABNT2 Brazilian Portuguese adjacency graph ──────────────────────────────
#
# Layout reference:
#   ' 1 2 3 4 5 6 7 8 9 0 - =
#     q w e r t y u i o p ´ [
#      a s d f g h j k l ç ~
#       z x c v b n m , . ;

_ABNT2_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "'": ["1"],
    "1": ["'", "2", "q"],
    "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "e"],
    "4": ["3", "5", "e", "r"],
    "5": ["4", "6", "r", "t"],
    "6": ["5", "7", "t", "y"],
    "7": ["6", "8", "y", "u"],
    "8": ["7", "9", "u", "i"],
    "9": ["8", "0", "i", "o"],
    "0": ["9", "-", "o", "p"],
    "-": ["0", "=", "p", "´"],
    "=": ["-", "´", "["],
    # Top letter row
    "q": ["1", "2", "w", "a"],
    "w": ["2", "3", "q", "e", "a", "s"],
    "e": ["3", "4", "w", "r", "s", "d"],
    "r": ["4", "5", "e", "t", "d", "f"],
    "t": ["5", "6", "r", "y", "f", "g"],
    "y": ["6", "7", "t", "u", "g", "h"],
    "u": ["7", "8", "y", "i", "h", "j"],
    "i": ["8", "9", "u", "o", "j", "k"],
    "o": ["9", "0", "i", "p", "k", "l"],
    "p": ["0", "-", "o", "´", "l", "ç"],
    "´": ["-", "=", "p", "[", "ç", "~"],
    "[": ["=", "´", "~"],
    # Home row
    "a": ["q", "w", "s", "z"],
    "s": ["w", "e", "a", "d", "z", "x"],
    "d": ["e", "r", "s", "f", "x", "c"],
    "f": ["r", "t", "d", "g", "c", "v"],
    "g": ["t", "y", "f", "h", "v", "b"],
    "h": ["y", "u", "g", "j", "b", "n"],
    "j": ["u", "i", "h", "k", "n", "m"],
    "k": ["i", "o", "j", "l", "m", ","],
    "l": ["o", "p", "k", "ç", ",", "."],
    "ç": ["p", "´", "l", "~", ".", ";"],
    "~": ["´", "[", "ç", ";"],
    # Bottom row
    "z": ["a", "s", "x"],
    "x": ["s", "d", "z", "c"],
    "c": ["d", "f", "x", "v"],
    "v": ["f", "g", "c", "b"],
    "b": ["g", "h", "v", "n"],
    "n": ["h", "j", "b", "m"],
    "m": ["j", "k", "n", ","],
    ",": ["k", "l", "m", "."],
    ".": ["l", "ç", ",", ";"],
    ";": ["ç", "~", "."],
}

_LAYOUTS: dict[str, dict[str, list[str]]] = {
    "qwerty": _QWERTY_ADJACENCY,
    "abnt2": _ABNT2_ADJACENCY,
}

# ── Known keyboard walk patterns ────────────────────────────────────────────

_KNOWN_WALKS: list[str] = [
    "qwerty", "qwertyuiop", "qwert", "qwer", "asdfgh", "asdfghjkl",
    "asdf", "zxcvbn", "zxcvbnm", "zxcv", "1234567890", "123456789",
    "12345678", "1234567", "123456", "12345", "1234", "qazwsx",
    "qazwsxedc", "zaq12wsx", "1qaz2wsx", "1qaz2wsx3edc",
    "!qaz2wsx", "1q2w3e4r", "1q2w3e", "1q2w3e4r5t",
    "zaq1xsw2", "mnbvcxz", "poiuytrewq", "lkjhgfdsa",
    "0987654321", "plmokn", "qpalzm", "qazsedcft",
    "asdfjkl", "qwerasdf", "poiulkjm",
    # ABNT2-specific
    "çlkjhg", "ç~lkjh",
    # Diagonal walks
    "qaz", "wsx", "edc", "rfv", "tgb", "yhn", "ujm",
    "zaq", "xsw", "cde", "vfr", "bgt", "nhy", "mju",
    # Number row patterns
    "147852", "258963", "321654", "654987",
    # Repeated patterns
    "qqwwee", "aassdd", "zzxxcc",
]

# ── Public API ──────────────────────────────────────────────────────────────


def list_layouts() -> list[str]:
    """Return available keyboard layout names."""
    return sorted(_LAYOUTS.keys())


def _get_adjacency(layout: str) -> dict[str, list[str]]:
    """Resolve layout name to adjacency graph; raise on unknown layout."""
    layout_lower = layout.lower()
    if layout_lower not in _LAYOUTS:
        raise ValueError(f"Layout desconhecido: {layout!r}. Disponiveis: {list_layouts()}")
    return _LAYOUTS[layout_lower]


def _apply_shift(text: str) -> str:
    """Apply shift mapping to produce uppercase and symbol variants."""
    return "".join(_SHIFT_MAP.get(ch, ch) for ch in text)


def _walk_from_key(
    start: str,
    adjacency: dict[str, list[str]],
    min_length: int,
    max_length: int,
    visited: set[str] | None = None,
    current_path: str = "",
) -> Generator[str, None, None]:
    """Recursively walk the adjacency graph from a starting key.

    Yields all paths of length between min_length and max_length,
    visiting each key at most once per path.
    """
    current_path = current_path + start
    if visited is None:
        visited = set()
    visited = visited | {start}

    if len(current_path) >= min_length:
        yield current_path

    if len(current_path) >= max_length:
        return

    neighbors = adjacency.get(start, [])
    for neighbor in neighbors:
        if neighbor not in visited:
            yield from _walk_from_key(
                neighbor, adjacency, min_length, max_length,
                visited, current_path,
            )


def generate_keyboard_walks(
    layout: str = "qwerty",
    min_length: int = 4,
    max_length: int = 12,
    include_shifted: bool = True,
    include_known: bool = True,
    walk_depth: int = 3,
    max_results: int = 0,
) -> Generator[str, None, None]:
    """Generate password candidates based on keyboard walk patterns.

    Args:
        layout: Keyboard layout to use ("qwerty" or "abnt2").
        min_length: Minimum walk length (inclusive).
        max_length: Maximum walk length (inclusive).
        include_shifted: Also yield uppercase and Shift+symbol variants.
        include_known: Include hardcoded known walk patterns.
        walk_depth: Maximum recursion depth for graph traversal per start key.
            Higher values produce more candidates but take longer.
        max_results: Maximum number of candidates to yield; 0 for unlimited.

    Yields:
        Unique keyboard walk strings matching the specified criteria.
    """
    adjacency = _get_adjacency(layout)
    seen: set[str] = set()
    count = 0

    def _emit(candidate: str) -> bool:
        """Track seen candidates; return True if limit reached."""
        nonlocal count
        if candidate in seen:
            return False
        if len(candidate) < min_length or len(candidate) > max_length:
            return False
        seen.add(candidate)
        count += 1
        return True

    def _check_limit() -> bool:
        return max_results > 0 and count >= max_results

    # Phase 1: known walks
    if include_known:
        for walk in _KNOWN_WALKS:
            if _emit(walk):
                yield walk
                if _check_limit():
                    return

            if include_shifted:
                shifted = _apply_shift(walk)
                if shifted != walk and _emit(shifted):
                    yield shifted
                    if _check_limit():
                        return

    # Phase 2: graph traversal walks
    effective_max = min(max_length, walk_depth + max_length)
    for start_key in adjacency:
        for walk in _walk_from_key(start_key, adjacency, min_length, effective_max):
            if len(walk) > max_length:
                continue
            if _emit(walk):
                yield walk
                if _check_limit():
                    return

            if include_shifted:
                shifted = _apply_shift(walk)
                if shifted != walk and _emit(shifted):
                    yield shifted
                    if _check_limit():
                        return

    logger.debug("keyboard_walk: gerados %d candidatos unicos (layout=%s)", count, layout)


def is_keyboard_walk(
    password: str,
    layout: str = "qwerty",
    min_consecutive: int = 3,
) -> bool:
    """Check if a string contains a keyboard walk pattern.

    A keyboard walk is detected when at least min_consecutive characters
    in sequence are adjacent on the specified keyboard layout.

    Args:
        password: The string to analyze.
        layout: Keyboard layout for adjacency check.
        min_consecutive: Minimum consecutive adjacent keys to consider a walk.

    Returns:
        True if a keyboard walk pattern is detected; False otherwise.
    """
    if len(password) < min_consecutive:
        return False

    adjacency = _get_adjacency(layout)

    # Normalize to lowercase for adjacency lookup
    lower_pw = password.lower()
    consecutive = 1

    for i in range(len(lower_pw) - 1):
        current = lower_pw[i]
        next_char = lower_pw[i + 1]

        neighbors = adjacency.get(current, [])
        if next_char in neighbors:
            consecutive += 1
            if consecutive >= min_consecutive:
                return True
        else:
            consecutive = 1

    lower_full = lower_pw
    return any(len(walk) >= min_consecutive and walk in lower_full for walk in _KNOWN_WALKS)

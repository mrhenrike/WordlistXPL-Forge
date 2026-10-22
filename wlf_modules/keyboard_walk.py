"""
keyboard_walk.py - Geracao de candidatos a senha baseados em keyboard walk patterns.

Gera combinacoes de teclas adjacentes percorridas em sequencia no teclado,
um padrao extremamente comum em senhas reais (qwerty, asdfgh, zxcvbn, etc.).

Layouts suportados:
  - QWERTY (US International)
  - ABNT2 (Portugues Brasileiro)
  - AZERTY (Frances)
  - QWERTZ (Alemao/Suico)
  - DVORAK (US Dvorak)
  - COLEMAK
  - QWERTY_LATAM (Espanhol Latino-Americano)
  - QWERTY_PT (Portugues de Portugal)
  - QWERTY_IT (Italiano)

Funcionalidades:
  - Grafos de adjacencia para 9 layouts ocidentais
  - Walks conhecidos (hardcoded) comuns em dicionarios de cracking
  - Geracao por travessia do grafo de adjacencia
  - Variantes com Shift (maiusculas e simbolos)
  - Deteccao de keyboard walks em strings existentes
  - Deduplicacao automatica

Exemplos:
  from wlf_modules.keyboard_walk import generate_keyboard_walks, is_keyboard_walk

  for walk in generate_keyboard_walks(layout="azerty", max_results=100):
      print(walk)

  if is_keyboard_walk("qwerty"):
      print("Keyboard walk detectado")

Autor: Andre Henrique (@mrhenrike) | Uniao Geek
Versao: 2.0.0
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

_AZERTY_SHIFT_MAP: dict[str, str] = {
    "&": "1", "é": "2", '"': "3", "'": "4", "(": "5", "-": "6",
    "è": "7", "_": "8", "ç": "9", "à": "0", ")": "°", "=": "+",
    "a": "A", "z": "Z", "e": "E", "r": "R", "t": "T",
    "y": "Y", "u": "U", "i": "I", "o": "O", "p": "P",
    "^": "¨", "$": "£",
    "q": "Q", "s": "S", "d": "D", "f": "F", "g": "G",
    "h": "H", "j": "J", "k": "K", "l": "L", "m": "M",
    "ù": "%", "*": "µ",
    "<": ">", "w": "W", "x": "X", "c": "C", "v": "V", "b": "B",
    "n": "N", ",": "?", ";": ".", ":": "/", "!": "§",
}

_QWERTZ_SHIFT_MAP: dict[str, str] = {
    "^": "°", "1": "!", "2": '"', "3": "§", "4": "$", "5": "%",
    "6": "&", "7": "/", "8": "(", "9": ")", "0": "=", "ß": "?", "´": "`",
    "q": "Q", "w": "W", "e": "E", "r": "R", "t": "T",
    "z": "Z", "u": "U", "i": "I", "o": "O", "p": "P",
    "ü": "Ü", "+": "*",
    "a": "A", "s": "S", "d": "D", "f": "F", "g": "G",
    "h": "H", "j": "J", "k": "K", "l": "L",
    "ö": "Ö", "ä": "Ä", "#": "'",
    "<": ">", "y": "Y", "x": "X", "c": "C", "v": "V", "b": "B",
    "n": "N", "m": "M", ",": ";", ".": ":", "-": "_",
}

_DVORAK_SHIFT_MAP: dict[str, str] = {
    "`": "~", "1": "!", "2": "@", "3": "#", "4": "$", "5": "%",
    "6": "^", "7": "&", "8": "*", "9": "(", "0": ")", "[": "{", "]": "}",
    "'": '"', ",": "<", ".": ">", "/": "?", "=": "+", "\\": "|",
    "p": "P", "y": "Y", "f": "F", "g": "G", "c": "C", "r": "R", "l": "L",
    "a": "A", "o": "O", "e": "E", "u": "U", "i": "I",
    "d": "D", "h": "H", "t": "T", "n": "N", "s": "S", "-": "_",
    ";": ":", "q": "Q", "j": "J", "k": "K", "x": "X",
    "b": "B", "m": "M", "w": "W", "v": "V", "z": "Z",
}

_LATAM_SHIFT_MAP: dict[str, str] = {
    "|": "°", "1": "!", "2": '"', "3": "#", "4": "$", "5": "%",
    "6": "&", "7": "/", "8": "(", "9": ")", "0": "=", "'": "?", "¿": "¡",
    "q": "Q", "w": "W", "e": "E", "r": "R", "t": "T",
    "y": "Y", "u": "U", "i": "I", "o": "O", "p": "P",
    "´": "¨", "+": "*",
    "a": "A", "s": "S", "d": "D", "f": "F", "g": "G",
    "h": "H", "j": "J", "k": "K", "l": "L", "ñ": "Ñ",
    "{": "[", "}": "]",
    "<": ">", "z": "Z", "x": "X", "c": "C", "v": "V", "b": "B",
    "n": "N", "m": "M", ",": ";", ".": ":", "-": "_",
}

_PT_SHIFT_MAP: dict[str, str] = {
    "\\": "|", "1": "!", "2": '"', "3": "#", "4": "$", "5": "%",
    "6": "&", "7": "/", "8": "(", "9": ")", "0": "=", "'": "?", "«": "»",
    "q": "Q", "w": "W", "e": "E", "r": "R", "t": "T",
    "y": "Y", "u": "U", "i": "I", "o": "O", "p": "P",
    "+": "*", "´": "`",
    "a": "A", "s": "S", "d": "D", "f": "F", "g": "G",
    "h": "H", "j": "J", "k": "K", "l": "L", "ç": "Ç", "º": "ª",
    "<": ">", "z": "Z", "x": "X", "c": "C", "v": "V", "b": "B",
    "n": "N", "m": "M", ",": ";", ".": ":", "-": "_",
}

_IT_SHIFT_MAP: dict[str, str] = {
    "\\": "|", "1": "!", "2": '"', "3": "£", "4": "$", "5": "%",
    "6": "&", "7": "/", "8": "(", "9": ")", "0": "=", "'": "?", "ì": "^",
    "q": "Q", "w": "W", "e": "E", "r": "R", "t": "T",
    "y": "Y", "u": "U", "i": "I", "o": "O", "p": "P",
    "è": "[", "+": "*",
    "a": "A", "s": "S", "d": "D", "f": "F", "g": "G",
    "h": "H", "j": "J", "k": "K", "l": "L",
    "ò": "@", "à": "#", "ù": "§",
    "<": ">", "z": "Z", "x": "X", "c": "C", "v": "V", "b": "B",
    "n": "N", "m": "M", ",": ";", ".": ":", "-": "_",
}

_LAYOUT_SHIFT_MAPS: dict[str, dict[str, str]] = {
    "qwerty": _SHIFT_MAP,
    "abnt2": _SHIFT_MAP,
    "azerty": _AZERTY_SHIFT_MAP,
    "qwertz": _QWERTZ_SHIFT_MAP,
    "dvorak": _DVORAK_SHIFT_MAP,
    "colemak": _SHIFT_MAP,
    "qwerty_latam": _LATAM_SHIFT_MAP,
    "qwerty_pt": _PT_SHIFT_MAP,
    "qwerty_it": _IT_SHIFT_MAP,
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

# ── AZERTY French adjacency graph ───────────────────────────────────────────
#
# Layout reference:
#   & é " ' ( - è _ ç à ) =
#     a z e r t y u i o p ^ $
#      q s d f g h j k l m ù *
#       < w x c v b n , ; : !

_AZERTY_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "&": ["é"],
    "é": ["&", '"', "a"],
    '"': ["é", "'", "a", "z"],
    "'": ['"', "(", "z", "e"],
    "(": ["'", "-", "e", "r"],
    "-": ["(", "è", "r", "t"],
    "è": ["-", "_", "t", "y"],
    "_": ["è", "ç", "y", "u"],
    "ç": ["_", "à", "u", "i"],
    "à": ["ç", ")", "i", "o"],
    ")": ["à", "=", "o", "p"],
    "=": [")", "p", "^"],
    # Top letter row
    "a": ["é", '"', "z", "q"],
    "z": ['"', "'", "a", "e", "q", "s"],
    "e": ["'", "(", "z", "r", "s", "d"],
    "r": ["(", "-", "e", "t", "d", "f"],
    "t": ["-", "è", "r", "y", "f", "g"],
    "y": ["è", "_", "t", "u", "g", "h"],
    "u": ["_", "ç", "y", "i", "h", "j"],
    "i": ["ç", "à", "u", "o", "j", "k"],
    "o": ["à", ")", "i", "p", "k", "l"],
    "p": [")", "=", "o", "^", "l", "m"],
    "^": ["=", "p", "$", "m", "ù"],
    "$": ["^", "ù", "*"],
    # Home row
    "q": ["a", "z", "s", "<"],
    "s": ["z", "e", "q", "d", "<", "w"],
    "d": ["e", "r", "s", "f", "w", "x"],
    "f": ["r", "t", "d", "g", "x", "c"],
    "g": ["t", "y", "f", "h", "c", "v"],
    "h": ["y", "u", "g", "j", "v", "b"],
    "j": ["u", "i", "h", "k", "b", "n"],
    "k": ["i", "o", "j", "l", "n", ","],
    "l": ["o", "p", "k", "m", ",", ";"],
    "m": ["p", "^", "l", "ù", ";", ":"],
    "ù": ["^", "$", "m", "*", ":", "!"],
    "*": ["$", "ù", "!"],
    # Bottom row
    "<": ["q", "s", "w"],
    "w": ["s", "d", "<", "x"],
    "x": ["d", "f", "w", "c"],
    "c": ["f", "g", "x", "v"],
    "v": ["g", "h", "c", "b"],
    "b": ["h", "j", "v", "n"],
    "n": ["j", "k", "b", ","],
    ",": ["k", "l", "n", ";"],
    ";": ["l", "m", ",", ":"],
    ":": ["m", "ù", ";", "!"],
    "!": ["ù", "*", ":"],
}

# ── QWERTZ German/Swiss adjacency graph ─────────────────────────────────────
#
# Layout reference:
#   ^ 1 2 3 4 5 6 7 8 9 0 ß ´
#     q w e r t z u i o p ü +
#      a s d f g h j k l ö ä #
#       < y x c v b n m , . -

_QWERTZ_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "^": ["1"],
    "1": ["^", "2", "q"],
    "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "e"],
    "4": ["3", "5", "e", "r"],
    "5": ["4", "6", "r", "t"],
    "6": ["5", "7", "t", "z"],
    "7": ["6", "8", "z", "u"],
    "8": ["7", "9", "u", "i"],
    "9": ["8", "0", "i", "o"],
    "0": ["9", "ß", "o", "p"],
    "ß": ["0", "´", "p", "ü"],
    "´": ["ß", "ü", "+"],
    # Top letter row
    "q": ["1", "2", "w", "a"],
    "w": ["2", "3", "q", "e", "a", "s"],
    "e": ["3", "4", "w", "r", "s", "d"],
    "r": ["4", "5", "e", "t", "d", "f"],
    "t": ["5", "6", "r", "z", "f", "g"],
    "z": ["6", "7", "t", "u", "g", "h"],
    "u": ["7", "8", "z", "i", "h", "j"],
    "i": ["8", "9", "u", "o", "j", "k"],
    "o": ["9", "0", "i", "p", "k", "l"],
    "p": ["0", "ß", "o", "ü", "l", "ö"],
    "ü": ["ß", "´", "p", "+", "ö", "ä"],
    "+": ["´", "ü", "ä", "#"],
    # Home row
    "a": ["q", "w", "s", "<"],
    "s": ["w", "e", "a", "d", "<", "y"],
    "d": ["e", "r", "s", "f", "y", "x"],
    "f": ["r", "t", "d", "g", "x", "c"],
    "g": ["t", "z", "f", "h", "c", "v"],
    "h": ["z", "u", "g", "j", "v", "b"],
    "j": ["u", "i", "h", "k", "b", "n"],
    "k": ["i", "o", "j", "l", "n", "m"],
    "l": ["o", "p", "k", "ö", "m", ","],
    "ö": ["p", "ü", "l", "ä", ",", "."],
    "ä": ["ü", "+", "ö", "#", ".", "-"],
    "#": ["+", "ä", "-"],
    # Bottom row
    "<": ["a", "s", "y"],
    "y": ["s", "d", "<", "x"],
    "x": ["d", "f", "y", "c"],
    "c": ["f", "g", "x", "v"],
    "v": ["g", "h", "c", "b"],
    "b": ["h", "j", "v", "n"],
    "n": ["j", "k", "b", "m"],
    "m": ["k", "l", "n", ","],
    ",": ["l", "ö", "m", "."],
    ".": ["ö", "ä", ",", "-"],
    "-": ["ä", "#", "."],
}

# ── DVORAK US adjacency graph ───────────────────────────────────────────────
#
# Layout reference:
#   ` 1 2 3 4 5 6 7 8 9 0 [ ]
#     ' , . p y f g c r l / = \
#      a o e u i d h t n s -
#       ; q j k x b m w v z

_DVORAK_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "`": ["1"],
    "1": ["`", "2", "'"],
    "2": ["1", "3", "'", ","],
    "3": ["2", "4", ",", "."],
    "4": ["3", "5", ".", "p"],
    "5": ["4", "6", "p", "y"],
    "6": ["5", "7", "y", "f"],
    "7": ["6", "8", "f", "g"],
    "8": ["7", "9", "g", "c"],
    "9": ["8", "0", "c", "r"],
    "0": ["9", "[", "r", "l"],
    "[": ["0", "]", "l", "/"],
    "]": ["[", "/", "="],
    # Top letter row
    "'": ["1", "2", ",", "a"],
    ",": ["2", "3", "'", ".", "a", "o"],
    ".": ["3", "4", ",", "p", "o", "e"],
    "p": ["4", "5", ".", "y", "e", "u"],
    "y": ["5", "6", "p", "f", "u", "i"],
    "f": ["6", "7", "y", "g", "i", "d"],
    "g": ["7", "8", "f", "c", "d", "h"],
    "c": ["8", "9", "g", "r", "h", "t"],
    "r": ["9", "0", "c", "l", "t", "n"],
    "l": ["0", "[", "r", "/", "n", "s"],
    "/": ["[", "]", "l", "=", "s", "-"],
    "=": ["]", "/", "\\", "-"],
    "\\": ["="],
    # Home row
    "a": ["'", ",", "o", ";"],
    "o": [",", ".", "a", "e", ";", "q"],
    "e": [".", "p", "o", "u", "q", "j"],
    "u": ["p", "y", "e", "i", "j", "k"],
    "i": ["y", "f", "u", "d", "k", "x"],
    "d": ["f", "g", "i", "h", "x", "b"],
    "h": ["g", "c", "d", "t", "b", "m"],
    "t": ["c", "r", "h", "n", "m", "w"],
    "n": ["r", "l", "t", "s", "w", "v"],
    "s": ["l", "/", "n", "-", "v", "z"],
    "-": ["/", "=", "s", "z"],
    # Bottom row
    ";": ["a", "o", "q"],
    "q": ["o", "e", ";", "j"],
    "j": ["e", "u", "q", "k"],
    "k": ["u", "i", "j", "x"],
    "x": ["i", "d", "k", "b"],
    "b": ["d", "h", "x", "m"],
    "m": ["h", "t", "b", "w"],
    "w": ["t", "n", "m", "v"],
    "v": ["n", "s", "w", "z"],
    "z": ["s", "-", "v"],
}

# ── COLEMAK adjacency graph ─────────────────────────────────────────────────
#
# Layout reference:
#   ` 1 2 3 4 5 6 7 8 9 0 - =
#     q w f p g j l u y ; [ ] \
#      a r s t d h n e i o '
#       z x c v b k m , . /

_COLEMAK_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "`": ["1"],
    "1": ["`", "2", "q"],
    "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "f"],
    "4": ["3", "5", "f", "p"],
    "5": ["4", "6", "p", "g"],
    "6": ["5", "7", "g", "j"],
    "7": ["6", "8", "j", "l"],
    "8": ["7", "9", "l", "u"],
    "9": ["8", "0", "u", "y"],
    "0": ["9", "-", "y", ";"],
    "-": ["0", "=", ";", "["],
    "=": ["-", "[", "]"],
    # Top letter row
    "q": ["1", "2", "w", "a"],
    "w": ["2", "3", "q", "f", "a", "r"],
    "f": ["3", "4", "w", "p", "r", "s"],
    "p": ["4", "5", "f", "g", "s", "t"],
    "g": ["5", "6", "p", "j", "t", "d"],
    "j": ["6", "7", "g", "l", "d", "h"],
    "l": ["7", "8", "j", "u", "h", "n"],
    "u": ["8", "9", "l", "y", "n", "e"],
    "y": ["9", "0", "u", ";", "e", "i"],
    ";": ["0", "-", "y", "[", "i", "o"],
    "[": ["-", "=", ";", "]", "o", "'"],
    "]": ["=", "[", "\\", "'"],
    "\\": ["]"],
    # Home row
    "a": ["q", "w", "r", "z"],
    "r": ["w", "f", "a", "s", "z", "x"],
    "s": ["f", "p", "r", "t", "x", "c"],
    "t": ["p", "g", "s", "d", "c", "v"],
    "d": ["g", "j", "t", "h", "v", "b"],
    "h": ["j", "l", "d", "n", "b", "k"],
    "n": ["l", "u", "h", "e", "k", "m"],
    "e": ["u", "y", "n", "i", "m", ","],
    "i": ["y", ";", "e", "o", ",", "."],
    "o": [";", "[", "i", "'", ".", "/"],
    "'": ["[", "]", "o", "/"],
    # Bottom row
    "z": ["a", "r", "x"],
    "x": ["r", "s", "z", "c"],
    "c": ["s", "t", "x", "v"],
    "v": ["t", "d", "c", "b"],
    "b": ["d", "h", "v", "k"],
    "k": ["h", "n", "b", "m"],
    "m": ["n", "e", "k", ","],
    ",": ["e", "i", "m", "."],
    ".": ["i", "o", ",", "/"],
    "/": ["o", "'", "."],
}

# ── QWERTY Latin American Spanish adjacency graph ───────────────────────────
#
# Layout reference:
#   | 1 2 3 4 5 6 7 8 9 0 ' ¿
#     q w e r t y u i o p ´ +
#      a s d f g h j k l ñ { }
#       < z x c v b n m , . -

_LATAM_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "|": ["1"],
    "1": ["|", "2", "q"],
    "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "e"],
    "4": ["3", "5", "e", "r"],
    "5": ["4", "6", "r", "t"],
    "6": ["5", "7", "t", "y"],
    "7": ["6", "8", "y", "u"],
    "8": ["7", "9", "u", "i"],
    "9": ["8", "0", "i", "o"],
    "0": ["9", "'", "o", "p"],
    "'": ["0", "¿", "p", "´"],
    "¿": ["'", "´", "+"],
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
    "p": ["0", "'", "o", "´", "l", "ñ"],
    "´": ["'", "¿", "p", "+", "ñ", "{"],
    "+": ["¿", "´", "{", "}"],
    # Home row
    "a": ["q", "w", "s", "<"],
    "s": ["w", "e", "a", "d", "<", "z"],
    "d": ["e", "r", "s", "f", "z", "x"],
    "f": ["r", "t", "d", "g", "x", "c"],
    "g": ["t", "y", "f", "h", "c", "v"],
    "h": ["y", "u", "g", "j", "v", "b"],
    "j": ["u", "i", "h", "k", "b", "n"],
    "k": ["i", "o", "j", "l", "n", "m"],
    "l": ["o", "p", "k", "ñ", "m", ","],
    "ñ": ["p", "´", "l", "{", ",", "."],
    "{": ["´", "+", "ñ", "}", ".", "-"],
    "}": ["+", "{", "-"],
    # Bottom row
    "<": ["a", "s", "z"],
    "z": ["s", "d", "<", "x"],
    "x": ["d", "f", "z", "c"],
    "c": ["f", "g", "x", "v"],
    "v": ["g", "h", "c", "b"],
    "b": ["h", "j", "v", "n"],
    "n": ["j", "k", "b", "m"],
    "m": ["k", "l", "n", ","],
    ",": ["l", "ñ", "m", "."],
    ".": ["ñ", "{", ",", "-"],
    "-": ["{", "}", "."],
}

# ── QWERTY Portuguese (Portugal) adjacency graph ────────────────────────────
#
# Layout reference:
#   \ 1 2 3 4 5 6 7 8 9 0 ' «
#     q w e r t y u i o p + ´
#      a s d f g h j k l ç º
#       < z x c v b n m , . -

_PT_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "\\": ["1"],
    "1": ["\\", "2", "q"],
    "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "e"],
    "4": ["3", "5", "e", "r"],
    "5": ["4", "6", "r", "t"],
    "6": ["5", "7", "t", "y"],
    "7": ["6", "8", "y", "u"],
    "8": ["7", "9", "u", "i"],
    "9": ["8", "0", "i", "o"],
    "0": ["9", "'", "o", "p"],
    "'": ["0", "«", "p", "+"],
    "«": ["'", "+", "´"],
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
    "p": ["0", "'", "o", "+", "l", "ç"],
    "+": ["'", "«", "p", "´", "ç", "º"],
    "´": ["«", "+", "º"],
    # Home row
    "a": ["q", "w", "s", "<"],
    "s": ["w", "e", "a", "d", "<", "z"],
    "d": ["e", "r", "s", "f", "z", "x"],
    "f": ["r", "t", "d", "g", "x", "c"],
    "g": ["t", "y", "f", "h", "c", "v"],
    "h": ["y", "u", "g", "j", "v", "b"],
    "j": ["u", "i", "h", "k", "b", "n"],
    "k": ["i", "o", "j", "l", "n", "m"],
    "l": ["o", "p", "k", "ç", "m", ","],
    "ç": ["p", "+", "l", "º", ",", "."],
    "º": ["+", "´", "ç", "."],
    # Bottom row
    "<": ["a", "s", "z"],
    "z": ["s", "d", "<", "x"],
    "x": ["d", "f", "z", "c"],
    "c": ["f", "g", "x", "v"],
    "v": ["g", "h", "c", "b"],
    "b": ["h", "j", "v", "n"],
    "n": ["j", "k", "b", "m"],
    "m": ["k", "l", "n", ","],
    ",": ["l", "ç", "m", "."],
    ".": ["ç", "º", ",", "-"],
    "-": ["º", "."],
}

# ── QWERTY Italian adjacency graph ──────────────────────────────────────────
#
# Layout reference:
#   \ 1 2 3 4 5 6 7 8 9 0 ' ì
#     q w e r t y u i o p è +
#      a s d f g h j k l ò à ù
#       < z x c v b n m , . -

_IT_ADJACENCY: dict[str, list[str]] = {
    # Number row
    "\\": ["1"],
    "1": ["\\", "2", "q"],
    "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "e"],
    "4": ["3", "5", "e", "r"],
    "5": ["4", "6", "r", "t"],
    "6": ["5", "7", "t", "y"],
    "7": ["6", "8", "y", "u"],
    "8": ["7", "9", "u", "i"],
    "9": ["8", "0", "i", "o"],
    "0": ["9", "'", "o", "p"],
    "'": ["0", "ì", "p", "è"],
    "ì": ["'", "è", "+"],
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
    "p": ["0", "'", "o", "è", "l", "ò"],
    "è": ["'", "ì", "p", "+", "ò", "à"],
    "+": ["ì", "è", "à", "ù"],
    # Home row
    "a": ["q", "w", "s", "<"],
    "s": ["w", "e", "a", "d", "<", "z"],
    "d": ["e", "r", "s", "f", "z", "x"],
    "f": ["r", "t", "d", "g", "x", "c"],
    "g": ["t", "y", "f", "h", "c", "v"],
    "h": ["y", "u", "g", "j", "v", "b"],
    "j": ["u", "i", "h", "k", "b", "n"],
    "k": ["i", "o", "j", "l", "n", "m"],
    "l": ["o", "p", "k", "ò", "m", ","],
    "ò": ["p", "è", "l", "à", ",", "."],
    "à": ["è", "+", "ò", "ù", ".", "-"],
    "ù": ["+", "à", "-"],
    # Bottom row
    "<": ["a", "s", "z"],
    "z": ["s", "d", "<", "x"],
    "x": ["d", "f", "z", "c"],
    "c": ["f", "g", "x", "v"],
    "v": ["g", "h", "c", "b"],
    "b": ["h", "j", "v", "n"],
    "n": ["j", "k", "b", "m"],
    "m": ["k", "l", "n", ","],
    ",": ["l", "ò", "m", "."],
    ".": ["ò", "à", ",", "-"],
    "-": ["à", "ù", "."],
}

# ── Layout registry ─────────────────────────────────────────────────────────

_LAYOUTS: dict[str, dict[str, list[str]]] = {
    "qwerty": _QWERTY_ADJACENCY,
    "abnt2": _ABNT2_ADJACENCY,
    "azerty": _AZERTY_ADJACENCY,
    "qwertz": _QWERTZ_ADJACENCY,
    "dvorak": _DVORAK_ADJACENCY,
    "colemak": _COLEMAK_ADJACENCY,
    "qwerty_latam": _LATAM_ADJACENCY,
    "qwerty_pt": _PT_ADJACENCY,
    "qwerty_it": _IT_ADJACENCY,
}

# ── Known keyboard walk patterns ────────────────────────────────────────────

_KNOWN_WALKS: list[str] = [
    # QWERTY / universal
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
    # AZERTY-specific
    "azerty", "azertyuiop", "qsdfgh", "qsdfghjklm", "wxcvbn",
    "azertyuiopqsdfghjklm", "azer1234",
    # QWERTZ-specific
    "qwertz", "qwertzuiop", "yxcvbnm", "qwert12345",
    # DVORAK-specific
    "aoeui", "aoeusnth", "aoeuidhtns",
    # COLEMAK-specific
    "arst", "arstdhneio", "qwfpg",
    # QWERTY_LATAM-specific
    "qwertyñ", "asdfghñ",
    # QWERTY_PT-specific
    "qwertyç", "asdfghç",
    # QWERTY_IT-specific
    "qwertyè", "asdfghò",
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


def _apply_shift(text: str, layout: str = "qwerty") -> str:
    """Apply layout-specific shift mapping to produce uppercase and symbol variants."""
    shift_map = _LAYOUT_SHIFT_MAPS.get(layout.lower(), _SHIFT_MAP)
    return "".join(shift_map.get(ch, ch) for ch in text)


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
        layout: Keyboard layout name (see list_layouts()).
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
    layout_lower = layout.lower()
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
                shifted = _apply_shift(walk, layout_lower)
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
                shifted = _apply_shift(walk, layout_lower)
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

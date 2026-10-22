"""
lyrics_engine.py - Password candidate generation from song lyrics.

Extracts meaningful tokens, acronyms, and short phrases from raw lyric
text and transforms them into password candidates using common human
patterns: first-letter acronyms, memorable phrases, keyword mutations,
line-initial combos, and title-case fragments.

Does not depend on any external API; lyrics are provided as plain text
via file or stdin.

Inspired by lyricpass (initstring) with deeper mutation coverage.

Usage (as library):
    from wlf_modules.lyrics_engine import generate_from_lyrics
    text = open("song.txt").read()
    for pw in generate_from_lyrics(text, artist="Legiao Urbana"):
        print(pw)

Usage (CLI):
    wlf.py lyrics --file song.txt --artist "Legiao Urbana"
    cat song.txt | wlf.py lyrics --artist "Legiao Urbana"

Author: Andre Henrique (@mrhenrike)
Version: 1.0.0
"""
from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Generator
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__info__ = {
    "name": "lyrics_engine",
    "version": "1.0.0",
    "author": "Andre Henrique (@mrhenrike)",
    "description": "Password generation from song lyrics (acronyms, phrases, mutations)",
    "category": "profiling",
    "tags": ["lyrics", "passphrase", "profiling", "cultural"],
}

_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "it", "its", "be", "as", "do", "no", "not",
    "so", "if", "my", "me", "we", "he", "she", "you", "your", "his", "her",
    "our", "up", "oh", "ah", "yeah", "da", "la", "na", "um", "uma",
    "de", "do", "dos", "das", "em", "que", "se", "por", "com", "para",
    "eu", "tu", "ele", "ela", "nos", "te", "me", "esse", "essa",
    "este", "esta", "isso", "aqui", "ali", "tao", "mais", "muito",
    "o", "e", "ou",
})

_COMMON_SUFFIXES = ["!", "@", "#", "123", "1234", "1", "01", "00"]

_LEET_MAP = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}


def _normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _extract_lines(text: str) -> list[str]:
    """Split lyrics into non-empty, stripped lines."""
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _extract_keywords(text: str, min_len: int = 4) -> list[str]:
    """Extract unique content words from text, filtering stop words."""
    words = re.findall(r"[a-zA-ZÀ-ÿ]+", _normalize(text))
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        w_clean = _normalize(w)
        if len(w_clean) >= min_len and w_clean not in _STOP_WORDS and w_clean not in seen:
            seen.add(w_clean)
            result.append(w_clean)
    return result


def _line_acronym(line: str) -> str:
    """Build an acronym from the first letter of each word in a line."""
    words = re.findall(r"[a-zA-ZÀ-ÿ]+", line)
    return "".join(w[0] for w in words if w).lower()


def _short_phrases(lines: list[str], max_words: int = 4) -> list[str]:
    """Extract short memorable phrases (2-4 words) from lines."""
    result: list[str] = []
    for line in lines:
        words = re.findall(r"[a-zA-ZÀ-ÿ]+", line)
        norm_words = [_normalize(w) for w in words]
        content = [w for w in norm_words if w not in _STOP_WORDS and len(w) >= 2]
        if 2 <= len(content) <= max_words:
            result.append("".join(content))
            if len(content) <= 3:
                result.append("".join(w.capitalize() for w in content))
    return result


def _mutate(base: str) -> list[str]:
    """Apply common password mutations to a base string."""
    variants: list[str] = [base]

    if base:
        variants.append(base.capitalize())
        variants.append(base[0].upper() + base[1:] if len(base) > 1 else base.upper())

    for suffix in _COMMON_SUFFIXES:
        variants.append(base + suffix)
        if base:
            variants.append(base.capitalize() + suffix)

    leet = "".join(_LEET_MAP.get(c, c) for c in base)
    if leet != base:
        variants.append(leet)
        for suffix in ["!", "123"]:
            variants.append(leet + suffix)

    return variants


def generate_from_lyrics(
    lyrics_text: str,
    *,
    artist: str = "",
    title: str = "",
    max_candidates: int = 0,
) -> Generator[str, None, None]:
    """Generate password candidates from song lyrics.

    Strategies:
      1. Per-line acronyms (first letter of each word)
      2. Keywords (content words >= 4 chars)
      3. Short phrases (2-4 content words concatenated)
      4. Artist/title tokens
      5. Combined artist+keyword patterns
      6. All above with suffix/leet mutations

    Args:
        lyrics_text: Raw lyrics as plain text.
        artist: Optional artist/band name.
        title: Optional song title.
        max_candidates: Limit output (0 = unlimited).

    Yields:
        Unique password candidate strings.
    """
    lines = _extract_lines(lyrics_text)
    keywords = _extract_keywords(lyrics_text)
    phrases = _short_phrases(lines)

    seen: set[str] = set()
    emitted = 0

    def _emit(candidate: str) -> bool:
        nonlocal emitted
        c = candidate.strip()
        if not c or len(c) < 4 or c in seen:
            return False
        seen.add(c)
        emitted += 1
        return True

    acronyms: list[str] = []
    for line in lines:
        acr = _line_acronym(line)
        if 3 <= len(acr) <= 20:
            acronyms.append(acr)

    full_acronym = "".join(acronyms) if acronyms else ""
    if 4 <= len(full_acronym) <= 30:
        for v in _mutate(full_acronym):
            if _emit(v):
                yield v
                if max_candidates and emitted >= max_candidates:
                    return

    for acr in acronyms:
        for v in _mutate(acr):
            if _emit(v):
                yield v
                if max_candidates and emitted >= max_candidates:
                    return

    for kw in keywords[:50]:
        for v in _mutate(kw):
            if _emit(v):
                yield v
                if max_candidates and emitted >= max_candidates:
                    return

    for phrase in phrases[:30]:
        for v in _mutate(phrase):
            if _emit(v):
                yield v
                if max_candidates and emitted >= max_candidates:
                    return

    meta_tokens: list[str] = []
    if artist:
        art_norm = _normalize(artist)
        art_words = [w for w in re.findall(r"[a-z]+", art_norm) if len(w) >= 2]
        meta_tokens.extend(art_words)
        joined = "".join(art_words)
        if len(joined) >= 3:
            meta_tokens.append(joined)
    if title:
        title_norm = _normalize(title)
        title_words = [w for w in re.findall(r"[a-z]+", title_norm) if len(w) >= 2]
        meta_tokens.extend(title_words)
        joined = "".join(title_words)
        if len(joined) >= 3:
            meta_tokens.append(joined)

    for tok in meta_tokens:
        for v in _mutate(tok):
            if _emit(v):
                yield v
                if max_candidates and emitted >= max_candidates:
                    return

    for tok in meta_tokens:
        for kw in keywords[:15]:
            for combo in [tok + kw, kw + tok, tok + kw.capitalize()]:
                for v in _mutate(combo):
                    if _emit(v):
                        yield v
                        if max_candidates and emitted >= max_candidates:
                            return

    for i, acr in enumerate(acronyms):
        for tok in meta_tokens[:5]:
            for combo in [acr + tok, tok + acr]:
                if _emit(combo):
                    yield combo
                    if max_candidates and emitted >= max_candidates:
                        return

    first_words: list[str] = []
    for line in lines:
        words = re.findall(r"[a-zA-ZÀ-ÿ]+", line)
        if words:
            w = _normalize(words[0])
            if len(w) >= 3 and w not in _STOP_WORDS:
                first_words.append(w)

    if 2 <= len(first_words) <= 8:
        combo = "".join(first_words)
        if len(combo) <= 30:
            for v in _mutate(combo):
                if _emit(v):
                    yield v
                    if max_candidates and emitted >= max_candidates:
                        return


def run(
    lyrics_text: str = "",
    lyrics_file: str = "",
    artist: str = "",
    title: str = "",
    max_candidates: int = 0,
) -> list[str]:
    """Generate lyrics-based passwords and return as list.

    Reads lyrics from ``lyrics_text`` or ``lyrics_file``.
    """
    text = lyrics_text
    if not text and lyrics_file:
        p = Path(lyrics_file)
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
        else:
            logger.error("Lyrics file not found: %s", lyrics_file)
            return []
    if not text:
        logger.error("No lyrics text provided.")
        return []

    return list(generate_from_lyrics(
        text,
        artist=artist,
        title=title,
        max_candidates=max_candidates,
    ))


def handle_lyrics(
    args: Any, _ctx: dict[str, Any]
) -> Generator[str, None, None] | None:
    """CLI handler for the lyrics subcommand."""
    import sys

    lyrics_file = getattr(args, "file", None)
    artist = getattr(args, "artist", "") or ""
    title = getattr(args, "title", "") or ""
    limit = getattr(args, "limit", 0) or 0

    text = ""
    if lyrics_file:
        p = Path(lyrics_file)
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
        else:
            logger.error("File not found: %s", lyrics_file)
            return None
    elif not sys.stdin.isatty():
        text = sys.stdin.read()

    if not text:
        logger.error("Provide lyrics via --file or stdin.")
        return None

    return generate_from_lyrics(text, artist=artist, title=title, max_candidates=limit)

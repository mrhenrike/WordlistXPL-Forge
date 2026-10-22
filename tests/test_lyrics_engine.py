"""Tests for lyrics_engine module."""
from __future__ import annotations

SAMPLE_LYRICS = """\
Que pais e este
No fundo do poco
Que pais e este
Nas favelas do alento
"""

SAMPLE_LYRICS_EN = """\
Is this the real life
Is this just fantasy
Caught in a landslide
No escape from reality
"""


class TestNormalize:

    def test_strips_accents(self):
        from wlf_modules.lyrics_engine import _normalize
        assert _normalize("Legião") == "legiao"
        assert _normalize("café") == "cafe"

    def test_lowercases(self):
        from wlf_modules.lyrics_engine import _normalize
        assert _normalize("HELLO") == "hello"


class TestExtractLines:

    def test_splits_and_strips(self):
        from wlf_modules.lyrics_engine import _extract_lines
        lines = _extract_lines("hello\n  world  \n\n  foo  ")
        assert lines == ["hello", "world", "foo"]

    def test_empty(self):
        from wlf_modules.lyrics_engine import _extract_lines
        assert _extract_lines("") == []
        assert _extract_lines("\n\n\n") == []


class TestExtractKeywords:

    def test_filters_stop_words(self):
        from wlf_modules.lyrics_engine import _extract_keywords
        kw = _extract_keywords("the quick brown fox and the lazy dog")
        assert "quick" in kw
        assert "brown" in kw
        assert "lazy" in kw
        assert "the" not in kw
        assert "and" not in kw

    def test_min_length(self):
        from wlf_modules.lyrics_engine import _extract_keywords
        kw = _extract_keywords("cat dog elephant")
        assert "cat" not in kw
        assert "dog" not in kw
        assert "elephant" in kw

    def test_unique(self):
        from wlf_modules.lyrics_engine import _extract_keywords
        kw = _extract_keywords("hello hello hello world world")
        assert kw.count("hello") == 1
        assert kw.count("world") == 1


class TestLineAcronym:

    def test_basic(self):
        from wlf_modules.lyrics_engine import _line_acronym
        assert _line_acronym("Is this the real life") == "ittrl"

    def test_empty(self):
        from wlf_modules.lyrics_engine import _line_acronym
        assert _line_acronym("") == ""


class TestShortPhrases:

    def test_extracts_phrases(self):
        from wlf_modules.lyrics_engine import _short_phrases
        lines = ["the quick brown fox", "hello world and more"]
        phrases = _short_phrases(lines)
        assert len(phrases) > 0

    def test_skips_long_lines(self):
        from wlf_modules.lyrics_engine import _short_phrases
        lines = ["one two three four five six seven eight nine ten"]
        phrases = _short_phrases(lines)
        assert len(phrases) == 0


class TestMutate:

    def test_includes_base(self):
        from wlf_modules.lyrics_engine import _mutate
        variants = _mutate("test")
        assert "test" in variants

    def test_includes_capitalized(self):
        from wlf_modules.lyrics_engine import _mutate
        variants = _mutate("test")
        assert "Test" in variants

    def test_includes_suffixes(self):
        from wlf_modules.lyrics_engine import _mutate
        variants = _mutate("test")
        assert "test123" in variants
        assert "test!" in variants
        assert "Test123" in variants

    def test_includes_leet(self):
        from wlf_modules.lyrics_engine import _mutate
        variants = _mutate("test")
        assert "7357" in variants

    def test_empty_base(self):
        from wlf_modules.lyrics_engine import _mutate
        variants = _mutate("")
        assert "" in variants


class TestGenerateFromLyrics:

    def test_produces_candidates(self):
        from wlf_modules.lyrics_engine import generate_from_lyrics
        results = list(generate_from_lyrics(SAMPLE_LYRICS_EN))
        assert len(results) > 10

    def test_no_duplicates(self):
        from wlf_modules.lyrics_engine import generate_from_lyrics
        results = list(generate_from_lyrics(SAMPLE_LYRICS_EN))
        assert len(results) == len(set(results))

    def test_min_length_4(self):
        from wlf_modules.lyrics_engine import generate_from_lyrics
        results = list(generate_from_lyrics(SAMPLE_LYRICS_EN))
        for r in results:
            assert len(r) >= 4

    def test_with_artist(self):
        from wlf_modules.lyrics_engine import generate_from_lyrics
        without = set(generate_from_lyrics(SAMPLE_LYRICS))
        with_artist = set(generate_from_lyrics(SAMPLE_LYRICS, artist="Legiao Urbana"))
        assert len(with_artist) > len(without)

    def test_with_title(self):
        from wlf_modules.lyrics_engine import generate_from_lyrics
        without = set(generate_from_lyrics(SAMPLE_LYRICS_EN))
        with_title = set(generate_from_lyrics(SAMPLE_LYRICS_EN, title="Bohemian Rhapsody"))
        assert len(with_title) > len(without)

    def test_max_candidates(self):
        from wlf_modules.lyrics_engine import generate_from_lyrics
        results = list(generate_from_lyrics(SAMPLE_LYRICS_EN, max_candidates=10))
        assert len(results) == 10

    def test_acronyms_present(self):
        from wlf_modules.lyrics_engine import generate_from_lyrics
        results = list(generate_from_lyrics(SAMPLE_LYRICS_EN))
        found_short = [r for r in results if len(r) <= 8 and r.isalpha() and r.islower()]
        assert len(found_short) > 0

    def test_portuguese_lyrics(self):
        from wlf_modules.lyrics_engine import generate_from_lyrics
        results = list(generate_from_lyrics(SAMPLE_LYRICS, artist="Legiao Urbana"))
        assert len(results) > 20


class TestRun:

    def test_from_text(self):
        from wlf_modules.lyrics_engine import run
        result = run(lyrics_text=SAMPLE_LYRICS_EN)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_from_file(self, tmp_path):
        from wlf_modules.lyrics_engine import run
        f = tmp_path / "song.txt"
        f.write_text(SAMPLE_LYRICS_EN, encoding="utf-8")
        result = run(lyrics_file=str(f))
        assert len(result) > 0

    def test_missing_file(self):
        from wlf_modules.lyrics_engine import run
        result = run(lyrics_file="/nonexistent/song.txt")
        assert result == []

    def test_no_input(self):
        from wlf_modules.lyrics_engine import run
        result = run()
        assert result == []

    def test_max_candidates(self):
        from wlf_modules.lyrics_engine import run
        result = run(lyrics_text=SAMPLE_LYRICS_EN, max_candidates=5)
        assert len(result) == 5


class TestHandleLyrics:

    def test_with_file(self, tmp_path):
        from types import SimpleNamespace

        from wlf_modules.lyrics_engine import handle_lyrics
        f = tmp_path / "lyrics.txt"
        f.write_text(SAMPLE_LYRICS_EN, encoding="utf-8")
        args = SimpleNamespace(file=str(f), artist="Queen", title="", limit=0)
        gen = handle_lyrics(args, {})
        assert gen is not None
        results = list(gen)
        assert len(results) > 0

    def test_missing_file(self):
        from types import SimpleNamespace

        from wlf_modules.lyrics_engine import handle_lyrics
        args = SimpleNamespace(file="/nonexistent.txt", artist="", title="", limit=0)
        result = handle_lyrics(args, {})
        assert result is None

    def test_no_input(self, monkeypatch):
        import io
        from types import SimpleNamespace

        from wlf_modules.lyrics_engine import handle_lyrics
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        args = SimpleNamespace(file=None, artist="", title="", limit=0)
        result = handle_lyrics(args, {})
        assert result is None

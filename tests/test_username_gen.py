"""Tests for username_gen module."""
from __future__ import annotations


class TestNormalize:

    def test_strips_accents(self):
        from wlf_modules.username_gen import _normalize
        assert _normalize("José") == "jose"
        assert _normalize("André") == "andre"
        assert _normalize("Müller") == "muller"

    def test_lowercases(self):
        from wlf_modules.username_gen import _normalize
        assert _normalize("MARIA") == "maria"

    def test_strips_whitespace(self):
        from wlf_modules.username_gen import _normalize
        assert _normalize("  ana ") == "ana"


class TestInitials:

    def test_single_char(self):
        from wlf_modules.username_gen import _initials
        assert _initials("jose") == "j"

    def test_empty(self):
        from wlf_modules.username_gen import _initials
        assert _initials("") == ""


class TestGenerateUsernames:

    def test_basic_first_last(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Maria", "Silva"))
        assert len(results) > 10
        assert "mariasilva" in results
        assert "maria.silva" in results
        assert "maria_silva" in results
        assert "silvamaria" in results
        assert "msilva" in results

    def test_with_year(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Ana", "Costa", year="1990"))
        assert "ana1990" in results
        assert "ana90" in results
        assert "anacosta1990" in results
        assert "anacosta90" in results

    def test_with_nickname(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Juliana", "Oliveira", nickname="ju"))
        assert "ju" in results
        assert "juoliveira" in results
        assert "ju.oliveira" in results

    def test_nick_differs_from_first(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Carlos", "Souza", nickname="kadu"))
        assert "kaducarlos" in results
        assert "carloskadu" in results

    def test_first_only(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Pedro"))
        assert "pedro" in results
        assert "pedro123" in results

    def test_max_results(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Maria", "Silva", max_results=5))
        assert len(results) == 5

    def test_no_duplicates(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Ana", "Costa", nickname="ana", year="1985"))
        assert len(results) == len(set(results))

    def test_sorted_by_length(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Maria", "Silva"))
        lengths = [len(u) for u in results]
        assert lengths == sorted(lengths)

    def test_accent_normalization(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("José", "Gonçalves"))
        assert "josegoncalves" in results
        assert "jose.goncalves" in results

    def test_prefix_patterns(self):
        from wlf_modules.username_gen import generate_usernames
        results = list(generate_usernames("Lucas", "Mendes"))
        assert "thelucas" in results
        assert "reallucas" in results
        assert "mrlucas" in results


class TestRun:

    def test_returns_list(self):
        from wlf_modules.username_gen import run
        result = run(first_name="Ana", last_name="Lima")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_input(self):
        from wlf_modules.username_gen import run
        result = run()
        assert isinstance(result, list)


class TestHandleUsername:

    def test_missing_args_returns_none(self):
        from types import SimpleNamespace

        from wlf_modules.username_gen import handle_username
        args = SimpleNamespace(first="", last="", nick="", year="", limit=0)
        result = handle_username(args, {})
        assert result is None

    def test_with_args_returns_generator(self):
        from types import SimpleNamespace

        from wlf_modules.username_gen import handle_username
        args = SimpleNamespace(first="Ana", last="Costa", nick="", year="", limit=0)
        gen = handle_username(args, {})
        assert gen is not None
        results = list(gen)
        assert len(results) > 0

    def test_limit_respected(self):
        from types import SimpleNamespace

        from wlf_modules.username_gen import handle_username
        args = SimpleNamespace(first="Ana", last="Costa", nick="", year="", limit=3)
        gen = handle_username(args, {})
        results = list(gen)
        assert len(results) == 3

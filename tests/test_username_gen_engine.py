"""Tests for username_gen_engine module."""
from __future__ import annotations


class TestSanitize:

    def test_strips_accents(self) -> None:
        from wlf_modules.username_gen_engine import _sanitize
        assert _sanitize("André") == "andre"
        assert _sanitize("Juliana") == "juliana"

    def test_removes_non_alnum(self) -> None:
        from wlf_modules.username_gen_engine import _sanitize
        assert _sanitize("O'Brien") == "obrien"
        assert _sanitize("Van der Berg") == "vanderberg"


class TestEmailLocal:

    def test_extracts_local(self) -> None:
        from wlf_modules.username_gen_engine import _email_local
        assert _email_local("juliana@corp.com") == "juliana"

    def test_no_at(self) -> None:
        from wlf_modules.username_gen_engine import _email_local
        assert _email_local("juliana") == ""

    def test_empty(self) -> None:
        from wlf_modules.username_gen_engine import _email_local
        assert _email_local("") == ""


class TestNameFormats:

    def test_basic_patterns(self) -> None:
        from wlf_modules.username_gen_engine import _name_formats
        patterns = _name_formats("Juliana", "Oliveira")
        assert "juliana" in patterns
        assert "oliveira" in patterns
        assert "julianaoliveira" in patterns
        assert "joliveira" in patterns
        assert "j.oliveira" in patterns
        assert "juliana.oliveira" in patterns

    def test_first_only(self) -> None:
        from wlf_modules.username_gen_engine import _name_formats
        patterns = _name_formats("Juliana", "")
        assert "juliana" in patterns
        assert len(patterns) >= 3

    def test_last_only(self) -> None:
        from wlf_modules.username_gen_engine import _name_formats
        patterns = _name_formats("", "Oliveira")
        assert "oliveira" in patterns

    def test_both_empty(self) -> None:
        from wlf_modules.username_gen_engine import _name_formats
        assert _name_formats("", "") == []


class TestGenerateUsernames:

    def test_produces_results(self) -> None:
        from wlf_modules.username_gen_engine import generate_usernames
        results = list(generate_usernames("Juliana", "Oliveira"))
        assert len(results) > 20

    def test_no_duplicates(self) -> None:
        from wlf_modules.username_gen_engine import generate_usernames
        results = list(generate_usernames("Juliana", "Oliveira"))
        assert len(results) == len(set(results))

    def test_with_domain(self) -> None:
        from wlf_modules.username_gen_engine import generate_usernames
        results = list(generate_usernames("Juliana", "Oliveira", domain="corp.com"))
        emails = [r for r in results if "@" in r]
        assert len(emails) > 0
        assert all(r.endswith("@corp.com") for r in emails)

    def test_with_email(self) -> None:
        from wlf_modules.username_gen_engine import generate_usernames
        results = list(generate_usernames("Juliana", "Oliveira", email="ju@test.com"))
        assert "ju" in results

    def test_with_nicknames(self) -> None:
        from wlf_modules.username_gen_engine import generate_usernames
        results = list(generate_usernames(
            "Juliana", "Oliveira", nicknames=["julinha", "juju"],
        ))
        assert "julinha" in results
        assert "juju" in results

    def test_max_candidates(self) -> None:
        from wlf_modules.username_gen_engine import generate_usernames
        results = list(generate_usernames("Juliana", "Oliveira", max_candidates=10))
        assert len(results) == 10

    def test_min_length(self) -> None:
        from wlf_modules.username_gen_engine import generate_usernames
        results = list(generate_usernames("Juliana", "Oliveira"))
        for r in results:
            if "@" not in r:
                assert len(r) >= 2


class TestRun:

    def test_returns_list(self) -> None:
        from wlf_modules.username_gen_engine import run
        result = run("Juliana", "Oliveira")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_with_all_params(self) -> None:
        from wlf_modules.username_gen_engine import run
        result = run(
            "Juliana", "Oliveira",
            email="ju@test.com", domain="corp.com",
            nicknames=["juju"], max_candidates=50,
        )
        assert len(result) <= 50
        assert len(result) > 0


class TestHandleUsernameGen:

    def test_basic(self) -> None:
        from wlf_modules.username_gen_engine import handle_username_gen
        from types import SimpleNamespace
        args = SimpleNamespace(
            first="Juliana", last="Oliveira",
            email="", domain="", nicknames=None, limit=0,
        )
        gen = handle_username_gen(args, {})
        assert gen is not None
        results = list(gen)
        assert len(results) > 0

    def test_no_input(self) -> None:
        from wlf_modules.username_gen_engine import handle_username_gen
        from types import SimpleNamespace
        args = SimpleNamespace(
            first="", last="", email="", domain="", nicknames=None, limit=0,
        )
        result = handle_username_gen(args, {})
        assert result is None

    def test_email_only(self) -> None:
        from wlf_modules.username_gen_engine import handle_username_gen
        from types import SimpleNamespace
        args = SimpleNamespace(
            first="", last="", email="admin@test.com",
            domain="", nicknames=None, limit=0,
        )
        gen = handle_username_gen(args, {})
        assert gen is not None
        results = list(gen)
        assert "admin" in results

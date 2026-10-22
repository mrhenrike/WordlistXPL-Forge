"""Tests for diceware_engine module."""
from __future__ import annotations


class TestLoadWordlist:

    def test_missing_file(self) -> None:
        from wlf_modules.diceware_engine import _load_wordlist
        assert _load_wordlist("/nonexistent/words.txt") == []

    def test_from_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from wlf_modules.diceware_engine import _load_wordlist
        f = tmp_path / "words.txt"
        f.write_text("apple\nbanana\ncherry\ndate\nelderberry\n")
        words = _load_wordlist(str(f))
        assert "apple" in words
        assert "banana" in words
        assert len(words) == 5

    def test_filters_short(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from wlf_modules.diceware_engine import _load_wordlist
        f = tmp_path / "words.txt"
        f.write_text("hi\nok\napple\nbanana\n")
        words = _load_wordlist(str(f))
        assert "hi" not in words
        assert "ok" not in words
        assert "apple" in words


class TestMutatePassphrase:

    def test_produces_variants(self) -> None:
        from wlf_modules.diceware_engine import _mutate_passphrase
        variants = _mutate_passphrase(["correct", "horse"], "-")
        assert "correct-horse" in variants
        assert "Correct-Horse" in variants
        assert "CORRECT-HORSE" in variants
        assert "correct-horse1" in variants
        assert "correct-horse123" in variants

    def test_no_duplicates(self) -> None:
        from wlf_modules.diceware_engine import _mutate_passphrase
        variants = _mutate_passphrase(["alpha", "beta"], "")
        assert len(variants) == len(set(variants))


class TestGeneratePassphrases:

    def test_produces_results(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        results = list(generate_passphrases(num_words=3, max_candidates=50, seed=42))
        assert len(results) == 50

    def test_no_duplicates(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        results = list(generate_passphrases(num_words=3, max_candidates=200, seed=42))
        assert len(results) == len(set(results))

    def test_min_length(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        results = list(generate_passphrases(num_words=3, max_candidates=100, seed=42))
        for r in results:
            assert len(r) >= 6

    def test_deterministic_with_seed(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        r1 = list(generate_passphrases(num_words=3, max_candidates=20, seed=42))
        r2 = list(generate_passphrases(num_words=3, max_candidates=20, seed=42))
        assert r1 == r2

    def test_different_seeds(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        r1 = list(generate_passphrases(num_words=3, max_candidates=50, seed=42))
        r2 = list(generate_passphrases(num_words=3, max_candidates=50, seed=99))
        assert r1 != r2

    def test_custom_wordlist(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
        results = list(generate_passphrases(
            num_words=3, wordlist=words, max_candidates=10, seed=42,
        ))
        assert len(results) > 0

    def test_custom_separators(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        results = list(generate_passphrases(
            num_words=3, separators=["_"], max_candidates=30, seed=42,
        ))
        underscore_count = sum(1 for r in results if "_" in r)
        assert underscore_count > 0

    def test_includes_common_passphrases(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        results = list(generate_passphrases(num_words=4, max_candidates=500, seed=42))
        assert "correcthorsebatterystaple" in results

    def test_clamps_num_words(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        results = list(generate_passphrases(num_words=1, max_candidates=10, seed=42))
        assert len(results) > 0

    def test_wordlist_too_small(self) -> None:
        from wlf_modules.diceware_engine import generate_passphrases
        results = list(generate_passphrases(
            num_words=4, wordlist=["one", "two"], max_candidates=10,
        ))
        assert results == []


class TestRun:

    def test_returns_list(self) -> None:
        from wlf_modules.diceware_engine import run
        result = run(num_words=3, max_candidates=20, seed=42)
        assert isinstance(result, list)
        assert len(result) == 20

    def test_with_wordlist_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        from wlf_modules.diceware_engine import run
        f = tmp_path / "words.txt"
        words = ["alpha", "beta", "gamma", "delta", "epsilon",
                 "zeta", "theta", "iota", "kappa", "lambda"]
        f.write_text("\n".join(words))
        result = run(num_words=3, wordlist_file=str(f), max_candidates=10, seed=42)
        assert len(result) > 0


class TestHandleDiceware:

    def test_basic(self) -> None:
        from wlf_modules.diceware_engine import handle_diceware
        from types import SimpleNamespace
        args = SimpleNamespace(
            words=3, wordlist="", separator=None,
            sample=50, limit=20, seed=42,
        )
        gen = handle_diceware(args, {})
        assert gen is not None
        results = list(gen)
        assert len(results) == 20

    def test_with_separator(self) -> None:
        from wlf_modules.diceware_engine import handle_diceware
        from types import SimpleNamespace
        args = SimpleNamespace(
            words=3, wordlist="", separator="-",
            sample=50, limit=30, seed=42,
        )
        gen = handle_diceware(args, {})
        assert gen is not None
        results = list(gen)
        assert any("-" in r for r in results)

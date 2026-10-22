"""Tests for default_creds_engine module."""
from __future__ import annotations


class TestBuiltinDb:

    def test_has_entries(self) -> None:
        from wlf_modules.default_creds_engine import _builtin_db
        db = _builtin_db()
        assert len(db) > 50

    def test_entry_structure(self) -> None:
        from wlf_modules.default_creds_engine import _builtin_db
        db = _builtin_db()
        for entry in db[:10]:
            assert "vendor" in entry
            assert "user" in entry
            assert "password" in entry
            assert "category" in entry


class TestLookup:

    def test_by_vendor(self) -> None:
        from wlf_modules.default_creds_engine import lookup
        results = lookup(vendor="cisco")
        assert len(results) >= 3
        assert all("cisco" in r["vendor"].lower() for r in results)

    def test_by_category(self) -> None:
        from wlf_modules.default_creds_engine import lookup
        results = lookup(category="firewall")
        assert len(results) >= 3
        assert all("firewall" in r["category"].lower() for r in results)

    def test_by_protocol(self) -> None:
        from wlf_modules.default_creds_engine import lookup
        results = lookup(protocol="ssh")
        assert len(results) >= 5

    def test_combined_filters(self) -> None:
        from wlf_modules.default_creds_engine import lookup
        results = lookup(vendor="cisco", protocol="ssh")
        assert len(results) >= 1
        for r in results:
            assert "cisco" in r["vendor"].lower()
            assert "ssh" in r["protocol"].lower()

    def test_no_match(self) -> None:
        from wlf_modules.default_creds_engine import lookup
        results = lookup(vendor="nonexistentvendor123")
        assert results == []

    def test_case_insensitive(self) -> None:
        from wlf_modules.default_creds_engine import lookup
        r1 = lookup(vendor="CISCO")
        r2 = lookup(vendor="cisco")
        assert len(r1) == len(r2)


class TestGeneratePairs:

    def test_colon_format(self) -> None:
        from wlf_modules.default_creds_engine import generate_pairs
        results = list(generate_pairs(vendor="cisco", output_format="colon"))
        assert len(results) > 0
        assert all(":" in r for r in results)

    def test_tab_format(self) -> None:
        from wlf_modules.default_creds_engine import generate_pairs
        results = list(generate_pairs(vendor="cisco", output_format="tab"))
        assert len(results) > 0
        assert all("\t" in r for r in results)

    def test_hydra_format(self) -> None:
        from wlf_modules.default_creds_engine import generate_pairs
        results = list(generate_pairs(vendor="cisco", output_format="hydra"))
        assert len(results) > 0
        assert all(r.startswith("-l ") for r in results)

    def test_no_duplicates(self) -> None:
        from wlf_modules.default_creds_engine import generate_pairs
        results = list(generate_pairs(vendor="cisco"))
        assert len(results) == len(set(results))

    def test_with_variants(self) -> None:
        from wlf_modules.default_creds_engine import generate_pairs
        without = list(generate_pairs(
            vendor="cisco", include_variants=False,
        ))
        with_var = list(generate_pairs(
            vendor="cisco", include_variants=True,
        ))
        assert len(with_var) > len(without)

    def test_max_candidates(self) -> None:
        from wlf_modules.default_creds_engine import generate_pairs
        results = list(generate_pairs(vendor="cisco", max_candidates=5))
        assert len(results) == 5

    def test_ics_category(self) -> None:
        from wlf_modules.default_creds_engine import generate_pairs
        results = list(generate_pairs(category="plc"))
        assert len(results) > 0

    def test_database_category(self) -> None:
        from wlf_modules.default_creds_engine import generate_pairs
        results = list(generate_pairs(category="database"))
        assert len(results) > 0


class TestListVendors:

    def test_returns_sorted_list(self) -> None:
        from wlf_modules.default_creds_engine import list_vendors
        vendors = list_vendors()
        assert len(vendors) > 10
        assert vendors == sorted(vendors)
        assert "cisco" in vendors


class TestListCategories:

    def test_returns_sorted_list(self) -> None:
        from wlf_modules.default_creds_engine import list_categories
        cats = list_categories()
        assert len(cats) > 5
        assert cats == sorted(cats)
        assert "firewall" in cats


class TestStats:

    def test_returns_stats(self) -> None:
        from wlf_modules.default_creds_engine import stats
        s = stats()
        assert s["total_entries"] > 50
        assert s["vendors"] > 10
        assert s["categories"] > 5
        assert s["protocols"] > 5


class TestRun:

    def test_returns_list(self) -> None:
        from wlf_modules.default_creds_engine import run
        result = run(vendor="cisco")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_with_max(self) -> None:
        from wlf_modules.default_creds_engine import run
        result = run(vendor="cisco", max_candidates=3)
        assert len(result) == 3


class TestHandleDefaultCreds:

    def test_basic(self) -> None:
        from wlf_modules.default_creds_engine import handle_default_creds
        from types import SimpleNamespace
        args = SimpleNamespace(
            vendor="cisco", product="", category="",
            protocol="", format="colon", no_variants=False, limit=0,
        )
        gen = handle_default_creds(args, {})
        assert gen is not None
        results = list(gen)
        assert len(results) > 0

    def test_no_filter(self) -> None:
        from wlf_modules.default_creds_engine import handle_default_creds
        from types import SimpleNamespace
        args = SimpleNamespace(
            vendor="", product="", category="",
            protocol="", format="colon", no_variants=False, limit=0,
        )
        result = handle_default_creds(args, {})
        assert result is None

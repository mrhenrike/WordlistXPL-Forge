"""Tests for W14 modules: mask_analyzer, chain_builder, hashcat_rules_db."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestMaskAnalyzer:

    def test_char_to_mask(self):
        from wlf_modules.mask_analyzer import char_to_mask
        assert char_to_mask("A") == "?u"
        assert char_to_mask("a") == "?l"
        assert char_to_mask("0") == "?d"
        assert char_to_mask("!") == "?s"

    def test_password_to_mask(self):
        from wlf_modules.mask_analyzer import password_to_mask
        assert password_to_mask("Abc123!") == "?u?l?l?d?d?d?s"
        assert password_to_mask("test") == "?l?l?l?l"

    def test_mask_keyspace(self):
        from wlf_modules.mask_analyzer import mask_keyspace
        assert mask_keyspace("?d?d?d?d") == 10000
        assert mask_keyspace("?l") == 26

    def test_mask_entropy(self):
        from wlf_modules.mask_analyzer import mask_entropy
        e = mask_entropy("?d?d?d?d")
        assert 13.0 < e < 14.0

    def test_mask_complexity_score(self):
        from wlf_modules.mask_analyzer import mask_complexity_score
        simple = mask_complexity_score("?d?d")
        complex_ = mask_complexity_score("?u?l?l?l?d?d?s")
        assert complex_ > simple

    def test_analyzer_feed_and_analyze(self):
        from wlf_modules.mask_analyzer import MaskAnalyzer
        a = MaskAnalyzer()
        a.feed(["Password1!", "Password2!", "test123", "admin"])
        result = a.analyze()
        assert result.total_passwords == 4
        assert result.unique_masks >= 2
        assert len(result.masks) > 0
        assert result.masks[0].count >= 1

    def test_analyzer_file(self, tmp_path):
        from wlf_modules.mask_analyzer import MaskAnalyzer
        f = tmp_path / "words.txt"
        f.write_text("abc\n123\nAbc1!\n", encoding="utf-8")
        a = MaskAnalyzer()
        a.feed_file(f)
        result = a.analyze()
        assert result.total_passwords == 3

    def test_export_top_masks(self):
        from wlf_modules.mask_analyzer import MaskAnalyzer, export_top_masks
        a = MaskAnalyzer()
        a.feed(["test123"] * 10 + ["admin"] * 5)
        result = a.analyze()
        masks = export_top_masks(result, top_n=5)
        assert len(masks) > 0
        assert masks[0] == "?l?l?l?l?d?d?d"

    def test_export_json(self, tmp_path):
        from wlf_modules.mask_analyzer import MaskAnalyzer, export_json
        a = MaskAnalyzer()
        a.feed(["pass1", "pass2"])
        result = a.analyze()
        out = tmp_path / "result.json"
        export_json(result, out)
        data = json.loads(out.read_text())
        assert data["total_passwords"] == 2

    def test_export_csv(self, tmp_path):
        from wlf_modules.mask_analyzer import MaskAnalyzer, export_csv
        a = MaskAnalyzer()
        a.feed(["abc123"])
        result = a.analyze()
        out = tmp_path / "result.csv"
        export_csv(result, out)
        content = out.read_text()
        assert "rank" in content
        assert "?l?l?l?d?d?d" in content

    def test_heatmap(self):
        from wlf_modules.mask_analyzer import MaskAnalyzer
        a = MaskAnalyzer()
        a.feed(["Ab1!"])
        result = a.analyze()
        assert len(result.heatmap) == 4
        assert result.heatmap[0].upper == 1
        assert result.heatmap[1].lower == 1
        assert result.heatmap[2].digit == 1
        assert result.heatmap[3].special == 1

    def test_reset(self):
        from wlf_modules.mask_analyzer import MaskAnalyzer
        a = MaskAnalyzer()
        a.feed(["test"])
        a.reset()
        result = a.analyze()
        assert result.total_passwords == 0


class TestChainBuilder:

    def test_basic_chain(self):
        from wlf_modules.chain_builder import Chain
        chain = Chain(name="test")
        chain.add_stage("case", [{"name": "capitalize"}, {"name": "upper"}])
        chain.add_stage("suffix", [{"name": "append_custom", "args": {"values": ["1", "!"]}}])
        assert chain.total_combinations() == 4

    def test_generate(self):
        from wlf_modules.chain_builder import Chain
        chain = Chain(name="test")
        chain.add_stage("case", [{"name": "capitalize"}])
        chain.add_stage("suffix", [{"name": "append_custom", "args": {"values": ["1"]}}])
        results = list(chain.generate(["password"]))
        assert "Password1" in results

    def test_dry_run(self):
        from wlf_modules.chain_builder import Chain
        chain = Chain(name="test")
        chain.add_stage("case", [{"name": "noop"}, {"name": "capitalize"}])
        results = chain.dry_run(["test"], limit=5)
        assert "test" in results
        assert "Test" in results

    def test_estimate(self):
        from wlf_modules.chain_builder import Chain
        chain = Chain(name="test")
        chain.add_stage("case", [{"name": "noop"}, {"name": "capitalize"}])
        chain.add_stage("suffix", [{"name": "append_custom", "args": {"values": ["1", "2", "3"]}}])
        assert chain.estimate_candidates(100) == 600

    def test_prebuilt_basic(self):
        from wlf_modules.chain_builder import chain_basic_mangling
        chain = chain_basic_mangling()
        assert chain.total_combinations() > 10
        results = chain.dry_run(["test"], limit=5)
        assert len(results) == 5

    def test_prebuilt_corporate(self):
        from wlf_modules.chain_builder import chain_corporate_pattern
        chain = chain_corporate_pattern()
        results = list(chain.generate(["company"]))
        assert "Company" in results
        assert any("2024" in r for r in results)

    def test_json_roundtrip(self, tmp_path):
        from wlf_modules.chain_builder import Chain, chain_to_json, chain_from_json
        chain = Chain(name="roundtrip")
        chain.add_stage("case", [{"name": "capitalize"}])
        path = tmp_path / "chain.json"
        chain_to_json(chain, path)
        loaded = chain_from_json(path)
        assert loaded.name == "roundtrip"
        assert len(loaded.stages) == 1

    def test_empty_chain(self):
        from wlf_modules.chain_builder import Chain
        chain = Chain(name="empty")
        results = list(chain.generate(["test"]))
        assert results == ["test"]

    def test_leet_transform(self):
        from wlf_modules.chain_builder import Chain
        chain = Chain(name="leet")
        chain.add_stage("leet", [{"name": "leet"}])
        results = list(chain.generate(["password"]))
        assert "p455w0rd" in results

    def test_aggressive_chain(self):
        from wlf_modules.chain_builder import chain_aggressive
        chain = chain_aggressive()
        assert chain.total_combinations() > 100


class TestHashcatRulesDb:

    def test_load_builtin_hob064(self):
        from wlf_modules.hashcat_rules_db import load_builtin
        rs = load_builtin("hob064")
        assert rs.count > 50
        assert rs.meta.name == "Hob064"

    def test_load_builtin_corporate(self):
        from wlf_modules.hashcat_rules_db import load_builtin
        rs = load_builtin("corporate")
        assert rs.count > 20

    def test_load_builtin_brazilian(self):
        from wlf_modules.hashcat_rules_db import load_builtin
        rs = load_builtin("brazilian")
        assert rs.count > 10

    def test_unknown_builtin(self):
        from wlf_modules.hashcat_rules_db import load_builtin
        with pytest.raises(ValueError, match="Unknown"):
            load_builtin("nonexistent")

    def test_deduplicate(self):
        from wlf_modules.hashcat_rules_db import RuleSet, RuleSetMeta
        meta = RuleSetMeta(name="test", author="test", description="test")
        rs = RuleSet(meta=meta, rules=["l", "u", "l", "c", "u"])
        removed = rs.deduplicate()
        assert removed == 2
        assert rs.count == 3

    def test_optimize(self):
        from wlf_modules.hashcat_rules_db import RuleSet, RuleSetMeta
        meta = RuleSetMeta(name="test", author="test", description="test")
        rs = RuleSet(meta=meta, rules=[":", "", "l", "l", "u"])
        stats = rs.optimize()
        assert stats["noops_removed"] == 2
        assert stats["duplicates_removed"] == 1
        assert stats["final_count"] == 2

    def test_apply_to_word(self):
        from wlf_modules.hashcat_rules_db import RuleSet, RuleSetMeta
        meta = RuleSetMeta(name="test", author="test", description="test")
        rs = RuleSet(meta=meta, rules=["l", "u", "c", "$1", "^!"])
        results = list(rs.apply_to_word("test"))
        assert "test" in results
        assert "TEST" in results
        assert "Test" in results
        assert "test1" in results
        assert "!test" in results

    def test_execute_rule_complex(self):
        from wlf_modules.hashcat_rules_db import _execute_rule
        assert _execute_rule("test", "c$1") == "Test1"
        assert _execute_rule("test", "u$!") == "TEST!"
        assert _execute_rule("abc", "r") == "cba"
        assert _execute_rule("test", "d") == "testtest"
        assert _execute_rule("pasta", "sa@") == "p@st@"
        assert _execute_rule("test", "T0") == "Test"

    def test_execute_rule_reject(self):
        from wlf_modules.hashcat_rules_db import _execute_rule
        assert _execute_rule("ab", ">5") is None
        assert _execute_rule("abcdefgh", "<5") is None

    def test_load_from_file(self, tmp_path):
        from wlf_modules.hashcat_rules_db import load_from_file
        f = tmp_path / "test.rule"
        f.write_text("# comment\nl\nu\nc\n\n$1\n", encoding="utf-8")
        rs = load_from_file(f)
        assert rs.count == 4
        assert rs.meta.name == "test"

    def test_merge_rulesets(self):
        from wlf_modules.hashcat_rules_db import load_builtin, merge_rulesets
        rs1 = load_builtin("hob064")
        rs2 = load_builtin("corporate")
        merged = merge_rulesets(rs1, rs2)
        assert merged.count <= rs1.count + rs2.count
        assert merged.count > rs1.count

    def test_export_hashcat(self, tmp_path):
        from wlf_modules.hashcat_rules_db import load_builtin
        rs = load_builtin("hob064")
        out = tmp_path / "hob064.rule"
        rs.export_hashcat(out)
        lines = out.read_text().strip().split("\n")
        assert len(lines) == rs.count

    def test_export_jtr(self, tmp_path):
        from wlf_modules.hashcat_rules_db import RuleSet, RuleSetMeta
        meta = RuleSetMeta(name="test", author="test", description="test")
        rs = RuleSet(meta=meta, rules=["l", "u", "c", "$1"])
        out = tmp_path / "test.conf"
        rs.export_jtr(out)
        content = out.read_text()
        assert "[List.Rules:Generated]" in content

    def test_coverage_against(self):
        from wlf_modules.hashcat_rules_db import RuleSet, RuleSetMeta
        meta = RuleSetMeta(name="test", author="test", description="test")
        rs = RuleSet(meta=meta, rules=["c$1", "u"])
        targets = {"Test1", "TEST", "other"}
        cov = rs.coverage_against(targets, ["test"])
        assert cov["hits"] == 2
        assert cov["total_targets"] == 3

    def test_hashcat_to_jtr_basic(self):
        from wlf_modules.hashcat_rules_db import _hashcat_to_jtr
        assert _hashcat_to_jtr("l") == "l"
        assert _hashcat_to_jtr("$1") == "$1"
        assert _hashcat_to_jtr(":") == ":"
        assert _hashcat_to_jtr("sa@") == "sa@"

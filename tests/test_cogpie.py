"""
test_cogpie.py - Unit tests for the CogPIE module.

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from wlf_modules.cogpie.cognitive_transforms import (
    apply_capitalization,
    apply_leet_partial,
    apply_numeric_suffixes,
    transform_pair,
    transform_token,
)
from wlf_modules.cogpie.engine import CogPIEEngine
from wlf_modules.cogpie.markov_pcfg_hybrid import HybridRanker
from wlf_modules.cogpie.policy_filter import PasswordPolicy, filter_candidates
from wlf_modules.cogpie.scorer import (
    estimate_guesses,
    practical_entropy,
    score_candidate,
    zxcvbn_score,
)
from wlf_modules.cogpie.semantic_expander import (
    expand_date,
    expand_profile,
    expand_token,
)


class TestSemanticExpander:

    def test_expand_token_basic(self):
        variants = expand_token("Andre")
        assert "andre" in variants
        assert "ANDRE" in variants
        assert "Andre" in variants
        assert len(variants) > 5

    def test_expand_token_accents(self):
        variants = expand_token("Joao")
        assert "joao" in variants
        assert "JOAO" in variants

    def test_expand_token_nicknames(self):
        variants = expand_token("Eduardo")
        assert "dudu" in variants or "edu" in variants

    def test_expand_token_leet(self):
        variants = expand_token("password")
        assert any("4" in v or "0" in v for v in variants)

    def test_expand_date_full(self):
        variants = expand_date("15/03/1990")
        assert "1990" in variants
        assert "90" in variants
        assert "15031990" in variants

    def test_expand_date_year_only(self):
        variants = expand_date("1985")
        assert "1985" in variants
        assert "85" in variants

    def test_expand_profile_names(self):
        profile = {
            "names": ["Andre Henrique", "Maria Silva"],
            "dates": ["1990"],
            "keywords": ["futebol"],
            "pets": ["Rex"],
        }
        banks = expand_profile(profile)
        assert len(banks["names"]) > 5
        assert "andre" in banks["names"] or "Andre" in banks["names"]
        assert "ah" in banks["names"] or "AH" in banks["names"]

    def test_expand_profile_phones(self):
        profile = {"phones": ["11987654321"]}
        banks = expand_profile(profile)
        assert "4321" in banks["phones"]


class TestCognitiveTransforms:

    def test_capitalization(self):
        caps = apply_capitalization("password")
        assert "Password" in caps
        assert "PASSWORD" in caps
        assert "password" in caps

    def test_numeric_suffixes(self):
        suffixes = list(apply_numeric_suffixes("test"))
        assert "test1" in suffixes
        assert "test123" in suffixes
        assert any("1990" in s for s in suffixes)

    def test_leet_partial(self):
        leet = apply_leet_partial("password")
        assert any("4" in v for v in leet)

    def test_transform_token(self):
        candidates = transform_token("andre")
        assert len(candidates) > 50

    def test_transform_pair(self):
        candidates = transform_pair("andre", "1990")
        assert any("andre" in c and "1990" in c for c in candidates)


class TestHybridRanker:

    def test_train_and_score(self):
        ranker = HybridRanker()
        for pw in ["password123", "letmein", "qwerty123", "admin2024"]:
            ranker.train(pw)

        score1 = ranker.score("password123")
        score2 = ranker.score("xKz9!mQ#vR2$")
        assert score1 > score2

    def test_rank_ordering(self):
        ranker = HybridRanker()
        corpus = ["password", "password1", "password12", "password123"] * 10
        for pw in corpus:
            ranker.train(pw)

        ranked = ranker.rank(["password", "xz9qmvr2"])
        assert ranked[0][0] == "password"

    def test_train_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for i in range(100):
                f.write(f"testpass{i}\n")
            f.flush()
            ranker = HybridRanker()
            count = ranker.train_from_file(f.name)
            assert count == 100


class TestScorer:

    def test_estimate_guesses_simple(self):
        g = estimate_guesses("123456", known_rank=1)
        assert g == 1.0

    def test_entropy_positive(self):
        e = practical_entropy("Xk9!mQ#vR2$pL")
        assert e > 0

    def test_zxcvbn_score_range(self):
        assert zxcvbn_score(5) == 0
        assert zxcvbn_score(15) == 1
        assert zxcvbn_score(25) == 2
        assert zxcvbn_score(30) == 3
        assert zxcvbn_score(40) == 4

    def test_score_candidate_structure(self):
        result = score_candidate("Password123!")
        assert "candidate" in result
        assert "entropy_bits" in result
        assert "score" in result
        assert result["score"] in range(5)


class TestPolicyFilter:

    def test_policy_accepts(self):
        policy = PasswordPolicy(min_length=8, require_digit=True)
        assert policy.accepts("Password1") is True
        assert policy.accepts("short") is False
        assert policy.accepts("NoDigitsHere") is False

    def test_policy_classes(self):
        policy = PasswordPolicy(min_char_classes=3)
        assert policy.accepts("Abc123") is True
        assert policy.accepts("abcdef") is False

    def test_filter_candidates(self):
        candidates = [("pass", 0.9), ("Password1", 0.8), ("ab", 0.7)]
        policy = PasswordPolicy(min_length=6)
        results = list(filter_candidates(candidates, policy=policy))
        assert len(results) == 1
        assert results[0][0] == "Password1"


class TestCogPIEEngine:

    def test_full_pipeline_no_corpus(self):
        profile = {
            "names": ["Carlos Silva"],
            "dates": ["1985"],
            "keywords": ["flamengo"],
            "pets": ["Rex"],
        }
        engine = CogPIEEngine()
        results = engine.generate(profile, max_candidates=500)
        assert len(results) > 0
        assert len(results) <= 500
        passwords = [r[0] for r in results]
        assert any("carlos" in p.lower() or "silva" in p.lower() for p in passwords)

    def test_full_pipeline_with_corpus(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            corpus = [
                "password123", "letmein", "qwerty", "abc123",
                "admin", "welcome1", "monkey", "dragon",
            ] * 50
            f.write("\n".join(corpus) + "\n")
            f.flush()

            profile = {
                "names": ["Maria"],
                "dates": ["2000"],
                "keywords": ["amor"],
            }
            engine = CogPIEEngine()
            engine.train(f.name, max_lines=400)
            results = engine.generate(profile, max_candidates=200)
            assert len(results) > 0

    def test_stream_mode(self):
        profile = {
            "names": ["Pedro"],
            "dates": ["1995"],
            "keywords": ["gato"],
        }
        engine = CogPIEEngine()
        passwords = list(engine.generate_stream(profile, max_candidates=50))
        assert len(passwords) > 0
        assert all(isinstance(p, str) for p in passwords)

    def test_stats_populated(self):
        profile = {"names": ["Test"], "keywords": ["key"]}
        engine = CogPIEEngine()
        engine.generate(profile, max_candidates=100)
        stats = engine.stats
        assert "total_time" in stats
        assert "output_count" in stats

    def test_policy_integration(self):
        profile = {
            "names": ["Ana"],
            "dates": ["2010"],
            "keywords": ["sol"],
        }
        policy = PasswordPolicy(min_length=8, min_char_classes=2)
        engine = CogPIEEngine()
        results = engine.generate(profile, policy=policy, max_candidates=200)
        for candidate, meta in results:
            assert len(candidate) >= 8
            assert meta["char_classes"] >= 2

"""
test_cogpie_training.py - Tests for CogPIE training pipeline.

Covers: pii_correlator, corpus_builder, real_benchmark, engine save/load.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from wlf_modules.cogpie.pii_correlator import (
    ALL_NAMES,
    NAMES_DE,
    NAMES_EN,
    NAMES_ES,
    NAMES_FR,
    NAMES_PT,
    CorpusStats,
    PIIMatch,
    correlate_corpus,
    correlate_password,
)
from wlf_modules.cogpie.engine import CogPIEEngine


class TestPIICorrelator:
    """Tests for pii_correlator module."""

    def test_name_detection_english(self):
        result = correlate_password("michael123")
        assert result.category in ("name_based", "hybrid")
        assert result.name_found == "michael"

    def test_name_detection_portuguese(self):
        result = correlate_password("fernanda2024")
        assert result.category in ("name_based", "hybrid")
        assert result.name_found == "fernanda"

    def test_name_detection_spanish(self):
        result = correlate_password("alejandro99")
        assert result.category in ("name_based", "hybrid")
        assert result.name_found == "alejandro"

    def test_name_detection_french(self):
        result = correlate_password("sebastien01")
        assert result.category in ("name_based", "hybrid")
        assert result.name_found == "sebastien"

    def test_name_detection_german(self):
        result = correlate_password("maximilian7")
        assert result.category in ("name_based", "hybrid")
        assert result.name_found == "maximilian"

    def test_date_detection_full_ddmmyyyy(self):
        result = correlate_password("pass15031990")
        assert result.date_found is not None
        assert result.date_type in ("full_date", "year_4")

    def test_date_detection_year(self):
        result = correlate_password("love2024ever")
        assert result.date_found is not None
        assert result.date_type == "year_4"

    def test_hybrid_name_date(self):
        result = correlate_password("maria1990")
        assert result.category == "hybrid"
        assert result.name_found is not None
        assert result.date_found is not None

    def test_sequential_detection(self):
        result = correlate_password("123456")
        assert result.category == "sequential"

    def test_qwerty_sequential(self):
        result = correlate_password("qwerty")
        assert result.category == "sequential"

    def test_random_like(self):
        result = correlate_password("xkj9!mQ")
        assert result.category == "random_like"

    def test_empty_password(self):
        result = correlate_password("")
        assert result.category == "random_like"

    def test_short_password(self):
        result = correlate_password("ab")
        assert result.category == "random_like"

    def test_name_databases_populated(self):
        assert len(NAMES_EN) > 100
        assert len(NAMES_PT) > 100
        assert len(NAMES_ES) > 100
        assert len(NAMES_FR) > 100
        assert len(NAMES_DE) > 100
        assert len(ALL_NAMES) > 500

    def test_cross_cultural_coverage(self):
        names_with_categories = [
            ("james", "en"), ("joao", "pt"), ("juan", "es"),
            ("pierre", "fr"), ("hans", "de"),
        ]
        for name, expected_lang in names_with_categories:
            result = correlate_password(f"{name}2024")
            assert result.name_found == name, f"Failed to detect {name}"

    def test_confidence_range(self):
        result = correlate_password("michael1990")
        assert 0.0 <= result.confidence <= 1.0

    def test_corpus_stats_in_memory(self):
        passwords = ["michael123", "123456", "maria1990", "xkj9mQ!!", "john2024"]
        stats = correlate_corpus(passwords=passwords)
        assert stats.total == 5
        assert isinstance(stats.as_dict(), dict)
        assert stats.as_dict()["total"] == 5

    def test_corpus_stats_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("michael123\n")
            f.write("maria1990\n")
            f.write("123456\n")
            f.write("randomXY7\n")
            tmppath = f.name

        try:
            stats = correlate_corpus(filepath=tmppath)
            assert stats.total == 4
            d = stats.as_dict()
            assert "pii_detectable_pct" in d
            assert d["pii_detectable_pct"] > 0
        finally:
            os.unlink(tmppath)


class TestEngineTrainFromCorpus:
    """Tests for engine.train_from_corpus and save/load."""

    @pytest.fixture
    def sample_corpus(self, tmp_path):
        corpus_file = tmp_path / "test_corpus.txt"
        passwords = [
            "password123", "michael1990", "maria2024", "john!doe99",
            "qwerty123", "iloveyou", "letmein", "admin2023",
            "dragon99", "master123", "abc12345", "welcome1",
            "monkey99", "shadow123", "sunshine1", "princess1",
        ]
        corpus_file.write_text("\n".join(passwords) + "\n")
        return str(corpus_file)

    def test_train_from_corpus(self, sample_corpus):
        engine = CogPIEEngine()
        count = engine.train_from_corpus(sample_corpus)
        assert count == 16

    def test_train_from_corpus_max_lines(self, sample_corpus):
        engine = CogPIEEngine()
        count = engine.train_from_corpus(sample_corpus, max_lines=5)
        assert count == 5

    def test_save_and_load_model(self, sample_corpus, tmp_path):
        engine = CogPIEEngine(alpha=0.5, beta=0.1, markov_order=2)
        engine.train_from_corpus(sample_corpus)

        model_path = str(tmp_path / "test_model.pkl")
        engine.save_model(model_path)
        assert os.path.isfile(model_path)

        loaded = CogPIEEngine.load_model(model_path)
        assert loaded.ranker.trained_count == 16

        profile = {
            "names": ["michael"],
            "dates": ["1990"],
            "keywords": [],
            "pets": [],
            "companies": [],
            "phones": [],
            "emails": [],
            "old_passwords": [],
            "numbers": ["1990"],
        }
        results = loaded.generate(profile, max_candidates=100)
        assert len(results) > 0

    def test_generate_after_training(self, sample_corpus):
        engine = CogPIEEngine()
        engine.train_from_corpus(sample_corpus)

        profile = {
            "names": ["maria"],
            "dates": ["2024"],
            "keywords": ["love"],
            "pets": [],
            "companies": [],
            "phones": [],
            "emails": [],
            "old_passwords": [],
            "numbers": ["2024"],
        }
        results = engine.generate(profile, max_candidates=1000)
        assert len(results) > 0
        candidates = [c for c, _ in results]
        assert all(isinstance(c, str) for c in candidates)

    def test_trained_model_scores_higher(self, sample_corpus):
        engine = CogPIEEngine()
        engine.train_from_corpus(sample_corpus)

        profile = {
            "names": ["michael"],
            "dates": ["1990"],
            "keywords": [],
            "pets": [],
            "companies": [],
            "phones": [],
            "emails": [],
            "old_passwords": [],
            "numbers": ["1990"],
        }
        results = engine.generate(profile, max_candidates=500)
        candidates = [c for c, _ in results]
        assert "michael1990" in candidates or "Michael1990" in candidates


class TestCorpusBuilder:
    """Tests for corpus builder functions (imported)."""

    def test_build_small_corpus(self, tmp_path):
        input_file = tmp_path / "input.txt"
        input_file.write_text(
            "michael123\nmaria1990\n123456\nab\n"
            "john2024\nmichael123\nxkj9mQ!!\n"
        )

        sys_path_backup = list(__import__("sys").path)
        try:
            forge_root = str(Path(__file__).resolve().parent.parent)
            if forge_root not in __import__("sys").path:
                __import__("sys").path.insert(0, forge_root)

            from tools.cogpie_corpus_builder import build_processed_corpus

            sources = [("test", str(input_file))]
            summary = build_processed_corpus(
                sources=sources,
                output_dir=str(tmp_path / "output"),
                max_lines=0,
                min_length=4,
                max_length=64,
            )
            assert summary["total_kept"] > 0
            assert summary["total_kept"] <= 7
            assert summary["skipped_duplicate"] >= 1
            assert os.path.isfile(tmp_path / "output" / "processed_corpus.txt")
            assert os.path.isfile(tmp_path / "output" / "corpus_stats.json")
            assert os.path.isfile(tmp_path / "output" / "pii_patterns.json")
        finally:
            __import__("sys").path[:] = sys_path_backup


class TestBenchmarkHelpers:
    """Tests for benchmark helper functions."""

    def test_extract_synthetic_profile(self):
        from tools.cogpie_real_benchmark import _extract_synthetic_profile

        profile = _extract_synthetic_profile("michael1990")
        assert profile is not None
        assert "michael" in profile["names"]
        assert any("1990" in d for d in profile["dates"])

    def test_extract_no_pii(self):
        from tools.cogpie_real_benchmark import _extract_synthetic_profile

        profile = _extract_synthetic_profile("xkj9mQ!!")
        assert profile is None

    def test_split_corpus(self):
        from tools.cogpie_real_benchmark import split_corpus

        passwords = [
            "michael123", "maria1990", "john2024",
            "xkj9mQ!!", "randompass", "123456",
            "fernanda2024", "carlos99", "test1234",
        ]
        train, test = split_corpus(passwords, test_ratio=0.3, seed=42)
        assert len(train) + len(test) <= len(passwords)
        assert len(test) >= 1

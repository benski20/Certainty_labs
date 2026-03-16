"""Tests for the data generation pipeline."""

import json
import pytest
from certainty.data.sampler import MockSampler, FileSampler
from certainty.data.labeler import SymbolicLabeler
from certainty.data.negatives import NegativeSynthesizer


def _portfolio_energy(parsed):
    """Simple energy: 0 if weights sum to ~1, else 10 (replaces compiler-based fn)."""
    if not isinstance(parsed, dict) or "weights" not in parsed:
        return 100.0
    try:
        total = sum(float(v) for v in parsed["weights"].values())
        return 0.0 if abs(total - 1.0) < 0.01 else 10.0 * abs(total - 1.0)
    except (TypeError, ValueError):
        return 10.0


@pytest.fixture
def energy_fn():
    return _portfolio_energy


class TestMockSampler:
    def test_sample_portfolio(self):
        sampler = MockSampler(domain="portfolio")
        results = sampler.sample("generate portfolio", n=20)
        assert len(results) == 20
        for r in results:
            parsed = json.loads(r)
            assert "weights" in parsed

    def test_sample_dosage(self):
        sampler = MockSampler(domain="dosage")
        results = sampler.sample("generate dosage", n=10)
        assert len(results) == 10
        for r in results:
            parsed = json.loads(r)
            assert "patient_age_years" in parsed

    def test_sample_generic(self):
        sampler = MockSampler(domain="generic")
        results = sampler.sample("anything", n=5)
        assert len(results) == 5


class TestSymbolicLabeler:
    def test_labels_valid_as_positive(self, energy_fn):
        labeler = SymbolicLabeler(energy_fn)
        valid = json.dumps({"weights": {"A": 0.33, "B": 0.33, "C": 0.34}})
        result = labeler.label_one(valid)
        assert result["label"] == "positive"
        assert result["energy"] < 0.01

    def test_labels_invalid_as_negative(self, energy_fn):
        labeler = SymbolicLabeler(energy_fn)
        invalid = json.dumps({"weights": {"A": 0.8, "B": 0.8}})
        result = labeler.label_one(invalid)
        assert result["label"] == "negative"
        assert result["energy"] > 0.5

    def test_labels_bad_json_as_negative(self, energy_fn):
        labeler = SymbolicLabeler(energy_fn)
        result = labeler.label_one("not json at all")
        assert result["label"] == "negative"
        assert result["parse_error"] is True

    def test_label_all(self, energy_fn):
        labeler = SymbolicLabeler(energy_fn)
        outputs = [
            json.dumps({"weights": {"A": 0.33, "B": 0.33, "C": 0.34}}),
            json.dumps({"weights": {"A": 0.9, "B": 0.9}}),
        ]
        results = labeler.label_all(outputs)
        assert len(results) == 2
        assert results[0]["label"] == "positive"
        assert results[1]["label"] == "negative"


class TestNegativeSynthesizer:
    def test_synthesize_produces_negatives(self, energy_fn):
        synth = NegativeSynthesizer(energy_fn)
        positives = [
            {
                "text": json.dumps({"weights": {"A": 0.33, "B": 0.33, "C": 0.34}}),
                "parsed": {"weights": {"A": 0.33, "B": 0.33, "C": 0.34}},
                "energy": 0.0,
                "label": "positive",
            }
        ]
        negatives = synth.synthesize(positives, n_needed=10)
        assert len(negatives) > 0
        for neg in negatives:
            assert neg["label"] == "negative"

    def test_corrupt_json_produces_parse_errors(self, energy_fn):
        synth = NegativeSynthesizer(energy_fn)
        example = {"text": '{"weights": {"A": 0.5, "B": 0.5}}'}
        result = synth.corrupt_json(example)
        assert result is not None
        assert result["parse_error"] is True

"""Tests for the ConstraintReranker."""

import os
import tempfile
import pytest
import torch
from certainty.models.ebm_model import TransEBM
from certainty.models.dataset import setup_tokenizer
from certainty.inference.reranker import ConstraintReranker


@pytest.fixture
def trained_model_path():
    """Create a small TransEBM and save it for testing."""
    tok, pad_id, cls_id = setup_tokenizer("gpt2", 512)
    model = TransEBM(vocab_size=len(tok), d_model=64, n_heads=2, n_layers=1)

    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        path = f.name
    model.save(path)
    yield path
    os.unlink(path)


class TestConstraintReranker:
    def test_rerank_returns_best(self, trained_model_path):
        reranker = ConstraintReranker(
            model_path=trained_model_path,
            device="cpu",
            max_length=512,
        )
        candidates = [
            '{"weights": {"AAPL": 0.5, "GOOG": 0.5}}',
            '{"weights": {"AAPL": 0.33, "GOOG": 0.33, "MSFT": 0.34}}',
            '{"weights": {"AAPL": 1.0}}',
        ]
        best, best_idx, energies = reranker.rerank(candidates)
        assert best in candidates
        assert 0 <= best_idx < len(candidates)
        assert len(energies) == len(candidates)

    def test_score_all(self, trained_model_path):
        reranker = ConstraintReranker(
            model_path=trained_model_path,
            device="cpu",
            max_length=512,
        )
        texts = ["hello world", "another text", "third one"]
        energies = reranker.score_all(texts)
        assert len(energies) == 3
        assert all(isinstance(e, float) for e in energies)

    def test_rerank_with_prompt(self, trained_model_path):
        reranker = ConstraintReranker(
            model_path=trained_model_path,
            device="cpu",
            max_length=512,
        )
        candidates = ["output A", "output B"]
        best, best_idx, energies = reranker.rerank(candidates, prompt="test prompt")
        assert best in candidates
        assert len(energies) == 2

    def test_single_candidate(self, trained_model_path):
        reranker = ConstraintReranker(
            model_path=trained_model_path,
            device="cpu",
            max_length=512,
        )
        candidates = ["only one"]
        best, best_idx, energies = reranker.rerank(candidates)
        assert best == "only one"
        assert best_idx == 0

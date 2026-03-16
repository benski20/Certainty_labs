"""Tests for the TransEBM model and Bradley-Terry loss."""

import os
import tempfile
import pytest
import torch
from certainty.models.ebm_model import TransEBM
from certainty.models.loss import bradley_terry_loss


class TestTransEBM:
    def test_forward_shape(self):
        model = TransEBM(vocab_size=1000, d_model=128, n_heads=2, n_layers=1)
        ids = torch.randint(0, 1000, (4, 32))
        mask = torch.ones(4, 32, dtype=torch.long)
        energies = model(ids, mask)
        assert energies.shape == (4,)

    def test_cls_pooling(self):
        model = TransEBM(vocab_size=1000, d_model=64, n_heads=2, n_layers=1)
        ids = torch.randint(0, 1000, (2, 16))
        mask = torch.ones(2, 16, dtype=torch.long)
        e1 = model(ids, mask)
        assert e1.shape == (2,)

    def test_padding_mask(self):
        model = TransEBM(vocab_size=1000, d_model=64, n_heads=2, n_layers=1)
        ids = torch.randint(0, 1000, (2, 20))
        mask_full = torch.ones(2, 20, dtype=torch.long)
        mask_partial = torch.ones(2, 20, dtype=torch.long)
        mask_partial[:, 10:] = 0
        e_full = model(ids, mask_full)
        e_partial = model(ids, mask_partial)
        assert e_full.shape == e_partial.shape == (2,)
        assert not torch.allclose(e_full, e_partial)

    def test_save_load_roundtrip(self):
        model = TransEBM(vocab_size=500, d_model=64, n_heads=2, n_layers=1)
        model.eval()
        ids = torch.randint(0, 500, (2, 10))
        mask = torch.ones(2, 10, dtype=torch.long)
        with torch.no_grad():
            e_before = model(ids, mask)

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            path = f.name
        try:
            model.save(path)
            loaded = TransEBM.load(path)
            with torch.no_grad():
                e_after = loaded(ids, mask)
            assert torch.allclose(e_before, e_after, atol=1e-6)
        finally:
            os.unlink(path)

    def test_resize_embeddings(self):
        model = TransEBM(vocab_size=500, d_model=64, n_heads=2, n_layers=1)
        assert model.emb.num_embeddings == 500
        model.resize_token_embeddings(600)
        assert model.emb.num_embeddings == 600
        ids = torch.randint(0, 600, (2, 10))
        mask = torch.ones(2, 10, dtype=torch.long)
        e = model(ids, mask)
        assert e.shape == (2,)


class TestBradleyTerryLoss:
    def test_basic_loss(self):
        energies = torch.tensor([0.5, 1.0, 2.0, 3.0])
        labels = torch.tensor([1.0, 1.0, 0.0, 0.0])
        loss = bradley_terry_loss(energies, labels)
        assert loss is not None
        assert loss.item() >= 0

    def test_perfect_separation(self):
        energies = torch.tensor([-5.0, -4.0, 5.0, 6.0])
        labels = torch.tensor([1.0, 1.0, 0.0, 0.0])
        loss = bradley_terry_loss(energies, labels)
        assert loss is not None
        assert loss.item() < 0.01

    def test_no_positives_returns_none(self):
        energies = torch.tensor([1.0, 2.0])
        labels = torch.tensor([0.0, 0.0])
        assert bradley_terry_loss(energies, labels) is None

    def test_no_negatives_returns_none(self):
        energies = torch.tensor([1.0, 2.0])
        labels = torch.tensor([1.0, 1.0])
        assert bradley_terry_loss(energies, labels) is None

    def test_gradients_flow(self):
        energies = torch.tensor([0.5, 2.0], requires_grad=True)
        labels = torch.tensor([1.0, 0.0])
        loss = bradley_terry_loss(energies, labels)
        loss.backward()
        assert energies.grad is not None
        assert not torch.all(energies.grad == 0)

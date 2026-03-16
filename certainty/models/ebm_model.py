"""
TransEBM -- Lightweight Transformer-based Energy-Based Model.

Architecture matches the real EORM implementation (Jiang et al., 2025):
https://github.com/ericjiang18/EnergyORM/blob/main/ebm_model.py

Key design choices from the paper:
  - From-scratch Transformer (no pretrained weights, only tokenizer reused)
  - Pre-LN (norm_first=True) for stable training
  - CLS token pooling (position 0) instead of mean pooling
  - Energy head: LayerNorm -> Linear -> GELU -> Linear
  - Embedding scaling by sqrt(d_model) (Vaswani et al.)
  - No explicit positional encoding
"""

from __future__ import annotations

import torch
import torch.nn as nn
from pathlib import Path
from typing import Optional


class TransEBM(nn.Module):
    """
    Lightweight Transformer EBM for scoring candidate outputs.

    Lower energy = better (more constraint-satisfying).
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 768,
        n_heads: int = 4,
        n_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.d_model = d_model
        self.emb = nn.Embedding(vocab_size, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model,
            n_heads,
            dim_feedforward=4 * d_model,
            activation="gelu",
            dropout=dropout,
            batch_first=True,
            norm_first=True,
        )
        self.enc = nn.TransformerEncoder(layer, n_layers)
        self.head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, 1),
        )

    def forward(self, ids: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """
        ids  : (B, L) token ids
        mask : (B, L) 1 = real token, 0 = pad
        Returns energies : (B,) -- lower = better
        """
        x = self.emb(ids) * (self.d_model**0.5)
        padding_mask = mask == 0
        x = self.enc(x, src_key_padding_mask=padding_mask)
        cls_repr = x[:, 0]
        energy = self.head(cls_repr).squeeze(-1)
        return energy

    def resize_token_embeddings(self, new_num_tokens: int) -> None:
        old_emb = self.emb
        if old_emb.num_embeddings == new_num_tokens:
            return
        new_emb = nn.Embedding(new_num_tokens, self.d_model)
        new_emb.weight.data.normal_(mean=0.0, std=0.02)
        n_copy = min(old_emb.num_embeddings, new_num_tokens)
        new_emb.weight.data[:n_copy, :] = old_emb.weight.data[:n_copy, :]
        self.emb = new_emb

    def save(self, path: str | Path, **extra_meta) -> None:
        meta = {
            "state_dict": self.state_dict(),
            "d_model": self.d_model,
            "vocab_size": self.emb.num_embeddings,
            "n_layers": len(self.enc.layers),
            "n_heads": self.enc.layers[0].self_attn.num_heads,
        }
        meta.update(extra_meta)
        torch.save(meta, path)

    @classmethod
    def load(
        cls,
        path: str | Path,
        device: str = "cpu",
        strict: bool = True,
        **kwargs,
    ) -> "TransEBM":
        """
        Load from either metadata format (TransEBM.save) or raw state_dict (EnergyORM).

        For raw state_dicts, pass vocab_size/d_model/n_heads/n_layers as kwargs,
        or they will be inferred from the weights where possible.
        """
        ckpt = torch.load(path, map_location=device, weights_only=False)

        if "state_dict" in ckpt:
            model = cls(
                vocab_size=ckpt["vocab_size"],
                d_model=ckpt["d_model"],
                n_heads=ckpt.get("n_heads", 4),
                n_layers=ckpt.get("n_layers", 2),
            )
            model.load_state_dict(ckpt["state_dict"], strict=strict)
        else:
            vocab_size = kwargs.get("vocab_size") or ckpt["emb.weight"].shape[0]
            d_model = kwargs.get("d_model") or ckpt["emb.weight"].shape[1]
            n_heads = kwargs.get("n_heads", 4)
            n_layers = kwargs.get("n_layers") or sum(
                1
                for k in ckpt
                if k.startswith("enc.layers.") and k.endswith(".norm1.weight")
            )
            model = cls(
                vocab_size=vocab_size,
                d_model=d_model,
                n_heads=n_heads,
                n_layers=max(n_layers, 1),
            )
            model.load_state_dict(ckpt, strict=strict)

        return model.to(device).eval()

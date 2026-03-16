"""
Constraint reranker using TransEBM.

Scores N candidate outputs and returns the one with lowest energy.
Works with any LLM API (GPT-4o, Claude, Llama, etc.) -- the reranker
only needs the text outputs, not the model internals.
"""

from __future__ import annotations

import torch
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

from ..models.ebm_model import TransEBM
from ..models.utils import setup_tokenizer


class ConstraintReranker:
    """Score candidate texts with a trained TransEBM and pick the best one."""

    def __init__(
        self,
        model_path: str | Path,
        tokenizer_path: Optional[str | Path] = None,
        device: str = "cpu",
        max_length: int = 2048,
    ):
        self.device = torch.device(device)
        self.max_length = max_length

        self.model = TransEBM.load(model_path, device=device)
        self.model.eval()

        if tokenizer_path and Path(tokenizer_path).exists():
            from transformers import AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path))
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.pad_id = self.tokenizer.pad_token_id

            cls_id = None
            if hasattr(self.tokenizer, "bos_token_id") and self.tokenizer.bos_token_id is not None:
                cls_id = self.tokenizer.bos_token_id
            elif hasattr(self.tokenizer, "cls_token_id") and self.tokenizer.cls_token_id is not None:
                cls_id = self.tokenizer.cls_token_id
            elif self.tokenizer.eos_token_id is not None:
                cls_id = self.tokenizer.eos_token_id
            self.cls_id = cls_id
        else:
            self.tokenizer, self.pad_id, self.cls_id = setup_tokenizer(
                "gpt2", max_length
            )

    def rerank(
        self,
        candidates: List[str],
        prompt: str = "",
    ) -> Tuple[str, int, List[float]]:
        """Score all candidates, return (best_text, best_index, all_energies)."""
        energies = self.score_all(candidates, prompt)
        best_idx = int(np.argmin(energies))
        return candidates[best_idx], best_idx, energies

    def score_all(self, texts: List[str], prompt: str = "") -> List[float]:
        """Return energy scores for each candidate text."""
        energies: List[float] = []
        sep = self.tokenizer.eos_token or "\n"
        for text in texts:
            combined = f"{prompt}{sep}{text}" if prompt else text
            ids = self.tokenizer.encode(
                combined,
                add_special_tokens=False,
                truncation=True,
                max_length=self.max_length - 1,
            )
            ids = [self.cls_id] + ids
            ids_t = torch.tensor([ids], dtype=torch.long, device=self.device)
            mask_t = torch.ones_like(ids_t)
            with torch.no_grad():
                energy = self.model(ids_t, mask_t).item()
            energies.append(energy)
        return energies

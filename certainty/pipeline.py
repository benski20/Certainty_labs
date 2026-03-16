"""
CertaintyPipeline -- High-level orchestrator.

Modes of operation:
  1. Bring your own data: load_data(path) or load_data_records(records) -> train() -> rerank(candidates)
  2. Default data: train() -> rerank(candidates)  (uses built-in GSM8K-Llama dataset)
  3. Inference only: load_model(path) -> rerank(candidates)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .models.trainer import EBMTrainer, TrainingConfig
from .inference.reranker import ConstraintReranker


class CertaintyPipeline:
    """
    End-to-end pipeline. Entry points:
      - load_data(path) or load_data_records(records) -> train() -> rerank()
      - train() with no data loads built-in GSM8K dataset
      - load_model(path) -> rerank()
    """

    def __init__(self, work_dir: str = "./certainty_workspace"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.reranker: Optional[ConstraintReranker] = None
        self._model_path: Optional[str] = None
        self._tokenizer_path: Optional[str] = None
        self._data_path: Optional[str] = None
        self._data_records: Optional[List[Dict[str, Any]]] = None

    def load_data(self, path: str) -> "CertaintyPipeline":
        """Load pre-existing EORM-format JSONL data."""
        self._data_path = path
        self._data_records = None
        print(f"Loaded data from {path}")
        return self

    def load_data_records(self, records: List[Dict[str, Any]]) -> "CertaintyPipeline":
        """Load in-memory EORM-format records [{question, label, gen_text}, ...]."""
        self._data_records = records
        self._data_path = None
        print(f"Loaded {len(records)} in-memory records")
        return self

    def train(
        self,
        config: Optional[TrainingConfig] = None,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Train TransEBM on the prepared data.
        If no data was loaded, falls back to the default EORM GSM8K-Llama demo dataset.
        """
        config = config or TrainingConfig()
        output_dir = str(self.work_dir / "model")
        trainer = EBMTrainer(config)
        metrics = trainer.train(
            data_path=self._data_path,
            data_records=self._data_records,
            output_dir=output_dir,
            progress_callback=progress_callback,
        )
        self._model_path = metrics["model_path"]
        self._tokenizer_path = metrics["tokenizer_path"]
        self._init_reranker()
        return metrics

    def load_model(
        self, model_path: str, tokenizer_path: Optional[str] = None
    ) -> "CertaintyPipeline":
        """Load a pre-trained model (skip training)."""
        self._model_path = model_path
        self._tokenizer_path = tokenizer_path
        self._init_reranker()
        return self

    def rerank(
        self, candidates: List[str], prompt: str = ""
    ) -> Tuple[str, int, List[float]]:
        """Rerank candidates, return (best_text, best_index, all_energies)."""
        assert self.reranker is not None, "Train or load a model first"
        return self.reranker.rerank(candidates, prompt)

    def score(self, candidates: List[str], prompt: str = "") -> List[float]:
        """Score candidates without selecting the best."""
        assert self.reranker is not None, "Train or load a model first"
        return self.reranker.score_all(candidates, prompt)

    def _init_reranker(self) -> None:
        if self._model_path:
            self.reranker = ConstraintReranker(
                model_path=self._model_path,
                tokenizer_path=self._tokenizer_path,
            )

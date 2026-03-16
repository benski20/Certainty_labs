"""Typed response objects for the Certainty Labs API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# Optional: pass to train() for clearer training config
@dataclass
class TrainingParams:
    """Training hyperparameters. Omit fields to use API defaults."""

    tokenizer_name: Optional[str] = None  # HuggingFace ID or alias, e.g. qwen2.5-7b, llama-3.1-8b
    epochs: Optional[int] = None
    batch_size: Optional[int] = None
    d_model: Optional[int] = None
    n_heads: Optional[int] = None
    n_layers: Optional[int] = None
    lr: Optional[float] = None
    max_length: Optional[int] = None
    validate_every: Optional[int] = None
    val_holdout: Optional[float] = None


@dataclass(frozen=True)
class HealthResponse:
    status: str
    version: str


@dataclass(frozen=True)
class TrainResponse:
    model_path: str
    best_val_acc: float
    epochs_trained: int
    elapsed_seconds: float


@dataclass(frozen=True)
class RerankResponse:
    best_candidate: str
    best_index: int
    all_energies: List[float]


@dataclass(frozen=True)
class ScoreResponse:
    """Energy scores for one or more outputs (verifiable/interpretable AI: logging, audit, confidence)."""
    energies: List[float]  # Lower = higher confidence / more constraint-satisfying


@dataclass(frozen=True)
class PipelineResponse:
    train: TrainResponse
    rerank: Optional[RerankResponse]

    @classmethod
    def _from_dict(cls, data: dict) -> "PipelineResponse":
        rerank = None
        if data.get("rerank"):
            r = data["rerank"]
            rerank = RerankResponse(
                best_candidate=r["best_candidate"],
                best_index=r["best_index"],
                all_energies=r["all_energies"],
            )
        return cls(
            train=TrainResponse(
                model_path=data["train"]["model_path"],
                best_val_acc=data["train"]["best_val_acc"],
                epochs_trained=data["train"]["epochs_trained"],
                elapsed_seconds=data["train"]["elapsed_seconds"],
            ),
            rerank=rerank,
        )

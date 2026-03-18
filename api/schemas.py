"""Pydantic request/response models for the Certainty Labs API."""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


# ── Health ───────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    version: str


# ── API Keys ─────────────────────────────────────────────────────────


class CreateKeyRequest(BaseModel):
    name: str = "default"


class CreateKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    prefix: str
    created_at: float


class KeyInfo(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: float


class ListKeysResponse(BaseModel):
    keys: List[KeyInfo]
    auth_enabled: bool


# ── Train ────────────────────────────────────────────────────────────


class TrainRequest(BaseModel):
    data_path: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    tokenizer_name: Optional[str] = None  # HuggingFace ID or alias: Qwen/*, meta-llama/*, or gpt2
    gpu: Optional[str] = None  # GPU type at runtime: T4, A10, L4, A100, etc. Default from deployment.
    epochs: int = 20
    batch_size: int = 1
    d_model: int = 768
    n_heads: int = 4
    n_layers: int = 2
    lr: float = 5e-5
    max_length: int = 2048
    validate_every: int = 1
    val_holdout: float = 0.2


class TrainResponse(BaseModel):
    model_path: str
    best_val_acc: float
    epochs_trained: int
    elapsed_seconds: float


# ── Rerank ───────────────────────────────────────────────────────────


class RerankRequest(BaseModel):
    candidates: List[str] = []
    prompt: str = ""
    model_path: str = "./certainty_workspace/model/ebm_certainty_model.pt"
    tokenizer_path: Optional[str] = None
    # Optional: use your own LLM to generate candidates, then rerank. If candidates is empty and these are set, the API generates n_candidates with your model first.
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    openai_base_url: Optional[str] = None
    # Optional: use Hugging Face Inference API for Qwen/Llama. If candidates empty and hf_model + hf_token set, generates n_candidates via HF.
    hf_model: Optional[str] = None  # e.g. Qwen/Qwen2.5-7B-Instruct, meta-llama/Llama-3.1-8B-Instruct
    hf_token: Optional[str] = None
    n_candidates: int = 5


class RerankResponse(BaseModel):
    best_candidate: str
    best_index: int
    all_energies: List[float]


# ── Score (verifiable / interpretable AI: energy for logging, audit, confidence) ─


class ScoreRequest(BaseModel):
    """Get EBM energy scores for one or more outputs. No reranking — use for logging, confidence tracking, audit."""
    texts: List[str]  # One or more outputs to score (order preserved in response)
    prompt: str = ""
    model_path: str = "./certainty_workspace/model/ebm_certainty_model.pt"
    tokenizer_path: Optional[str] = None


class ScoreResponse(BaseModel):
    energies: List[float]  # One energy per text; lower = more constraint-satisfying / higher confidence


# ── Pipeline ─────────────────────────────────────────────────────────


class PipelineRequest(BaseModel):
    data_path: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    tokenizer_name: Optional[str] = None  # HuggingFace ID or alias for Qwen/Llama compatibility
    gpu: Optional[str] = None  # GPU type at runtime: T4, A10, L4, A100, etc.
    epochs: int = 10
    batch_size: int = 1
    d_model: int = 768
    n_heads: int = 4
    n_layers: int = 2
    lr: float = 5e-5
    max_length: int = 2048
    validate_every: int = 1
    val_holdout: float = 0.2
    candidates: Optional[List[str]] = None


class PipelineResponse(BaseModel):
    train: TrainResponse
    rerank: Optional[RerankResponse] = None

"""Synchronous client for the Certainty Labs API."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from certaintylabs.exceptions import APIError, ConnectionError, TimeoutError

logger = logging.getLogger("certaintylabs")
from certaintylabs.types import (
    HealthResponse,
    PipelineResponse,
    RerankResponse,
    ScoreResponse,
    TrainResponse,
    TrainingParams,
)

# Fixed API base URL — users do not configure this.
_BASE_URL = "https://sandboxtesting101--certainty-labs-api.modal.run"
_DEFAULT_TIMEOUT = 300.0

_ENV_API_KEY = "CERTAINTY_API_KEY"


class Certainty:
    """Synchronous Python client for the Certainty Labs API.

    Set your API key via environment variable::

        export CERTAINTY_API_KEY="ck_..."

    Then in code::

        from certaintylabs import Certainty

        client = Certainty()  # reads api_key from env
        result = client.train(epochs=10)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        self.base_url = _BASE_URL.rstrip("/")
        self.api_key = api_key if api_key is not None else os.environ.get(_ENV_API_KEY)
        self.timeout = timeout

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        logger.info("Certainty client initialized base_url=%s auth=%s", self.base_url, "yes" if self.api_key else "no")

    def _parse_json(self, resp: httpx.Response) -> dict:
        """Parse response as JSON; raise clear error if body is empty or invalid."""
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            preview = (resp.text[:200] + "…") if len(resp.text or "") > 200 else (resp.text or "(empty)")
            logger.error("JSONDecodeError status=%d body=%s", resp.status_code, preview)
            raise APIError(
                status_code=resp.status_code,
                detail=f"Invalid JSON response: {e}. Body: {preview}. "
                "The server may have timed out or returned an error page.",
            ) from e
        return data

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        url = f"{self.base_url}{path}"
        logger.debug("Request %s %s", method, url)
        start = time.monotonic()
        try:
            resp = self._client.request(method, path, **kwargs)
        except httpx.ConnectError as e:
            logger.warning("ConnectionError %s %s: %s", method, path, e)
            raise ConnectionError(self.base_url, e) from e
        except httpx.TimeoutException as e:
            logger.warning("Timeout %s %s after %.1fs", method, path, time.monotonic() - start)
            raise TimeoutError(self.timeout, path) from e

        elapsed = time.monotonic() - start
        logger.debug("Response %s %s -> %d in %.2fs", method, path, resp.status_code, elapsed)

        if resp.status_code >= 400:
            logger.warning("API error %s %s -> %d: %s", method, path, resp.status_code, (resp.text or "")[:200])
            body = {}
            if resp.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = resp.json()
                except json.JSONDecodeError:
                    pass
            raise APIError(
                status_code=resp.status_code,
                detail=body.get("detail", resp.text or "(empty response)"),
                error_type=body.get("error_type"),
            )
        data = self._parse_json(resp)
        logger.debug("Parsed JSON %s %s: %s", method, path, str(data)[:300] + "…" if len(str(data)) > 300 else str(data))
        return data

    # ── Endpoints ─────────────────────────────────────────────────────

    def health(self) -> HealthResponse:
        """Check API health and version."""
        logger.debug("health()")
        data = self._request("GET", "/health")
        return HealthResponse(status=data["status"], version=data["version"])

    def train(
        self,
        *,
        data_path: Optional[str] = None,
        data: Optional[List[Dict[str, Any]]] = None,
        tokenizer_name: Optional[str] = None,
        epochs: int = 20,
        batch_size: int = 1,
        d_model: int = 768,
        n_heads: int = 4,
        n_layers: int = 2,
        lr: float = 5e-5,
        max_length: int = 2048,
        validate_every: int = 1,
        val_holdout: float = 0.2,
        training_params: Optional[TrainingParams] = None,
    ) -> TrainResponse:
        """Train a TransEBM energy model.

        Data source (one of):
          - ``data``: in-memory list of {question, label, gen_text} dicts
          - ``data_path``: server path to EORM JSONL (or use ``train_from_file`` for local path)
        If neither is given, the server uses its built-in GSM8K dataset.

        Use ``tokenizer_name`` for Qwen/Llama compatibility (e.g. ``qwen2.5-7b``, ``llama-3.1-8b`` or full HF ID).
        Use ``training_params`` to pass a TrainingParams object; explicit kwargs override.
        """
        payload: Dict[str, Any] = {
            "epochs": epochs,
            "batch_size": batch_size,
            "d_model": d_model,
            "n_heads": n_heads,
            "n_layers": n_layers,
            "lr": lr,
            "max_length": max_length,
            "validate_every": validate_every,
            "val_holdout": val_holdout,
        }
        if tokenizer_name is not None:
            payload["tokenizer_name"] = tokenizer_name
        if training_params:
            for k, v in vars(training_params).items():
                if v is not None:
                    payload[k] = v
        if data_path is not None:
            payload["data_path"] = data_path
        if data is not None:
            payload["data"] = data

        logger.info("train(epochs=%d, data=%s)", epochs, "provided" if (data is not None or data_path is not None) else "built-in")
        data_resp = self._request("POST", "/train", json=payload)
        return TrainResponse(
            model_path=data_resp["model_path"],
            best_val_acc=data_resp["best_val_acc"],
            epochs_trained=data_resp["epochs_trained"],
            elapsed_seconds=data_resp["elapsed_seconds"],
        )

    def train_with_data(
        self,
        samples: List[Dict[str, Any]],
        *,
        tokenizer_name: Optional[str] = None,
        epochs: int = 20,
        batch_size: int = 1,
        d_model: int = 768,
        n_heads: int = 4,
        n_layers: int = 2,
        lr: float = 5e-5,
        max_length: int = 2048,
        validate_every: int = 1,
        val_holdout: float = 0.2,
        training_params: Optional[TrainingParams] = None,
    ) -> TrainResponse:
        """Train on in-memory data. Each item in ``samples`` should have keys: question, label, gen_text."""
        return self.train(
            data=samples,
            tokenizer_name=tokenizer_name,
            epochs=epochs,
            batch_size=batch_size,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            lr=lr,
            max_length=max_length,
            validate_every=validate_every,
            val_holdout=val_holdout,
            training_params=training_params,
        )

    def train_from_file(
        self,
        path: str,
        *,
        tokenizer_name: Optional[str] = None,
        epochs: int = 20,
        batch_size: int = 1,
        d_model: int = 768,
        n_heads: int = 4,
        n_layers: int = 2,
        lr: float = 5e-5,
        max_length: int = 2048,
        validate_every: int = 1,
        val_holdout: float = 0.2,
        training_params: Optional[TrainingParams] = None,
    ) -> TrainResponse:
        """Train on a local EORM JSONL file. Reads the file and sends records to the API."""
        logger.info("train_from_file(path=%s)", path)
        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return self.train_with_data(
            records,
            tokenizer_name=tokenizer_name,
            epochs=epochs,
            batch_size=batch_size,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            lr=lr,
            max_length=max_length,
            validate_every=validate_every,
            val_holdout=val_holdout,
            training_params=training_params,
        )

    def rerank(
        self,
        candidates: Optional[List[str]] = None,
        prompt: str = "",
        model_path: str = "./certainty_workspace/model/ebm_certainty_model.pt",
        tokenizer_path: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
        openai_base_url: Optional[str] = None,
        hf_model: Optional[str] = None,
        hf_token: Optional[str] = None,
        n_candidates: int = 5,
    ) -> RerankResponse:
        """Rerank LLM candidate outputs using a trained TransEBM model.

        Pass pre-generated ``candidates``, or leave candidates empty and set either
        ``openai_api_key`` (and optionally ``openai_model``, ``openai_base_url``) or
        ``hf_model`` + ``hf_token`` (Hugging Face Inference for Qwen/Llama) so the API
        generates ``n_candidates``, then reranks them.
        """
        payload: Dict[str, Any] = {
            "candidates": candidates if candidates is not None else [],
            "prompt": prompt,
            "model_path": model_path,
        }
        if tokenizer_path is not None:
            payload["tokenizer_path"] = tokenizer_path
        if openai_api_key is not None:
            payload["openai_api_key"] = openai_api_key
        if openai_model is not None:
            payload["openai_model"] = openai_model
        if openai_base_url is not None:
            payload["openai_base_url"] = openai_base_url
        if hf_model is not None:
            payload["hf_model"] = hf_model
        if hf_token is not None:
            payload["hf_token"] = hf_token
        if (candidates is None or len(candidates) == 0) and (openai_api_key is not None or (hf_model and hf_token)):
            payload["n_candidates"] = n_candidates

        logger.debug("rerank(candidates=%d, prompt_len=%d)", len(candidates or []), len(prompt))
        data = self._request("POST", "/rerank", json=payload)
        return RerankResponse(
            best_candidate=data["best_candidate"],
            best_index=data["best_index"],
            all_energies=data["all_energies"],
        )

    def score(
        self,
        texts: List[str],
        prompt: str = "",
        model_path: str = "./certainty_workspace/model/ebm_certainty_model.pt",
        tokenizer_path: Optional[str] = None,
    ) -> ScoreResponse:
        """Get EBM energy scores for one or more outputs (no reranking).

        Use for verifiable/interpretable AI: log confidence, audit reliability, track scores over time.
        Lower energy = higher confidence / more constraint-satisfying.
        """
        payload: Dict[str, Any] = {
            "texts": texts,
            "prompt": prompt,
            "model_path": model_path,
        }
        if tokenizer_path is not None:
            payload["tokenizer_path"] = tokenizer_path
        logger.debug("score(texts=%d)", len(texts))
        data = self._request("POST", "/score", json=payload)
        return ScoreResponse(energies=data["energies"])

    def pipeline(
        self,
        *,
        data_path: Optional[str] = None,
        data: Optional[List[Dict[str, Any]]] = None,
        tokenizer_name: Optional[str] = None,
        epochs: int = 10,
        batch_size: int = 1,
        d_model: int = 768,
        n_heads: int = 4,
        n_layers: int = 2,
        lr: float = 5e-5,
        max_length: int = 2048,
        validate_every: int = 1,
        val_holdout: float = 0.2,
        candidates: Optional[List[str]] = None,
    ) -> PipelineResponse:
        """Run train (on your data or built-in) then optionally rerank candidates."""
        payload: Dict[str, Any] = {
            "epochs": epochs,
            "batch_size": batch_size,
            "d_model": d_model,
            "n_heads": n_heads,
            "n_layers": n_layers,
            "lr": lr,
            "max_length": max_length,
            "validate_every": validate_every,
            "val_holdout": val_holdout,
        }
        if tokenizer_name is not None:
            payload["tokenizer_name"] = tokenizer_name
        if data_path is not None:
            payload["data_path"] = data_path
        if data is not None:
            payload["data"] = data
        if candidates is not None:
            payload["candidates"] = candidates

        logger.info("pipeline(epochs=%d, candidates=%s)", epochs, len(candidates) if candidates else 0)
        data_resp = self._request("POST", "/pipeline", json=payload)
        return PipelineResponse._from_dict(data_resp)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "Certainty":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

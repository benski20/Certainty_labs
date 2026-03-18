"""Asynchronous client for the Certainty Labs API."""

from __future__ import annotations

import io
import json
import logging
import os
import time
import zipfile
from pathlib import Path
from urllib.parse import quote
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


class AsyncCertainty:
    """Asynchronous Python client for the Certainty Labs API.

    Set your API key via environment variable: CERTAINTY_API_KEY.
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

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )
        logger.info("AsyncCertainty client initialized base_url=%s auth=%s", self.base_url, "yes" if self.api_key else "no")

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

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        logger.debug("Request %s %s", method, f"{self.base_url}{path}")
        start = time.monotonic()
        try:
            resp = await self._client.request(method, path, **kwargs)
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

    async def download_model(
        self,
        model_path: str,
        local_dir: str = ".",
    ) -> str:
        """Download a trained model and tokenizer to a local directory.
        Extracts model.pt, tokenizer/, and metrics.json (if present) to local_dir.
        Returns the path to the extracted model.pt.
        """
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        headers: Dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/models/download?path={quote(model_path, safe='')}"
        resp = await self._client.get(url, headers=headers, timeout=self.timeout)

        if resp.status_code >= 400:
            body = {}
            if resp.headers.get("content-type", "").startswith("application/json"):
                try:
                    body = resp.json()
                except json.JSONDecodeError:
                    pass
            raise APIError(
                status_code=resp.status_code,
                detail=body.get("detail", resp.text or "(empty response)"),
            )

        with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
            zf.extractall(local_path)

        return str(local_path / "model.pt")

    # ── Endpoints ─────────────────────────────────────────────────────

    async def health(self) -> HealthResponse:
        """Check API health and version."""
        data = await self._request("GET", "/health")
        return HealthResponse(status=data["status"], version=data["version"])

    async def train(
        self,
        *,
        data_path: Optional[str] = None,
        data: Optional[List[Dict[str, Any]]] = None,
        tokenizer_name: Optional[str] = None,
        gpu: Optional[str] = None,
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
        save_to: Optional[str] = None,
    ) -> TrainResponse:
        """Train a TransEBM. Use ``data`` or ``data_path``, or neither for built-in dataset. Use ``tokenizer_name`` for Qwen/Llama (e.g. qwen2.5-7b, llama-3.1-8b). Use ``save_to`` to download the model after training."""
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
        if gpu is not None:
            payload["gpu"] = gpu
        if training_params:
            for k, v in vars(training_params).items():
                if v is not None:
                    payload[k] = v
        if data_path is not None:
            payload["data_path"] = data_path
        if data is not None:
            payload["data"] = data

        data_resp = await self._request("POST", "/train", json=payload)
        result = TrainResponse(
            model_path=data_resp["model_path"],
            best_val_acc=data_resp["best_val_acc"],
            epochs_trained=data_resp["epochs_trained"],
            elapsed_seconds=data_resp["elapsed_seconds"],
        )
        if save_to:
            await self.download_model(result.model_path, local_dir=save_to)
        return result

    async def train_with_data(
        self,
        samples: List[Dict[str, Any]],
        *,
        tokenizer_name: Optional[str] = None,
        gpu: Optional[str] = None,
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
        save_to: Optional[str] = None,
    ) -> TrainResponse:
        """Train on in-memory data. Each item in ``samples`` should have keys: question, label, gen_text."""
        return await self.train(
            data=samples,
            tokenizer_name=tokenizer_name,
            gpu=gpu,
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
            save_to=save_to,
        )

    async def train_from_file(
        self,
        path: str,
        *,
        tokenizer_name: Optional[str] = None,
        gpu: Optional[str] = None,
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
        save_to: Optional[str] = None,
    ) -> TrainResponse:
        """Train on a local EORM JSONL file. Reads the file and sends records to the API."""
        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return await self.train_with_data(
            records,
            tokenizer_name=tokenizer_name,
            gpu=gpu,
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
            save_to=save_to,
        )

    async def rerank(
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

        Pass pre-generated ``candidates``, or leave empty and set ``openai_api_key`` or
        ``hf_model`` + ``hf_token`` so the API generates ``n_candidates``, then reranks.
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

        data = await self._request("POST", "/rerank", json=payload)
        return RerankResponse(
            best_candidate=data["best_candidate"],
            best_index=data["best_index"],
            all_energies=data["all_energies"],
        )

    async def score(
        self,
        texts: List[str],
        prompt: str = "",
        model_path: str = "./certainty_workspace/model/ebm_certainty_model.pt",
        tokenizer_path: Optional[str] = None,
    ) -> ScoreResponse:
        """Get EBM energy scores for one or more outputs (verifiable/interpretable AI: logging, audit, confidence)."""
        payload: Dict[str, Any] = {
            "texts": texts,
            "prompt": prompt,
            "model_path": model_path,
        }
        if tokenizer_path is not None:
            payload["tokenizer_path"] = tokenizer_path
        data = await self._request("POST", "/score", json=payload)
        return ScoreResponse(energies=data["energies"])

    async def pipeline(
        self,
        *,
        data_path: Optional[str] = None,
        data: Optional[List[Dict[str, Any]]] = None,
        tokenizer_name: Optional[str] = None,
        gpu: Optional[str] = None,
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
        save_to: Optional[str] = None,
    ) -> PipelineResponse:
        """Run train (on your data or built-in) then optionally rerank candidates. Use ``save_to`` to download the model after training."""
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
        if gpu is not None:
            payload["gpu"] = gpu
        if data_path is not None:
            payload["data_path"] = data_path
        if data is not None:
            payload["data"] = data
        if candidates is not None:
            payload["candidates"] = candidates

        data_resp = await self._request("POST", "/pipeline", json=payload)
        result = PipelineResponse._from_dict(data_resp)
        if save_to:
            await self.download_model(result.train.model_path, local_dir=save_to)
        return result

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncCertainty":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

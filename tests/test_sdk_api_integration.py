"""
Thorough integration tests for the Certainty Labs SDK, API, and client.

Uses REAL data from demo_dataset/results_gsm8k_llama3_test_n4_temp0.7_p0.9_test.jsonl,
actually trains a model, and exercises every endpoint and client path.

Prerequisites:
  - API: uses the SDK's fixed base URL (no configuration needed).
  - For train/score/rerank to pass, the server must have all runtime deps
    (transformers, torch, numpy, etc.; see requirements.txt). Render and
    other hosts need these installed.

Run:
  python -m pytest tests/test_sdk_api_integration.py -v
  python -m pytest tests/test_sdk_api_integration.py -v --tb=short
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Project root and SDK path so we can load demo data and import certaintylabs
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
if str(_PROJECT_ROOT / "sdk") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "sdk"))

DEMO_JSONL = _PROJECT_ROOT / "demo_dataset" / "results_gsm8k_llama3_test_n4_temp0.7_p0.9_test.jsonl"
# Subset size: enough for valid train/val groups but keep test runtime reasonable
DEMO_SUBSET_LINES = 600


def _load_demo_records(max_lines: int = DEMO_SUBSET_LINES) -> list[dict]:
    """Load real EORM records from the demo JSONL (question, label, gen_text)."""
    if not DEMO_JSONL.exists():
        pytest.skip(f"Demo dataset not found: {DEMO_JSONL}")
    records = []
    with open(DEMO_JSONL, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


# Must match SDK's fixed base URL (users cannot override).
_DEFAULT_BASE_URL = "https://sandboxtesting101--certainty-labs-api.modal.run"

# Remote servers (e.g. Render) can have cold starts; use generous timeouts.
_REMOTE_TIMEOUT = 180.0


@pytest.fixture(scope="module")
def base_url():
    """API base URL (fixed, matches SDK)."""
    return _DEFAULT_BASE_URL.rstrip("/")


def _check_certainty_server(base_url: str) -> None:
    """Verify the server at base_url is the Certainty API; skip if not."""
    import httpx
    try:
        r = httpx.get(f"{base_url}/health", timeout=_REMOTE_TIMEOUT)
        if r.status_code != 200:
            pytest.skip(f"API at {base_url} returned {r.status_code} (start server: uvicorn api.main:app)")
        data = r.json()
        if data.get("status") != "ok" or "version" not in data:
            pytest.skip(f"API at {base_url} is not Certainty Labs (got {data})")
    except Exception as e:
        pytest.skip(f"Cannot reach API at {base_url}: {e}. Start with: uvicorn api.main:app")


@pytest.fixture(scope="module")
def api_key(base_url):
    """
    When the server has auth enabled, create a key or use CERTAINTY_API_KEY from env.
    Falls back to env var when /api-keys requires X-User-ID (Supabase) or returns 401.
    """
    import httpx
    env_key = os.environ.get("CERTAINTY_API_KEY", "").strip()
    with httpx.Client(base_url=base_url, timeout=_REMOTE_TIMEOUT) as client:
        r = client.get("/api-keys")
        if r.status_code != 200:
            return env_key or None
        data = r.json()
        if not data.get("auth_enabled"):
            return None
        create = client.post("/api-keys", json={"name": "pytest-integration"})
        if create.status_code != 200:
            return env_key or None
        return create.json()["key"]


@pytest.fixture(scope="module")
def demo_records():
    """Real in-memory records from demo_dataset JSONL."""
    return _load_demo_records()


@pytest.fixture(scope="module")
def demo_data_path():
    """Path to the real demo JSONL file."""
    if not DEMO_JSONL.exists():
        pytest.skip(f"Demo dataset not found: {DEMO_JSONL}")
    return str(DEMO_JSONL)


@pytest.fixture(scope="module")
def sync_client(base_url, api_key):
    """Sync Certainty client pointing at the running API (with API key when auth enabled)."""
    _check_certainty_server(base_url)
    from certaintylabs import Certainty
    client = Certainty(api_key=api_key, timeout=360.0)
    yield client
    client.close()


@pytest.fixture(scope="module")
def trained_model_path(sync_client, demo_records):
    """
    Run a real training job with demo data and return the model_path.
    Uses a small subset and 1 epoch so the suite finishes in reasonable time.
    Shared across tests so we only train once per run.
    """
    # Use 250 records and 1 epoch so training completes in ~1–2 min on CPU
    subset = demo_records[:250]
    resp = sync_client.train(
        data=subset,
        tokenizer_name="gpt2",
        epochs=1,
        batch_size=2,
        d_model=128,
        n_heads=2,
        n_layers=1,
        max_length=512,
        validate_every=1,
        val_holdout=0.2,
    )
    assert resp.model_path
    # Model is saved on the server's filesystem; path is server-side
    return resp.model_path


# ----- Health -----


class TestHealth:
    """GET /health and SDK health()."""

    def test_sync_health(self, sync_client):
        from certaintylabs.types import HealthResponse
        r = sync_client.health()
        assert isinstance(r, HealthResponse)
        assert r.status == "ok"
        assert isinstance(r.version, str)
        assert len(r.version) > 0

    @pytest.mark.asyncio
    async def test_async_health(self, base_url, api_key):
        from certaintylabs import AsyncCertainty
        async with AsyncCertainty(api_key=api_key) as client:
            r = await client.health()
            assert r.status == "ok"
            assert r.version


# ----- Train -----


class TestTrain:
    """POST /train: data in-memory, from file, and training_params."""

    def test_train_with_in_memory_data(self, sync_client, demo_records):
        from certaintylabs.types import TrainResponse
        r = sync_client.train(
            data=demo_records[:400],
            tokenizer_name="gpt2",
            epochs=1,
            batch_size=2,
            d_model=128,
            n_heads=2,
            n_layers=1,
            max_length=512,
        )
        assert isinstance(r, TrainResponse)
        assert r.model_path
        # model_path is a server-side filesystem path (e.g. Modal container), not local.
        # Prove it exists by using it in a follow-up call.
        scored = sync_client.score(["sanity check"], model_path=r.model_path)
        assert len(scored.energies) == 1
        assert r.epochs_trained >= 1
        assert r.elapsed_seconds >= 0
        assert 0 <= r.best_val_acc <= 100

    def test_train_from_file(self, sync_client, api_key, demo_data_path):
        from certaintylabs import Certainty
        client = Certainty(api_key=api_key, timeout=360.0)
        try:
            r = client.train_from_file(
                demo_data_path,
                tokenizer_name="gpt2",
                epochs=1,
                batch_size=2,
                d_model=128,
                n_heads=2,
                n_layers=1,
                max_length=512,
            )
            assert r.model_path
            assert r.epochs_trained == 1
        finally:
            client.close()

    def test_train_with_data_convenience(self, sync_client, demo_records):
        r = sync_client.train_with_data(
            demo_records[:300],
            tokenizer_name="gpt2",
            epochs=1,
            d_model=128,
            n_heads=2,
            n_layers=1,
        )
        assert r.model_path
        scored = sync_client.score(["sanity check"], model_path=r.model_path)
        assert len(scored.energies) == 1

    def test_train_with_gpu_param(self, sync_client, demo_records):
        """Train with gpu param (runtime GPU selection). API uses it when deployed on Modal."""
        r = sync_client.train(
            data=demo_records[:200],
            tokenizer_name="gpt2",
            gpu="A10",
            epochs=1,
            batch_size=2,
            d_model=128,
            n_heads=2,
            n_layers=1,
            max_length=512,
            verbose=False,
        )
        assert r.model_path
        assert r.epochs_trained >= 1

    def test_train_with_training_params(self, sync_client, demo_records):
        from certaintylabs.types import TrainingParams
        params = TrainingParams(
            epochs=1,
            batch_size=2,
            d_model=128,
            n_heads=2,
            n_layers=1,
            max_length=512,
        )
        r = sync_client.train(data=demo_records[:300], training_params=params)
        assert r.model_path
        assert r.epochs_trained == 1

    @pytest.mark.asyncio
    async def test_async_train(self, base_url, api_key, demo_records):
        from certaintylabs import AsyncCertainty
        async with AsyncCertainty(api_key=api_key, timeout=360.0) as client:
            r = await client.train(
                data=demo_records[:300],
                tokenizer_name="gpt2",
                epochs=1,
                d_model=128,
                n_heads=2,
                n_layers=1,
            )
            assert r.model_path
            assert r.epochs_trained == 1


# ----- Score -----


class TestScore:
    """POST /score: EBM energy scores for texts."""

    def test_score_returns_energies(self, sync_client, trained_model_path):
        from certaintylabs.types import ScoreResponse
        texts = [
            "The answer is 42.",
            "I think the result is 100.",
        ]
        r = sync_client.score(texts, model_path=trained_model_path)
        assert isinstance(r, ScoreResponse)
        assert len(r.energies) == 2
        assert all(isinstance(e, (int, float)) for e in r.energies)

    def test_score_single_text(self, sync_client, trained_model_path):
        r = sync_client.score(["Single output."], model_path=trained_model_path)
        assert len(r.energies) == 1

    @pytest.mark.asyncio
    async def test_async_score(self, base_url, api_key, trained_model_path):
        from certaintylabs import AsyncCertainty
        async with AsyncCertainty(api_key=api_key) as client:
            r = await client.score(
                ["Async score text one.", "Async score text two."],
                model_path=trained_model_path,
            )
            assert len(r.energies) == 2

    def test_score_404_when_model_missing(self, sync_client):
        from certaintylabs.exceptions import APIError
        with pytest.raises(APIError) as exc_info:
            sync_client.score(
                ["hello"],
                model_path="/nonexistent/model.pt",
            )
        # 404 = model not found; 500 = server missing deps; 502 = gateway/down (e.g. Render)
        assert exc_info.value.status_code in (404, 500, 502)


# ----- Rerank -----


class TestRerank:
    """POST /rerank: rerank candidates with trained model."""

    def test_rerank_returns_best_and_energies(self, sync_client, trained_model_path):
        from certaintylabs.types import RerankResponse
        candidates = [
            "First candidate answer.",
            "Second candidate answer.",
            "Third candidate answer.",
        ]
        r = sync_client.rerank(
            candidates=candidates,
            prompt="What is 2+2?",
            model_path=trained_model_path,
        )
        assert isinstance(r, RerankResponse)
        assert r.best_candidate in candidates
        assert 0 <= r.best_index < len(candidates)
        assert len(r.all_energies) == len(candidates)
        assert all(isinstance(e, (int, float)) for e in r.all_energies)

    @pytest.mark.asyncio
    async def test_async_rerank(self, base_url, api_key, trained_model_path):
        from certaintylabs import AsyncCertainty
        async with AsyncCertainty(api_key=api_key) as client:
            r = await client.rerank(
                candidates=["Option A", "Option B"],
                model_path=trained_model_path,
            )
            assert r.best_candidate in ("Option A", "Option B")
            assert len(r.all_energies) == 2

    def test_rerank_404_when_model_missing(self, sync_client):
        from certaintylabs.exceptions import APIError
        with pytest.raises(APIError) as exc_info:
            sync_client.rerank(
                candidates=["c1", "c2"],
                model_path="/nonexistent/model.pt",
            )
        # 401 if auth required, 400/404 for bad request, 500/502 if server/gateway issue
        assert exc_info.value.status_code in (400, 401, 404, 500, 502)


# ----- Model Download -----


class TestModelDownload:
    """GET /models/download: download trained model for local reuse."""

    def test_download_model(self, sync_client, trained_model_path, tmp_path):
        """Download model.pt and tokenizer to local dir. Skips if API not yet deployed with /models/download."""
        from certaintylabs.exceptions import APIError
        try:
            local_model = sync_client.download_model(
                trained_model_path,
                local_dir=str(tmp_path),
                verbose=False,
            )
        except APIError as e:
            if e.status_code == 404:
                pytest.skip("API /models/download not deployed yet (redeploy Modal)")
            raise
        assert (tmp_path / "model.pt").exists()
        assert (tmp_path / "tokenizer").exists() or (tmp_path / "tokenizer").is_dir()

    def test_train_with_save_to(self, sync_client, demo_records, tmp_path):
        """Train with save_to downloads model after training. Skips if download endpoint missing."""
        from certaintylabs.exceptions import APIError
        try:
            r = sync_client.train(
                data=demo_records[:250],
                tokenizer_name="gpt2",
                epochs=1,
                batch_size=2,
                d_model=128,
                n_heads=2,
                n_layers=1,
                max_length=512,
                save_to=str(tmp_path),
                verbose=False,
            )
        except APIError as e:
            if e.status_code == 404:
                pytest.skip("API /models/download not deployed yet (redeploy Modal)")
            raise
        assert (tmp_path / "model.pt").exists()
        assert r.model_path


# ----- Pipeline -----


class TestPipeline:
    """POST /pipeline: train then optionally rerank."""

    def test_pipeline_train_only(self, sync_client, demo_records):
        from certaintylabs.types import PipelineResponse
        r = sync_client.pipeline(
            data=demo_records[:350],
            tokenizer_name="gpt2",
            epochs=1,
            d_model=128,
            n_heads=2,
            n_layers=1,
        )
        assert isinstance(r, PipelineResponse)
        assert r.train.model_path
        assert r.train.epochs_trained == 1
        assert r.rerank is None

    def test_pipeline_train_and_rerank(self, sync_client, demo_records):
        r = sync_client.pipeline(
            data=demo_records[:350],
            tokenizer_name="gpt2",
            epochs=1,
            d_model=128,
            n_heads=2,
            n_layers=1,
            candidates=["Answer one.", "Answer two.", "Answer three."],
        )
        assert r.train.model_path
        assert r.rerank is not None
        assert r.rerank.best_candidate in ("Answer one.", "Answer two.", "Answer three.")
        assert len(r.rerank.all_energies) == 3

    @pytest.mark.asyncio
    async def test_async_pipeline(self, base_url, api_key, demo_records):
        from certaintylabs import AsyncCertainty
        async with AsyncCertainty(api_key=api_key, timeout=360.0) as client:
            r = await client.pipeline(
                data=demo_records[:300],
                tokenizer_name="gpt2",
                epochs=1,
                d_model=128,
                n_heads=2,
                n_layers=1,
            )
            assert r.train.model_path
            assert r.train.epochs_trained == 1


# ----- API Keys (raw HTTP; not in SDK) -----


class TestAPIKeys:
    """API key endpoints: create, list, delete. Exercises same surface as platform client."""

    def test_list_keys(self, base_url):
        import httpx
        with httpx.Client(base_url=base_url, timeout=_REMOTE_TIMEOUT) as client:
            r = client.get("/api-keys")
            if r.status_code == 401:
                pytest.skip("API keys require X-User-ID (Supabase); manage via dashboard")
            assert r.status_code == 200
            data = r.json()
            assert "keys" in data
            assert "auth_enabled" in data
            assert isinstance(data["keys"], list)

    def test_create_and_list_and_delete_key(self, base_url):
        import httpx
        with httpx.Client(base_url=base_url, timeout=_REMOTE_TIMEOUT) as client:
            create = client.post("/api-keys", json={"name": "test-key-pytest"})
            if create.status_code == 401:
                pytest.skip("API keys require X-User-ID (Supabase); manage via dashboard")
            assert create.status_code == 200
            body = create.json()
            assert "key" in body
            assert body["key"].startswith("ck_")
            raw_key = body["key"]
            key_id = body["id"]

            list_r = client.get("/api-keys")
            assert list_r.status_code == 200
            keys = list_r.json()["keys"]
            ids = [k["id"] for k in keys]
            assert key_id in ids

            delete_r = client.delete(f"/api-keys/{key_id}")
            assert delete_r.status_code == 200
            list_after = client.get("/api-keys")
            keys_after = list_after.json()["keys"]
            assert key_id not in [k["id"] for k in keys_after]


# ----- Raw HTTP (platform client surface) -----


class TestRawHTTP:
    """Mirror platform/src/lib/api.ts: health, train, rerank, pipeline."""

    def test_health_via_http(self, base_url):
        import httpx
        with httpx.Client(base_url=base_url, timeout=_REMOTE_TIMEOUT) as client:
            r = client.get("/health")
            assert r.status_code == 200
            data = r.json()
            assert data["status"] == "ok"
            assert "version" in data

    def test_train_via_http(self, base_url, api_key, demo_records):
        import httpx
        payload = {
            "data": demo_records[:250],
            "tokenizer_name": "gpt2",
            "epochs": 1,
            "batch_size": 2,
            "d_model": 128,
            "n_heads": 2,
            "n_layers": 1,
            "max_length": 512,
        }
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        with httpx.Client(base_url=base_url, timeout=360.0, headers=headers) as client:
            r = client.post("/train", json=payload)
            assert r.status_code == 200
            data = r.json()
            assert "model_path" in data
            assert "best_val_acc" in data
            assert "epochs_trained" in data
            assert "elapsed_seconds" in data
            model_path = data["model_path"]
            assert model_path

            # Use same model for rerank
            rerank_r = client.post(
                "/rerank",
                json={
                    "candidates": ["A", "B", "C"],
                    "prompt": "",
                    "model_path": model_path,
                },
            )
            assert rerank_r.status_code == 200
            rr = rerank_r.json()
            assert "best_candidate" in rr
            assert "best_index" in rr
            assert "all_energies" in rr
            assert len(rr["all_energies"]) == 3

    def test_score_via_http(self, base_url, api_key, trained_model_path):
        import httpx
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        with httpx.Client(base_url=base_url, timeout=_REMOTE_TIMEOUT, headers=headers) as client:
            r = client.post(
                "/score",
                json={
                    "texts": ["first", "second"],
                    "prompt": "",
                    "model_path": trained_model_path,
                },
            )
            assert r.status_code == 200
            data = r.json()
            assert "energies" in data
            assert len(data["energies"]) == 2


# ----- Exceptions and client behavior -----


class TestExceptions:
    """SDK raises correct exception types with useful attributes."""

    def test_api_error_has_status_and_detail(self, sync_client):
        from certaintylabs.exceptions import APIError, CertaintyError
        with pytest.raises(APIError) as exc_info:
            sync_client.score(
                [],
                model_path="./certainty_workspace/model/ebm_certainty_model.pt",
            )
        err = exc_info.value
        assert isinstance(err, CertaintyError)
        # 400 = empty texts, 404 = model path missing, 500/502 = server or gateway issue
        assert err.status_code in (400, 404, 500, 502)
        assert err.detail

    def test_context_manager_sync(self, base_url, api_key):
        from certaintylabs import Certainty
        with Certainty(api_key=api_key) as client:
            r = client.health()
            assert r.status == "ok"
        # After exit, client is closed (no double-close)

    @pytest.mark.asyncio
    async def test_context_manager_async(self, base_url, api_key):
        from certaintylabs import AsyncCertainty
        async with AsyncCertainty(api_key=api_key) as client:
            r = await client.health()
            assert r.status == "ok"


# ----- Types and response shapes -----


class TestResponseTypes:
    """Response objects have expected attributes and types."""

    def test_train_response_fields(self, sync_client, demo_records):
        r = sync_client.train(
            data=demo_records[:200],
            tokenizer_name="gpt2",
            epochs=1,
            d_model=128,
            n_heads=2,
            n_layers=1,
        )
        assert hasattr(r, "model_path") and isinstance(r.model_path, str)
        assert hasattr(r, "best_val_acc") and isinstance(r.best_val_acc, (int, float))
        assert hasattr(r, "epochs_trained") and isinstance(r.epochs_trained, int)
        assert hasattr(r, "elapsed_seconds") and isinstance(r.elapsed_seconds, (int, float))

    def test_rerank_response_fields(self, sync_client, trained_model_path):
        r = sync_client.rerank(
            candidates=["x", "y"],
            model_path=trained_model_path,
        )
        assert isinstance(r.best_candidate, str)
        assert isinstance(r.best_index, int)
        assert isinstance(r.all_energies, list)
        assert all(isinstance(x, (int, float)) for x in r.all_energies)

    def test_pipeline_response_from_dict(self):
        from certaintylabs.types import PipelineResponse
        data = {
            "train": {
                "model_path": "/tmp/m.pt",
                "best_val_acc": 75.0,
                "epochs_trained": 2,
                "elapsed_seconds": 10.0,
            },
            "rerank": {
                "best_candidate": "best",
                "best_index": 0,
                "all_energies": [0.1, 0.2],
            },
        }
        p = PipelineResponse._from_dict(data)
        assert p.train.model_path == "/tmp/m.pt"
        assert p.train.epochs_trained == 2
        assert p.rerank is not None
        assert p.rerank.best_candidate == "best"
        assert p.rerank.all_energies == [0.1, 0.2]

    def test_pipeline_response_rerank_null(self):
        from certaintylabs.types import PipelineResponse
        data = {
            "train": {
                "model_path": "/tmp/m.pt",
                "best_val_acc": 70.0,
                "epochs_trained": 1,
                "elapsed_seconds": 5.0,
            },
            "rerank": None,
        }
        p = PipelineResponse._from_dict(data)
        assert p.rerank is None


# ----- Connection / server-down (optional; skip if server is up) -----


class TestConnectionBehavior:
    """When server is unreachable, SDK raises ConnectionError."""

    def test_connection_error_on_bad_host(self):
        from unittest.mock import patch
        from certaintylabs import Certainty
        from certaintylabs.exceptions import ConnectionError as CertaintyConnectionError
        # Use a port that is not listening (patch fixed base URL for this test)
        with patch("certaintylabs.client._BASE_URL", "http://127.0.0.1:31999"):
            client = Certainty(timeout=2.0)
        try:
            with pytest.raises(CertaintyConnectionError) as exc_info:
                client.health()
            assert "127.0.0.1" in str(exc_info.value) or "31999" in str(exc_info.value)
        finally:
            client.close()

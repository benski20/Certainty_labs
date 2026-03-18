"""Tests for usage metering."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure we use local file store (no Supabase)
os.environ.pop("SUPABASE_URL", None)
os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)


def test_path_to_endpoint():
    from api.usage_meter import path_to_endpoint

    assert path_to_endpoint("/train") == "train"
    assert path_to_endpoint("/rerank") == "rerank"
    assert path_to_endpoint("/score") == "score"
    assert path_to_endpoint("/pipeline") == "pipeline"
    assert path_to_endpoint("/models/download") == "models/download"
    assert path_to_endpoint("/models/download?path=x") == "models/download"
    assert path_to_endpoint("/health") is None
    assert path_to_endpoint("/") is None
    assert path_to_endpoint("/api-keys") is None


def test_file_usage_store_increment_and_get():
    from api.usage_meter import FileUsageStore, _current_periods

    with tempfile.TemporaryDirectory() as tmp:
        usage_file = Path(tmp) / "api_usage.json"
        with patch("api.usage_meter._USAGE_FILE", usage_file):
            store = FileUsageStore()
            store.increment("key1", "train")
            store.increment("key1", "train")
            store.increment("key1", "rerank")
            store.increment("key2", "train")

            month, day = _current_periods()
            k1_month = store.get_by_key("key1", month)
            k2_month = store.get_by_key("key2", month)

            assert k1_month["train"] == 2
            assert k1_month["rerank"] == 1
            assert k2_month["train"] == 1


def test_record_usage_file_store():
    from api.usage_meter import FileUsageStore, get_usage_store, record_usage, _current_periods

    with tempfile.TemporaryDirectory() as tmp:
        usage_file = Path(tmp) / "api_usage.json"
        with patch("api.usage_meter._USAGE_FILE", usage_file):
            record_usage("key_abc", "train")
            record_usage("key_abc", "train")
            record_usage("key_abc", "rerank")

            store = get_usage_store()
            assert isinstance(store, FileUsageStore)
            month, _ = _current_periods()
            data = store.get_by_key("key_abc", month)
            assert data["train"] == 2
            assert data["rerank"] == 1


def test_usage_metering_middleware_flow():
    """
    Test middleware + auth + record_usage flow with a minimal app.
    Avoids importing api.main (which requires Python 3.10+ for str | None).
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from api.usage_meter import path_to_endpoint, record_usage

    app = FastAPI()

    @app.middleware("http")
    async def usage_middleware(request, call_next):
        # Simulate auth setting key_id (as require_api_key does)
        request.state.key_id = "test_key_123"
        response = await call_next(request)
        if 200 <= response.status_code < 300 and hasattr(request.state, "key_id"):
            endpoint = path_to_endpoint(request.url.path)
            if endpoint:
                try:
                    record_usage(request.state.key_id, endpoint)
                except Exception:
                    pass
        return response

    @app.post("/train")
    async def fake_train():
        return {"model_path": "x", "best_val_acc": 75.0}

    with tempfile.TemporaryDirectory() as tmp:
        usage_file = Path(tmp) / "api_usage.json"
        with patch("api.usage_meter._USAGE_FILE", usage_file):
            client = TestClient(app)
            r = client.post("/train")
            assert r.status_code == 200, f"Got {r.status_code}: {r.text}"

        assert usage_file.exists()
        usage_data = json.loads(usage_file.read_text())
        from api.usage_meter import _current_periods
        month, _ = _current_periods()
        assert month in usage_data
        assert "test_key_123" in usage_data[month]
        assert usage_data[month]["test_key_123"]["train"] == 1

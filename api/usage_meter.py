"""Usage metering: record and query API usage per key and endpoint."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_USAGE_FILE = _PROJECT_ROOT / "certainty_workspace" / "api_usage.json"
_TABLE_NAME = "api_usage"

# Path -> endpoint name for metering
_PATH_TO_ENDPOINT = {
    "/train": "train",
    "/rerank": "rerank",
    "/score": "score",
    "/pipeline": "pipeline",
    "/models/download": "models/download",
}


def _current_periods() -> tuple[str, str]:
    """Return (month_period, day_period) e.g. ('2025-03', '2025-03-17')."""
    now = datetime.utcnow()
    month = now.strftime("%Y-%m")
    day = now.strftime("%Y-%m-%d")
    return month, day


def _file_load() -> dict:
    """Load usage from local JSON. Structure: {period: {key_id: {endpoint: count}}}."""
    if not _USAGE_FILE.exists():
        return {}
    try:
        return json.loads(_USAGE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _file_save(data: dict) -> None:
    _USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _USAGE_FILE.write_text(json.dumps(data, indent=2))


class FileUsageStore:
    """Store usage in local JSON (development)."""

    def increment(self, key_id: str, endpoint: str) -> None:
        data = _file_load()
        for period in _current_periods():
            if period not in data:
                data[period] = {}
            if key_id not in data[period]:
                data[period][key_id] = {}
            data[period][key_id][endpoint] = data[period][key_id].get(endpoint, 0) + 1
        _file_save(data)

    def get_by_key(self, key_id: str, period: str) -> dict[str, int]:
        data = _file_load()
        key_data = data.get(period, {}).get(key_id, {})
        return dict(key_data)

    def get_by_user(self, user_id: str, period: str, keys_by_user: list[dict]) -> dict[str, int]:
        key_ids = [k["id"] for k in keys_by_user if k.get("user_id") == user_id]
        data = _file_load()
        period_data = data.get(period, {})
        totals: dict[str, int] = {}
        for kid in key_ids:
            for endpoint, count in period_data.get(kid, {}).items():
                totals[endpoint] = totals.get(endpoint, 0) + count
        return totals


class SupabaseUsageStore:
    """Store usage in Supabase Postgres (production)."""

    def __init__(self, url: str, service_role_key: str):
        try:
            from supabase import create_client
        except ImportError:
            raise ImportError(
                "Supabase usage store requires: pip install supabase. "
                "Or leave SUPABASE_URL unset to use local file storage."
            ) from None
        self._client = create_client(url, service_role_key)

    def increment(self, key_id: str, endpoint: str) -> None:
        month_period, day_period = _current_periods()
        for period in (month_period, day_period):
            self._client.rpc(
                "increment_api_usage",
                {"p_key_id": key_id, "p_period": period, "p_endpoint": endpoint},
            ).execute()

    def get_by_key(self, key_id: str, period: str) -> dict[str, int]:
        resp = (
            self._client.table(_TABLE_NAME)
            .select("endpoint,count")
            .eq("key_id", key_id)
            .eq("period", period)
            .execute()
        )
        return {r["endpoint"]: r["count"] for r in (resp.data or [])}

    def get_by_user(self, user_id: str, period: str, keys_by_user: list[dict]) -> dict[str, int]:
        key_ids = [k["id"] for k in keys_by_user if k.get("user_id") == user_id]
        if not key_ids:
            return {}
        resp = (
            self._client.table(_TABLE_NAME)
            .select("endpoint,count")
            .eq("period", period)
            .in_("key_id", key_ids)
            .execute()
        )
        totals: dict[str, int] = {}
        for r in resp.data or []:
            totals[r["endpoint"]] = totals.get(r["endpoint"], 0) + r["count"]
        return totals


def get_usage_store():
    """Return the active usage store: Supabase if configured, else local file."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if url and key:
        return SupabaseUsageStore(url, key)
    return FileUsageStore()


def path_to_endpoint(path: str) -> str | None:
    """Map request path to endpoint name for metering. Returns None if not a metered endpoint."""
    # Normalize: remove query string, ensure leading /
    p = path.split("?")[0].rstrip("/") or "/"
    if p in _PATH_TO_ENDPOINT:
        return _PATH_TO_ENDPOINT[p]
    # Check prefix for /models/download
    if p.startswith("/models/"):
        return "models/download"
    return None


def record_usage(key_id: str, endpoint: str) -> None:
    """Increment usage count for the given key and endpoint."""
    store = get_usage_store()
    if hasattr(store, "increment"):
        store.increment(key_id, endpoint)

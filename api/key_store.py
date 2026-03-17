"""API key storage backends: Supabase (production) or local JSON file (development)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_KEYS_FILE = _PROJECT_ROOT / "certainty_workspace" / "api_keys.json"
_TABLE_NAME = "api_keys"


def _file_load() -> List[dict]:
    if not _KEYS_FILE.exists():
        return []
    return json.loads(_KEYS_FILE.read_text())


def _file_save(keys: List[dict]) -> None:
    _KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _KEYS_FILE.write_text(json.dumps(keys, indent=2))


class FileKeyStore:
    """Store API keys in a local JSON file (development)."""

    def create(self, record: dict) -> None:
        keys = _file_load()
        keys.append(record)
        _file_save(keys)

    def list_all(self, user_id: str | None = None) -> List[dict]:
        keys = _file_load()
        if user_id is None:
            return keys
        return [k for k in keys if k.get("user_id") == user_id]

    def delete_by_id(self, key_id: str, user_id: str | None = None) -> bool:
        keys = _file_load()
        if user_id is None:
            filtered = [k for k in keys if k["id"] != key_id]
        else:
            filtered = [k for k in keys if not (k["id"] == key_id and k.get("user_id") == user_id)]
        if len(filtered) == len(keys):
            return False
        _file_save(filtered)
        return True

    def exists_hash(self, key_hash: str) -> bool:
        keys = _file_load()
        return any(k["key_hash"] == key_hash for k in keys)


class SupabaseKeyStore:
    """Store API keys in Supabase Postgres (production)."""

    def __init__(self, url: str, service_role_key: str):
        try:
            from supabase import create_client
        except ImportError:
            raise ImportError(
                "Supabase backend requires: pip install supabase. "
                "Or leave SUPABASE_URL unset to use local file storage."
            ) from None
        self._client = create_client(url, service_role_key)

    def create(self, record: dict) -> None:
        self._client.table(_TABLE_NAME).insert(
            {
                "id": record["id"],
                "name": record["name"],
                "key_hash": record["key_hash"],
                "prefix": record["prefix"],
                "created_at": record["created_at"],
                "user_id": record.get("user_id"),
            }
        ).execute()

    def list_all(self, user_id: str | None = None) -> List[dict]:
        query = self._client.table(_TABLE_NAME).select("id,name,key_hash,prefix,created_at,user_id")
        if user_id is not None:
            query = query.eq("user_id", user_id)
        resp = query.execute()
        return list(resp.data) if resp.data else []

    def delete_by_id(self, key_id: str, user_id: str | None = None) -> bool:
        query = self._client.table(_TABLE_NAME).delete().eq("id", key_id)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        resp = query.execute()
        return len(resp.data) > 0 if resp.data else False

    def exists_hash(self, key_hash: str) -> bool:
        resp = self._client.table(_TABLE_NAME).select("id").eq("key_hash", key_hash).limit(1).execute()
        return len(resp.data) > 0 if resp.data else False


def get_key_store():
    """Return the active key store: Supabase if configured, else local file."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if url and key:
        return SupabaseKeyStore(url, key)
    return FileKeyStore()

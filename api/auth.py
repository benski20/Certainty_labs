"""API key authentication for the Certainty Labs API.

Keys can be stored in Supabase (production) or in certainty_workspace/api_keys.json (local).
When no keys exist, auth is disabled (open mode for local development).
"""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request

from api.key_store import get_key_store

_KEY_PREFIX = "ck_"


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key(name: str = "default", user_id: Optional[str] = None) -> tuple[str, dict]:
    """Create a new API key. Returns (raw_key, key_record).

    The raw key is shown once; only the hash is persisted.
    """
    raw = _KEY_PREFIX + secrets.token_hex(24)
    record = {
        "id": secrets.token_hex(8),
        "name": name,
        "key_hash": _hash_key(raw),
        "prefix": raw[:8],
        "created_at": time.time(),
        # Optional: associate with an application user (e.g. Supabase user id)
        "user_id": user_id,
    }
    store = get_key_store()
    store.create(record)
    return raw, record


def list_api_keys(user_id: Optional[str] = None) -> list[dict]:
    """Return key records (hashes, not raw keys).

    When user_id is provided, only returns keys owned by that user.
    """
    return get_key_store().list_all(user_id=user_id)


def revoke_api_key(key_id: str, user_id: Optional[str] = None) -> bool:
    """Remove a key by id. Returns True if found and removed.

    When user_id is provided, only deletes keys owned by that user.
    """
    return get_key_store().delete_by_id(key_id, user_id=user_id)


def _extract_token(request: Request) -> Optional[str]:
    """Pull the API key from Authorization header or X-API-Key header."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()

    x_key = request.headers.get("x-api-key", "")
    if x_key:
        return x_key.strip()

    return None


async def require_api_key(request: Request) -> Optional[str]:
    """FastAPI dependency that enforces API key auth.

    When no keys have been created yet, all requests are allowed (open mode).
    Once at least one key exists, every protected request must carry a valid key.
    """
    store = get_key_store()
    keys = store.list_all()

    if not keys:
        return None

    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Pass it as 'Authorization: Bearer ck_...' or 'X-API-Key: ck_...' header.",
        )

    token_hash = _hash_key(token)
    if not store.exists_hash(token_hash):
        raise HTTPException(status_code=401, detail="Invalid API key.")

    return token

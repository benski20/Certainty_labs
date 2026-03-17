"""API key management endpoints.

These endpoints are intended for use from the authenticated dashboard.
To scope keys to a specific signed-in user, the frontend should send
an ``X-User-ID`` header (for example, the Supabase user id). When present,
only keys with a matching ``user_id`` are returned or deleted.
"""

from fastapi import APIRouter, HTTPException, Request

from api.auth import generate_api_key, list_api_keys, revoke_api_key
from api.schemas import (
    CreateKeyRequest,
    CreateKeyResponse,
    KeyInfo,
    ListKeysResponse,
)

router = APIRouter(prefix="/api-keys")


@router.post("", response_model=CreateKeyResponse)
async def create_key(req: CreateKeyRequest, request: Request):
    """Create a new API key.

    The raw key is returned exactly once in the response.
    Store it securely — it cannot be retrieved again.
    When this is the first key created, auth enforcement activates
    for all protected endpoints.
    """
    user_id = request.headers.get("x-user-id") or None
    raw_key, record = generate_api_key(name=req.name, user_id=user_id)
    return CreateKeyResponse(
        id=record["id"],
        name=record["name"],
        key=raw_key,
        prefix=record["prefix"],
        created_at=record["created_at"],
    )


@router.get("", response_model=ListKeysResponse)
async def get_keys(request: Request):
    """List API keys for the current user (metadata only — hashes are never exposed)."""
    user_id = request.headers.get("x-user-id") or None
    keys = list_api_keys(user_id=user_id)
    # Auth enforcement is global: once any key exists, API key auth is on.
    any_keys = list_api_keys(user_id=None)
    return ListKeysResponse(
        keys=[
            KeyInfo(
                id=k["id"],
                name=k["name"],
                prefix=k["prefix"],
                created_at=k["created_at"],
            )
            for k in keys
        ],
        auth_enabled=len(any_keys) > 0,
    )


@router.delete("/{key_id}")
async def delete_key(key_id: str, request: Request):
    """Revoke an API key by its id. Takes effect immediately."""
    user_id = request.headers.get("x-user-id") or None
    removed = revoke_api_key(key_id, user_id=user_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Key '{key_id}' not found.")
    remaining = list_api_keys(user_id=None)
    return {
        "deleted": key_id,
        "auth_enabled": len(remaining) > 0,
    }

"""API key management endpoints."""

from fastapi import APIRouter, HTTPException

from api.auth import generate_api_key, list_api_keys, revoke_api_key
from api.schemas import (
    CreateKeyRequest,
    CreateKeyResponse,
    KeyInfo,
    ListKeysResponse,
)

router = APIRouter(prefix="/api-keys")


@router.post("", response_model=CreateKeyResponse)
async def create_key(req: CreateKeyRequest):
    """Create a new API key.

    The raw key is returned exactly once in the response.
    Store it securely — it cannot be retrieved again.
    When this is the first key created, auth enforcement activates
    for all protected endpoints.
    """
    raw_key, record = generate_api_key(name=req.name)
    return CreateKeyResponse(
        id=record["id"],
        name=record["name"],
        key=raw_key,
        prefix=record["prefix"],
        created_at=record["created_at"],
    )


@router.get("", response_model=ListKeysResponse)
async def get_keys():
    """List all API keys (metadata only — hashes are never exposed)."""
    keys = list_api_keys()
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
        auth_enabled=len(keys) > 0,
    )


@router.delete("/{key_id}")
async def delete_key(key_id: str):
    """Revoke an API key by its id. Takes effect immediately."""
    removed = revoke_api_key(key_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Key '{key_id}' not found.")
    remaining = list_api_keys()
    return {
        "deleted": key_id,
        "auth_enabled": len(remaining) > 0,
    }

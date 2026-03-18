"""Usage endpoint — return usage for the current API key."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request

from api.usage_meter import get_usage_store

router = APIRouter()


@router.get("/usage")
async def get_usage(request: Request, period: Optional[str] = None):
    """
    Return usage for the current API key.
    Requires auth. period defaults to current month (YYYY-MM).
    """
    if not hasattr(request.state, "key_id"):
        return {"usage": {}, "period": period or "", "detail": "No key_id (auth may be disabled)"}
    key_id = request.state.key_id
    period = period or datetime.utcnow().strftime("%Y-%m")
    store = get_usage_store()
    usage = store.get_by_key(key_id, period)
    return {"usage": usage, "period": period, "key_id": key_id}

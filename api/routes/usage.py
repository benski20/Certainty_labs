"""Usage endpoint — return usage for the current API key or by user (dashboard)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request

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


@router.get("/usage/by-user")
async def get_usage_by_user(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    period: Optional[str] = None,
    periods: Optional[int] = None,
):
    """
    Return total + breakdown usage for a user (dashboard).
    Requires auth + X-User-ID header. period defaults to current month.
    If periods=N, returns last N months for charts.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=400,
            detail="X-User-ID header required for dashboard usage.",
        )
    store = get_usage_store()
    if not hasattr(store, "get_user_summary"):
        raise HTTPException(status_code=501, detail="User summary not available (local store).")

    if periods and periods > 1:
        # Last N months
        now = datetime.utcnow()
        period_list = [
            (now - timedelta(days=30 * i)).strftime("%Y-%m")
            for i in range(periods)
        ]
        rows = store.get_user_summary_range(x_user_id, period_list)
        return {"user_id": x_user_id, "periods": rows}
    period = period or datetime.utcnow().strftime("%Y-%m")
    summary = store.get_user_summary(x_user_id, period)
    return {"user_id": x_user_id, "period": period, **summary}

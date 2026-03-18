#!/usr/bin/env python3
"""
Manual test for usage metering.

Usage:
  Local:  uvicorn api.main:app --host 127.0.0.1 --port 8000
          python scripts/test_usage_metering.py
  Remote: CERTAINTY_BASE_URL=https://...modal.run CERTAINTY_API_KEY=ck_... python scripts/test_usage_metering.py

Creates/uses API key, POSTs /train, then verifies via GET /usage or local api_usage.json.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

BASE_URL = os.environ.get("CERTAINTY_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = 300.0  # Training can be slow


def main():
    print("=== Usage Metering Test ===\n")

    # 1. Health check
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=10)
        assert r.status_code == 200, r.text
        print(f"1. Health OK: {r.json()}")
    except Exception as e:
        print(f"ERROR: Cannot reach API at {BASE_URL}. Start with: uvicorn api.main:app")
        print(f"  {e}")
        return 1

    # 2. Get or create API key
    api_key = os.environ.get("CERTAINTY_API_KEY", "").strip()
    if api_key:
        print(f"2. Using CERTAINTY_API_KEY from env: {api_key[:12]}...")
    else:
        # Try to create a key (works when Supabase not configured)
        r = httpx.post(f"{BASE_URL}/api-keys", json={"name": "usage-test"}, timeout=10)
        if r.status_code == 200:
            api_key = r.json()["key"]
            print(f"2. Created API key: {api_key[:12]}...")
        else:
            print(f"2. POST /api-keys failed: {r.status_code} {r.text}")
            print("   Set CERTAINTY_API_KEY or ensure Supabase is not configured (local keys).")
            return 1

    headers = {"Authorization": f"Bearer {api_key}"}

    # 3. Check usage file before request
    usage_file = _PROJECT_ROOT / "certainty_workspace" / "api_usage.json"
    usage_before = {}
    if usage_file.exists():
        usage_before = json.loads(usage_file.read_text())
        print(f"3. Usage before: {usage_before}")
    else:
        print("3. No usage file yet (expected)")

    # 4. Make a request to /train (minimal config)
    print("\n4. POST /train (epochs=1, batch_size=2)...")
    r = httpx.post(
        f"{BASE_URL}/train",
        json={"epochs": 1, "batch_size": 2, "d_model": 64, "n_heads": 2, "n_layers": 1},
        headers=headers,
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        print(f"   FAILED: {r.status_code} {r.text[:500]}")
        return 1
    print(f"   OK: {r.json()}")

    # 5. Verify usage — try GET /usage first (works for remote API), else check local file
    r_usage = httpx.get(f"{BASE_URL}/usage", headers=headers, timeout=10)
    if r_usage.status_code == 200:
        data = r_usage.json()
        usage_data = data.get("usage", {})
        period = data.get("period", "")
        if "train" in usage_data and usage_data["train"] >= 1:
            print(f"\n5. SUCCESS: GET /usage shows train={usage_data['train']} (period={period})")
        else:
            print(f"\n5. Usage from API: {data}")
            if not usage_data:
                print("   WARNING: No usage recorded (api_usage table may need migration)")
    elif usage_file.exists():
        usage_after = json.loads(usage_file.read_text())
        print(f"\n5. Usage (local file): {json.dumps(usage_after, indent=2)}")
        found = False
        for period_data in usage_after.values():
            if isinstance(period_data, dict):
                for endpoints in period_data.values():
                    if isinstance(endpoints, dict) and "train" in endpoints:
                        found = True
                        break
        if found:
            print("   SUCCESS: train usage found in local file")
    else:
        print("\n5. No GET /usage endpoint and no local api_usage.json (remote API with Supabase?)")

    print("\n=== Usage metering test complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

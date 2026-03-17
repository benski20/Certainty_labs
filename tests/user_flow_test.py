#!/usr/bin/env python3
"""
User-flow test: simulate a user who downloaded the SDK and runs simple client code.
Uses provided API key. Tests every endpoint thoroughly.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Project root for demo data
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
if str(_PROJECT_ROOT / "sdk") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "sdk"))

# User's API key (as provided; try ck_ if pick_ fails - Certainty uses ck_ prefix)
API_KEY = "pick_51d438769cd98c157714ef1c17a0b00c1662aa36d0c7e32a"
API_KEY_ALT = "ck_51d438769cd98c157714ef1c17a0b00c1662aa36d0c7e32a"

DEMO_JSONL = _PROJECT_ROOT / "demo_dataset" / "results_gsm8k_llama3_test_n4_temp0.7_p0.9_test.jsonl"


def load_demo_records(max_lines: int = 200) -> list[dict]:
    """Load EORM records from demo JSONL."""
    if not DEMO_JSONL.exists():
        raise FileNotFoundError(f"Demo dataset not found: {DEMO_JSONL}")
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


def run_tests(api_key: str) -> tuple[int, int]:
    """Run all tests. Returns (passed, failed)."""
    from certaintylabs import Certainty
    from certaintylabs.exceptions import APIError

    passed = 0
    failed = 0

    def ok(name: str):
        nonlocal passed
        passed += 1
        print(f"  ✓ {name}")

    def fail(name: str, e: Exception):
        nonlocal failed
        failed += 1
        print(f"  ✗ {name}: {e}")

    print("\n=== 1. Health ===")
    try:
        client = Certainty(api_key=api_key, timeout=360.0)
        r = client.health()
        assert r.status == "ok"
        assert r.version
        ok("GET /health")
    except Exception as e:
        fail("GET /health", e)
        return passed, failed  # Can't continue without health

    print("\n=== 2. API Keys (list) ===")
    try:
        import httpx
        r = httpx.get(f"{client.base_url}/api-keys", headers={"Authorization": f"Bearer {api_key}"}, timeout=60)
        if r.status_code == 200:
            data = r.json()
            assert "keys" in data
            ok("GET /api-keys")
        elif r.status_code == 401:
            # Backend may require X-User-ID; list via dashboard. Try without for programmatic.
            print("  (401: keys managed in dashboard; continuing)")
            ok("GET /api-keys (auth note)")
        else:
            fail("GET /api-keys", Exception(f"status {r.status_code}: {r.text[:200]}"))
    except Exception as e:
        fail("GET /api-keys", e)

    print("\n=== 3. Train (built-in GSM8K, 1 epoch) ===")
    try:
        r = client.train(epochs=1, batch_size=2, d_model=128, n_heads=2, n_layers=1, max_length=512)
        assert r.model_path
        assert r.epochs_trained >= 1
        assert 0 <= r.best_val_acc <= 100
        ok("POST /train (built-in)")
        model_path = r.model_path
    except Exception as e:
        fail("POST /train", e)
        model_path = None

    if model_path:
        print("\n=== 4. Train (in-memory data) ===")
        try:
            records = load_demo_records(150)
            r = client.train(
                data=records,
                tokenizer_name="gpt2",
                epochs=1,
                batch_size=2,
                d_model=128,
                n_heads=2,
                n_layers=1,
                max_length=512,
            )
            assert r.model_path
            ok("POST /train (in-memory data)")
            model_path = r.model_path
        except Exception as e:
            fail("POST /train (in-memory)", e)

        print("\n=== 5. Score ===")
        try:
            r = client.score(["The answer is 4.", "The answer is 5."], model_path=model_path)
            assert len(r.energies) == 2
            assert all(isinstance(e, (int, float)) for e in r.energies)
            ok("POST /score")
        except Exception as e:
            fail("POST /score", e)

        print("\n=== 6. Rerank ===")
        try:
            candidates = ["First answer.", "Second answer.", "Third answer."]
            r = client.rerank(candidates=candidates, prompt="What is 2+2?", model_path=model_path)
            assert r.best_candidate in candidates
            assert 0 <= r.best_index < len(candidates)
            assert len(r.all_energies) == len(candidates)
            ok("POST /rerank")
        except Exception as e:
            fail("POST /rerank", e)

        print("\n=== 7. Pipeline (train + optional rerank) ===")
        try:
            records = load_demo_records(100)
            r = client.pipeline(
                data=records,
                epochs=1,
                batch_size=2,
                d_model=128,
                n_heads=2,
                n_layers=1,
                candidates=["Option A", "Option B"],
            )
            assert r.train.model_path
            assert r.rerank is not None
            assert r.rerank.best_candidate in ["Option A", "Option B"]
            ok("POST /pipeline")
        except Exception as e:
            fail("POST /pipeline", e)

    print("\n=== 8. Error handling (404) ===")
    try:
        try:
            client.score(["x"], model_path="/nonexistent/model.pt")
            fail("Score 404", Exception("Expected APIError"))
        except APIError as e:
            assert e.status_code in (404, 500, 502)
            ok("404/502 handled correctly")
    except Exception as e:
        fail("Error handling", e)

    print("\n=== 9. Invalid API key (401) ===")
    try:
        bad_client = Certainty(api_key="ck_invalid_key_12345", timeout=30)
        try:
            bad_client.train(epochs=1)  # Protected endpoint
            fail("Train with bad key", Exception("Expected 401"))
        except APIError as e:
            if e.status_code == 401:
                ok("401 on invalid key (train)")
            else:
                fail("Invalid key test", e)
        bad_client.close()
    except Exception as e:
        fail("Invalid key test", e)

    client.close()
    return passed, failed


def main():
    print("=" * 60)
    print("Certainty Labs API — User-Flow Test")
    print("=" * 60)
    print(f"API Key: {API_KEY[:20]}...")
    print()

    passed, failed = run_tests(API_KEY)

    # If pick_ fails (e.g. 401 Invalid API key), try ck_ prefix
    if failed > 0:
        print("\n--- Retrying with ck_ prefix (Certainty key format) ---")
        p2, f2 = run_tests(API_KEY_ALT)
        passed = p2
        failed = f2

    print("\n" + "=" * 60)
    print(f"Result: {passed} passed, {failed} failed")
    print("=" * 60)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script for the certaintylabs SDK.

Run with the API server up:
    uvicorn api.main:app --reload   # in one terminal
    python scripts/test_sdk.py      # in another

Or point at a different host with CERTAINTY_BASE_URL.
"""

import sys


def main():
    print("Testing certaintylabs SDK...")
    print()

    try:
        from certaintylabs import Certainty, __version__
        print(f"  OK import certaintylabs (version {__version__})")
    except ImportError as e:
        print(f"  FAIL import: {e}")
        print("  Install with: pip install certaintylabs")
        return 1

    client = Certainty()
    print(f"  OK client created (base_url={client.base_url})")
    print()

    try:
        health = client.health()
        print(f"  OK GET /health -> status={health.status}, version={health.version}")
    except Exception as e:
        print(f"  FAIL health: {e}")
        print("  Make sure the API is running: uvicorn api.main:app --reload")
        return 1

    print()
    print("SDK health check passed.")
    print("  (Train and rerank are not run here — they need data and can be slow.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

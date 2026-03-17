#!/usr/bin/env python3
"""
User test: install with pip install certaintylabs, then run:
  CERTAINTY_API_KEY="ck_..." python examples/user_test.py
"""
from certaintylabs import Certainty

client = Certainty()
print(client.health().version)           # 0.1.0
r = client.train(epochs=1)               # built-in GSM8K
best = client.rerank(["4","5","6"], prompt="What is 2+2?")
print(best.best_candidate)

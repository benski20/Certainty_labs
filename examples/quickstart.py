#!/usr/bin/env python3
"""
Certainty Labs — Quickstart (real user flow)

Run this after:
  1. Create API key in Platform → API Keys
  2. export CERTAINTY_API_KEY="ck_..."

  pip install certaintylabs
  python examples/quickstart.py
"""
import os
from certaintylabs import Certainty

def main():
    # SDK reads CERTAINTY_API_KEY from env (base URL is fixed)
    api_key = os.environ.get("CERTAINTY_API_KEY")
    if not api_key:
        print("Error: Set CERTAINTY_API_KEY (create key in Platform → API Keys)")
        raise SystemExit(1)
    client = Certainty()

    # 1. Check the server is running
    print("1. Health check...")
    health = client.health()
    print(f"   OK — version {health.version}")

    # 2. Train on built-in GSM8K (per quickstart)
    print("\n2. Training on built-in GSM8K (1 epoch)...")
    result = client.train(epochs=1, batch_size=2, d_model=256, n_heads=2, n_layers=1)
    print(f"   Accuracy: {result.best_val_acc:.1f}% in {result.elapsed_seconds:.0f}s")
    print(f"   Model: {result.model_path}")

    # 3. Rerank candidate answers (per docs)
    print("\n3. Reranking candidates...")
    candidates = [
        "Janet sells 16 - 3 - 4 = 9 eggs. 9 * 2 = $18. The answer is 18.",
        "Janet has 16 eggs, sells all. 16 * 2 = $32.",
        "Janet sells 16 - 3 - 4 = 9 duck eggs. 9 * $2 = $18. The answer is $18.",
    ]
    prompt = "Janet's ducks lay 16 eggs per day. She eats three and bakes muffins with four. She sells the rest at $2 each. How much does she make?"
    best = client.rerank(candidates=candidates, prompt=prompt, model_path=result.model_path)
    print(f"   Best: {best.best_candidate[:60]}...")
    print(f"   Energies: {[f'{e:.2f}' for e in best.all_energies]}")

    # 4. Score outputs (verifiable AI — per docs)
    print("\n4. Scoring outputs (confidence tracking)...")
    scores = client.score(
        texts=["The answer is 18.", "The answer is 32."],
        prompt=prompt,
        model_path=result.model_path,
    )
    print(f"   Energies: {scores.energies} (lower = higher confidence)")

    # 5. Train from file (if demo data exists)
    from pathlib import Path
    _root = Path(__file__).resolve().parent.parent
    demo_path = _root / "demo_dataset" / "results_gsm8k_llama3_test_n4_temp0.7_p0.9_test.jsonl"
    if demo_path.exists():
        print("\n5. Train from file...")
        file_result = client.train_from_file(
            str(demo_path),
            tokenizer_name="gpt2",
            epochs=1,
            batch_size=2,
            d_model=256,
            n_heads=2,
            n_layers=1,
        )
        print(f"   Accuracy: {file_result.best_val_acc:.1f}%")
    else:
        print("\n5. (Skipping train_from_file — no demo data)")

    # 6. Pipeline: train + rerank in one call
    print("\n6. Pipeline (train + rerank)...")
    pipeline_result = client.pipeline(
        epochs=1,
        batch_size=2,
        d_model=256,
        n_heads=2,
        n_layers=1,
        candidates=["Option A", "Option B", "Option C"],
    )
    print(f"   Train acc: {pipeline_result.train.best_val_acc:.1f}%")
    print(f"   Rerank best: {pipeline_result.rerank.best_candidate}")

    client.close()
    print()
    print("\n✓ All done. Certainty API works as documented.")


if __name__ == "__main__":
    main()

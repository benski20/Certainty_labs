# Certainty Labs

**Constraint-Guaranteed Outputs for Production AI**

Certainty Labs trains a lightweight [TransEBM](https://github.com/ericjiang18/EnergyORM) energy model on your labeled data and uses it to rerank LLM outputs — selecting the most constraint-satisfying candidate without retraining the base LLM. Works with GPT-4o, Claude, Llama 3, Mistral, or any model.

## How It Works

```
Your data (EORM JSONL)  ->  TransEBM Trainer  ->  ebm_model.pt
                                                      |
Reranker  <-  lowest-energy candidate (best)  <-  N candidate outputs
```

1. **Provide** training data in EORM format (question, label 0/1, gen_text) or use the built-in GSM8K dataset.
2. **Train** a TransEBM with Bradley-Terry contrastive loss.
3. **Rerank** N candidate LLM outputs — pick the one with lowest energy.

## Quickstart

```bash
# Install
pip install -e '.[demo,dev]'

# Run tests
pytest tests/ -v

# Start the API
uvicorn api.main:app --reload
```

## Bring Your Own Data

You can train on the **built-in GSM8K dataset**, on **your own data** (in-memory or JSONL file), or **inference only** with a pre-trained model.

**Option 1: Built-in dataset (no data needed)**  
Train on the included GSM8K-Llama math reasoning data.

```python
from certainty.pipeline import CertaintyPipeline
pipeline = CertaintyPipeline()
pipeline.train()  # uses built-in dataset
best, idx, energies = pipeline.rerank(["answer A", "answer B", "answer C"], prompt="...")
```

**Option 2: Your own data**  
EORM format: each record has `question`, `label` (0 or 1), and `gen_text`.

*Python library:*
```python
pipeline = CertaintyPipeline()
pipeline.load_data("your_data.jsonl")  # or load_data_records([{...}, ...])
pipeline.train()
```

*API / SDK:*
```python
from certaintylabs import Certainty
client = Certainty()
samples = [{"question": "...", "label": 1, "gen_text": "..."}, ...]
result = client.train_with_data(samples, epochs=10)
# Or: result = client.train_from_file("your_data.jsonl", epochs=10)
```

**Option 3: Inference only**  
Load a trained model and rerank.

```python
pipeline = CertaintyPipeline()
pipeline.load_model("path/to/model.pt")
best, idx, energies = pipeline.rerank(candidates)
```

**Rerank with your own LLM to generate candidates:**  
Pass `openai_api_key` (and optionally `openai_model`, `openai_base_url`) to the rerank API so it generates N candidates with your model, then reranks them in one call.

### Generating your own data externally

If you need to create EORM-format training data yourself (e.g. your own labeling pipeline or constraints):

- **Format:** JSONL, one JSON object per line. Each line: `{"question": "...", "label": 0 or 1, "gen_text": "..."}`.  
  `question` = prompt or task; `label` = 1 for correct / constraint-satisfying, 0 for incorrect; `gen_text` = the model output.
- **Labeling:** Use your own criteria (rule-based, model-as-judge, human) to set `label` per (question, gen_text). Each question should have at least some positive and some negative examples for contrastive training.
- **Export:** Save as a `.jsonl` file and use `train_from_file(path)` (SDK) or `POST /train` with `data` (inline) or `data_path` (server path).

Supported data formats: JSONL. Training parameters (epochs, batch_size, d_model, lr, etc.) are configurable via the API and SDK (see SDK README).

## Architecture

- **Model**: Lightweight Transformer (EORM), trained from scratch
- **Loss**: Bradley-Terry pairwise loss (`softplus(E_pos - E_neg)`)
- **Tokenizer**: GPT-2 (reused; no pretrained weights)
- **Training**: AdamW (lr=5e-5), cosine warmup, FP16 AMP, gradient clipping

## API

| Endpoint   | Method | Description                          |
|-----------|--------|--------------------------------------|
| `/health` | GET    | Health check                         |
| `/train`  | POST   | Train on your data or built-in       |
| `/rerank` | POST   | Score candidates; optional LLM gen   |
| `/pipeline` | POST | Train then optionally rerank         |

## Project Structure

```
certainty/
├── data/         # Sampling, labeling (internal), EORM loading
├── models/       # TransEBM + Bradley-Terry loss + trainer
├── inference/    # Reranker
└── pipeline.py   # High-level orchestrator
```

## License

MIT

# Certainty Python SDK

Python client for the [Certainty Labs](https://certaintylabs.ai) API — constraint enforcement for production LLMs.

Train TransEBM energy models and rerank LLM outputs in a few lines of code.

The SDK supports **bring your own data** (in-memory or local JSONL), **tune training** (epochs, batch size, model size, learning rate, etc.), and **use your own LLM** in rerank to generate candidates (openai_api_key + openai_base_url). You provide EORM-format training data; generate it externally if needed (see below).

## Install

```bash
pip install certaintylabs
```

## Quick Start

```python
from certaintylabs import Certainty

client = Certainty(base_url="http://localhost:8000")

# Check the server is running
health = client.health()
print(health.version)  # "0.1.0"

# Train on the built-in GSM8K math reasoning dataset
result = client.train(epochs=10, d_model=768)
print(f"Accuracy: {result.best_val_acc:.1%} in {result.elapsed_seconds:.0f}s")

# Rerank LLM candidate answers
best = client.rerank(
    candidates=[
        "Janet sells 16 - 3 - 4 = 9 eggs. 9 * 2 = $18. The answer is 18.",
        "Janet has 16 eggs, sells all. 16 * 2 = $32.",
        "Janet sells 16 - 3 - 4 = 9 duck eggs. 9 * $2 = $18. The answer is $18.",
    ],
    prompt="Janet's ducks lay 16 eggs per day. She eats three and bakes muffins with four. She sells the rest at $2 each. How much does she make?",
)
print(best.best_candidate)
```

## Async Support

```python
from certaintylabs import AsyncCertainty

async def main():
    async with AsyncCertainty() as client:
        result = await client.train(epochs=5)
        best = await client.rerank(["A", "B", "C"], prompt="...")
```

## Production: base URL and API key

For production or shared deployments, **don’t hardcode the API URL or API key**. Use environment variables so the same code works everywhere:

| Variable               | Purpose |
|------------------------|--------|
| `CERTAINTY_BASE_URL`   | API root (e.g. `https://api.certaintylabs.ai` or your own host). |
| `CERTAINTY_API_KEY`     | API key (e.g. `ck_...`). |

If these are set, `Certainty()` and `AsyncCertainty()` use them when you don’t pass `base_url` or `api_key`:

```bash
export CERTAINTY_BASE_URL="https://api.certaintylabs.ai"
export CERTAINTY_API_KEY="ck_your_key_here"
```

```python
from certaintylabs import Certainty

# Uses CERTAINTY_BASE_URL and CERTAINTY_API_KEY from the environment
client = Certainty()
client.health()
```

You can still pass `base_url` or `api_key` explicitly; those override the environment.

- **Local dev:** Omit both; the client defaults to `http://localhost:8000` and no key.
- **Your own server:** Set `CERTAINTY_BASE_URL` (and optionally `CERTAINTY_API_KEY`) in your deployment config.
- **Certainty-hosted API:** Set both env vars as provided in your dashboard.

## Data options

| Option | SDK / API |
|--------|-----------|
| **Built-in dataset** | `train(epochs=10)` with no data → uses GSM8K |
| **Your data** | `train_with_data(samples)` or `train_from_file("path.jsonl")` or `train(data=...)` |
| **Rerank** | `rerank(candidates, prompt=...)` or have the API generate candidates: `rerank(prompt=..., openai_api_key=..., n_candidates=5)` |

### Generating your own data externally

Training data must be **EORM format**: one JSON object per line with `question`, `label` (0 or 1), and `gen_text`. Create this data with your own pipeline (e.g. your LLM + your labeling rules or model-as-judge). Save as `.jsonl` and use `train_from_file(path)` or send the list to `train(data=...)`.

## API Reference

### `Certainty(base_url=None, api_key=None, timeout=300.0)`

| Parameter  | Type            | Default                  |
|------------|-----------------|--------------------------|
| `base_url` | `str` or `None` | `None` → env `CERTAINTY_BASE_URL` or `"http://localhost:8000"` |
| `api_key`  | `str` or `None` | `None` → env `CERTAINTY_API_KEY` or no auth |
| `timeout`  | `float`         | `300.0`                  |

### Methods

#### `client.health() -> HealthResponse`

Returns API status and version.

#### Using your own data

You can train on in-memory data or a local JSONL file instead of server-side data.

**In-memory:** each record is a dict with `question`, `label`, and `gen_text` (EORM format).

```python
samples = [
    {"question": "What is 2+2?", "label": 1, "gen_text": "The answer is 4."},
    {"question": "What is 3*3?", "label": 1, "gen_text": "The answer is 9."},
]
result = client.train_with_data(samples, epochs=10)
```

**Local file:** one JSON object per line (same keys).

```python
result = client.train_from_file("my_data.jsonl", epochs=15, lr=1e-4)
```

**Low-level:** pass `data=...` or `data_path=...` into `client.train()` for full control.

#### Tuning training parameters

Override defaults via keyword arguments or a `TrainingParams` object (omit fields to keep API defaults):

```python
from certaintylabs import Certainty, TrainingParams

client = Certainty()

# Via kwargs
result = client.train(epochs=15, batch_size=2, lr=1e-4, max_length=1024)

# Via TrainingParams (good for reusing a config)
params = TrainingParams(epochs=15, batch_size=2, lr=1e-4, validate_every=2)
result = client.train(training_params=params)
# Or with your own data
result = client.train_with_data(samples, training_params=params)
```

`TrainingParams` supports: `epochs`, `batch_size`, `d_model`, `n_heads`, `n_layers`, `lr`, `max_length`, `validate_every`, `val_holdout`.

#### Rerank with your own model to generate candidates

You can either pass pre-generated candidates or have the API **generate candidates with your LLM** and then rerank them in one call. Use your own base model API (OpenAI, Claude, Llama, etc.) for generation:

```python
# Option A: You provide candidates (e.g. from your own LLM elsewhere)
best = client.rerank(
    candidates=["answer A", "answer B", "answer C"],
    prompt="What is 2+2?",
)

# Option B: API generates n_candidates with your LLM, then reranks
best = client.rerank(
    prompt="What is 2+2?",
    openai_api_key="sk-...",
    openai_model="gpt-4o-mini",
    openai_base_url="https://api.openai.com/v1",
    n_candidates=5,
)
print(best.best_candidate)  # best of the 5 generated answers
```

#### `client.train(**kwargs) -> TrainResponse`

Train a TransEBM. Data source: `data` (list of records), `data_path` (server path), or neither (built-in GSM8K). Key parameters:

| Parameter         | Type            | Default   |
|-------------------|-----------------|-----------|
| `yaml_content`    | `str` or `None` | `None`    |
| `data_path`       | `str` or `None` | `None`    |
| `data`            | list of dicts   | `None`    |
| `epochs`          | `int`           | `20`      |
| `d_model`         | `int`           | `768`     |
| `n_heads`         | `int`           | `4`       |
| `n_layers`        | `int`           | `2`       |
| `lr`              | `float`         | `5e-5`    |
| `max_length`      | `int`           | `2048`    |
| `training_params` | `TrainingParams` or `None` | `None` |

```python
result = client.train(data_path="path/to/gsm8k.jsonl", epochs=10)
print(result.model_path)     # "./certainty_workspace/model/..."
print(result.best_val_acc)   # 0.85
```

#### `client.rerank(...) -> RerankResponse`

Rerank LLM outputs using a trained TransEBM. Either pass **candidates** you already have, or omit candidates and set **openai_api_key** (and optionally **openai_model**, **openai_base_url**) so the API generates **n_candidates** with your LLM and then reranks them.

| Parameter          | Type            | Default |
|--------------------|-----------------|---------|
| `candidates`       | `List[str]` or `None` | `None` (use with `openai_api_key` to generate) |
| `prompt`           | `str`           | `""`    |
| `model_path`       | `str`           | `"./certainty_workspace/model/ebm_certainty_model.pt"` |
| `tokenizer_path`   | `str` or `None` | `None`  |
| `openai_api_key`   | `str` or `None` | `None`  |
| `openai_model`     | `str` or `None` | `None`  |
| `openai_base_url`  | `str` or `None` | `None`  |
| `n_candidates`     | `int`           | `5` (only used when generating via your API) |

```python
best = client.rerank(
    candidates=["answer A", "answer B", "answer C"],
    prompt="What is 2+2?",
)
print(best.best_candidate)  # the highest-scored candidate
print(best.all_energies)    # energy scores for each candidate
```

#### `client.pipeline(**kwargs) -> PipelineResponse`

Run train (on your data or built-in) then optionally rerank. Pass `data` or `data_path` to use your data; omit for built-in. Pass `candidates` to rerank after training.

```python
result = client.pipeline(epochs=10, candidates=["answer A", "answer B"])
print(result.train.best_val_acc)
if result.rerank:
    print(result.rerank.best_candidate)
```

## Error Handling

```python
from certaintylabs import Certainty, APIError, ConnectionError

client = Certainty()

try:
    client.compile("invalid yaml: [[[")
except APIError as e:
    print(e.status_code)  # 400
    print(e.detail)       # error message from the server

try:
    client = Certainty(base_url="http://localhost:9999")
    client.health()
except ConnectionError as e:
    print(e)  # "Could not connect to http://localhost:9999: ..."
```

## License

MIT

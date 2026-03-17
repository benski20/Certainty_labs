# Certainty Labs API — Modal GPU setup

Run the Certainty Labs API on [Modal](https://modal.com) with a GPU. No VM management: deploy from your repo and get a URL. Training and inference use the GPU automatically.

---

## 1. Prerequisites

- **Modal account** — sign up at [modal.com](https://modal.com).
- **Modal CLI** — install and log in:

```bash
pip install modal
modal token new
```

Follow the prompts (browser auth). Your machine is then linked to your Modal workspace.

---

## 2. Deploy the API

From the **project root** (where `modal_app.py` and `requirements.txt` are):

```bash
modal deploy modal_app.py
```

Modal builds an image (installs PyTorch + CUDA and `requirements.txt`), **bakes your repo into the image (production-safe)**, and deploys the FastAPI app. When it finishes, it prints a URL like:

```text
https://your-workspace--certainty-labs-api.modal.run
```

That URL is your API base. Use it as `CERTAINTY_BASE_URL` for the SDK, tests, or frontend.

---

## 3. Verify

```bash
curl https://your-workspace--certainty-labs-api.modal.run/health
# Expect: {"status":"ok","version":"0.1.0"}
```

```bash
curl https://your-workspace--certainty-labs-api.modal.run/
# Expect: {"service":"Certainty Labs API","docs":"/docs","health":"/health"}
```

---

## 4. Run integration tests

From the repo root:

```bash
export CERTAINTY_BASE_URL=https://your-workspace--certainty-labs-api.modal.run
python3 -m pytest tests/test_sdk_api_integration.py -v --tb=short
```

The first request may take 30–60 seconds (cold start); later requests are faster.

---

## 5. Optional: environment secrets (Supabase, etc.)

If your API needs `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, or other env vars:

1. In the [Modal dashboard](https://modal.com/secrets), create a **Secret** (e.g. name `certainty-env`) and add the key/value pairs.
2. In `modal_app.py`, attach the secret to the function:

```python
@app.function(
    gpu="T4",
    timeout=3600,
    allow_concurrent_inputs=10,
    secrets=[modal.Secret.from_name("certainty-env")],
)
@modal.asgi_app(label="certainty-labs-api")
def web():
    ...
```

Redeploy with `modal deploy modal_app.py`.

---

## 6. Persistence (production)

`modal_app.py` mounts a **Modal Volume** at `/app/certainty_workspace` so these survive container restarts:

- trained model checkpoints under `certainty_workspace/model/`
- local API key store `certainty_workspace/api_keys.json` (when Supabase is not configured)

This avoids “works only locally / lost on restart” behavior.

---

## 7. Optional: different GPU or longer timeout

Edit `modal_app.py`:

- **GPU:** Change `gpu="T4"` to e.g. `gpu="A10"`, `gpu="L4"`, or `gpu="A100"` (see [Modal GPU options](https://modal.com/docs/guide/gpu)).
- **Timeout:** Increase `timeout=3600` (seconds) if training runs longer.

Redeploy after changes.

---

## 8. Local development (ephemeral endpoint)

Run the app once; Modal prints a temporary URL that stops when you press Ctrl+C:

```bash
modal run modal_app.py
```

Useful for quick checks; for a stable URL use `modal deploy modal_app.py`.

---

## Quick reference

| Step | Command / action |
|------|-------------------|
| 1 | `pip install modal` and `modal token new` |
| 2 | `modal deploy modal_app.py` → note the URL |
| 3 | `curl <URL>/health` |
| 4 | `CERTAINTY_BASE_URL=<URL> pytest tests/test_sdk_api_integration.py -v` |
| Secrets | Create secret in dashboard, add `secrets=[modal.Secret.from_name("...")]` to `@app.function` |

---

## How it works

- **`modal_app.py`** defines a Modal app that:
  - Builds an image with Python 3.10, PyTorch (CUDA 11.8), and `requirements.txt`.
  - **Copies** your project into the image at `/app` (so `api` and `certainty` are importable).
  - Serves `api.main:app` (your FastAPI app) behind an ASGI endpoint with a **T4** GPU.
- **Training** (`POST /train`) and **inference** (e.g. `/score`, `/rerank`) run on that GPU. No VM or SSH; Modal scales and bills on use.

## Persistence

Trained models are written to `certainty_workspace/` and are persisted via a Modal Volume.

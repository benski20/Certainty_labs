"""
Certainty Labs API on Modal (GPU).

Deploy:
  modal deploy modal_app.py

Run once (ephemeral):
  modal run modal_app.py

Then use the deployed URL as CERTAINTY_BASE_URL (e.g. for tests or frontend).
"""

from __future__ import annotations

import os
import sys

import modal

# Image: install deps from requirements.txt (with PyTorch CUDA), then mount app code at /app.
REQUIREMENTS = "requirements.txt"

image = (
    modal.Image.debian_slim(python_version="3.10")
    .add_local_file(REQUIREMENTS, "/tmp/requirements.txt", copy=True)
    .run_commands(
        "pip install torch --index-url https://download.pytorch.org/whl/cu118",
        "pip install -r /tmp/requirements.txt",
    )
    .add_local_dir(
        ".",
        "/app",
        # Production: bake code into the image so nothing depends on local files at runtime.
        copy=True,
        ignore=[
            ".venv",
            "__pycache__",
            ".git",
            "*.pyc",
            "certainty_workspace",
            "platform",
            "node_modules",
            ".pytest_cache",
            "*.egg-info",
        ],
    )
    .env({"PYTHONPATH": "/app"})
)

app = modal.App("certainty-labs-api", image=image)

# Persist models + API keys across container restarts.
# - `certainty_workspace/model/*` (trained checkpoints)
# - `certainty_workspace/api_keys.json` (local key store, if Supabase not configured)
workspace_volume = modal.Volume.from_name("certainty-workspace", create_if_missing=True)


@app.function(
    gpu="T4",
    timeout=3600,
    allow_concurrent_inputs=10,
    volumes={"/app/certainty_workspace": workspace_volume},
)
@modal.asgi_app(label="certainty-labs-api")
def web():
    """Serve the Certainty Labs FastAPI app on GPU (T4). Training and inference use the GPU."""
    # Ensure app code is on path (mount is at /app)
    sys.path.insert(0, "/app")
    os.chdir("/app")

    from api.main import app as fastapi_app

    return fastapi_app

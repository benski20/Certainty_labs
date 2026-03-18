"""
Certainty Labs API on Modal (GPU).

Deploy:
  modal deploy modal_app.py

Run once (ephemeral):
  modal run modal_app.py

Then use the deployed URL as CERTAINTY_BASE_URL (e.g. for tests or frontend).

GPU: Default from MODAL_GPU env var. Users can pass gpu="A10" etc. in train() for runtime selection.
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
workspace_volume = modal.Volume.from_name("certainty-workspace", create_if_missing=True)

# Default GPU for deployment (MODAL_GPU env var). Used when user doesn't specify gpu in train().
DEFAULT_GPU = os.environ.get("MODAL_GPU", "A10")


@app.cls(
    gpu=DEFAULT_GPU,
    timeout=3600,
    volumes={"/app/certainty_workspace": workspace_volume},
)
class Trainer:
    """Runs training on a specific GPU. Use with_options(gpu="A100") for runtime GPU selection."""

    @modal.method()
    def run_train(self, req_dict: dict) -> dict:
        """Execute training. req_dict is the TrainRequest as a dict."""
        sys.path.insert(0, "/app")
        os.chdir("/app")

        from certainty.pipeline import CertaintyPipeline
        from certainty.models.trainer import TrainingConfig

        def _resolve_tokenizer(name: str | None) -> str:
            if not name:
                return "gpt2"
            from certainty.models.supported_models import resolve_tokenizer_name
            return resolve_tokenizer_name(name)

        pipeline = CertaintyPipeline()
        if req_dict.get("data") is not None:
            pipeline.load_data_records(req_dict["data"])
        elif req_dict.get("data_path"):
            pipeline.load_data(req_dict["data_path"])

        config = TrainingConfig(
            tokenizer_name=_resolve_tokenizer(req_dict.get("tokenizer_name")),
            epochs=req_dict.get("epochs", 20),
            batch_size=req_dict.get("batch_size", 1),
            d_model=req_dict.get("d_model", 768),
            n_heads=req_dict.get("n_heads", 4),
            n_layers=req_dict.get("n_layers", 2),
            lr=req_dict.get("lr", 5e-5),
            max_length=req_dict.get("max_length", 2048),
            validate_every=req_dict.get("validate_every", 1),
            val_holdout=req_dict.get("val_holdout", 0.2),
        )
        return pipeline.train(config=config)


@app.function(
    gpu=DEFAULT_GPU,
    timeout=3600,
    allow_concurrent_inputs=10,
    volumes={"/app/certainty_workspace": workspace_volume},
)
@modal.asgi_app(label="certainty-labs-api")
def web():
    """Serve the Certainty Labs FastAPI app on GPU. Training spawns on user-specified GPU."""
    sys.path.insert(0, "/app")
    os.chdir("/app")
    os.environ["CERTAINTY_MODAL"] = "1"

    from api.main import app as fastapi_app

    return fastapi_app

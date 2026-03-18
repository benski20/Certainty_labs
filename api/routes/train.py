"""Train a TransEBM energy model on your data or the built-in dataset."""

import asyncio
import os

from fastapi import APIRouter, HTTPException

from api.schemas import TrainRequest, TrainResponse

router = APIRouter()

# GPU types supported by Modal for runtime selection
_VALID_GPUS = frozenset({"T4", "L4", "A10", "A100", "L40S", "H100", "H200", "B200"})


def _resolve_tokenizer(name: str | None) -> str:
    if not name:
        return "gpt2"
    from certainty.models.supported_models import resolve_tokenizer_name
    return resolve_tokenizer_name(name)


async def _train_via_modal(req: TrainRequest, gpu: str) -> dict:
    """Spawn Modal Trainer with requested GPU and run training."""
    from modal_app import Trainer, DEFAULT_GPU, workspace_volume

    target_gpu = gpu if gpu in _VALID_GPUS else DEFAULT_GPU
    req_dict = req.model_dump(exclude={"gpu"})

    trainer_cls = Trainer.with_options(
        gpu=target_gpu,
        volumes={"/app/certainty_workspace": workspace_volume},
    )
    # Run in thread pool to avoid blocking (remote() is sync)
    return await asyncio.to_thread(
        trainer_cls().run_train.remote,
        req_dict,
    )


@router.post("/train", response_model=TrainResponse)
async def train_model(req: TrainRequest):
    try:
        if os.environ.get("CERTAINTY_MODAL"):
            from modal_app import DEFAULT_GPU
            gpu = (req.gpu or DEFAULT_GPU).upper()
            metrics = await _train_via_modal(req, gpu)
        else:
            metrics = await _train_inline(req)

        return TrainResponse(
            model_path=metrics["model_path"],
            best_val_acc=metrics["best_val_acc"],
            epochs_trained=metrics["epochs_trained"],
            elapsed_seconds=metrics["elapsed_seconds"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _train_inline(req: TrainRequest) -> dict:
    """Run training inline (same container as web app)."""
    from certainty.pipeline import CertaintyPipeline
    from certainty.models.trainer import TrainingConfig

    pipeline = CertaintyPipeline()
    if req.data is not None:
        pipeline.load_data_records(req.data)
    elif req.data_path:
        pipeline.load_data(req.data_path)

    train_config = TrainingConfig(
        tokenizer_name=_resolve_tokenizer(req.tokenizer_name),
        epochs=req.epochs,
        batch_size=req.batch_size,
        d_model=req.d_model,
        n_heads=req.n_heads,
        n_layers=req.n_layers,
        lr=req.lr,
        max_length=req.max_length,
        validate_every=req.validate_every,
        val_holdout=req.val_holdout,
    )
    # Run in thread pool so we don't block the event loop
    return await asyncio.to_thread(pipeline.train, config=train_config)

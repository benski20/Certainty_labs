"""Train a TransEBM energy model on your data or the built-in dataset."""

from fastapi import APIRouter, HTTPException

from api.schemas import TrainRequest, TrainResponse

router = APIRouter()


def _resolve_tokenizer(name: str | None) -> str:
    if not name:
        return "gpt2"
    from certainty.models.supported_models import resolve_tokenizer_name
    return resolve_tokenizer_name(name)


@router.post("/train", response_model=TrainResponse)
async def train_model(req: TrainRequest):
    from certainty.pipeline import CertaintyPipeline
    from certainty.models.trainer import TrainingConfig

    try:
        pipeline = CertaintyPipeline()

        if req.data is not None:
            pipeline.load_data_records(req.data)
        elif req.data_path:
            pipeline.load_data(req.data_path)
        # else: trainer uses built-in GSM8K dataset

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
        metrics = pipeline.train(config=train_config)

        return TrainResponse(
            model_path=metrics["model_path"],
            best_val_acc=metrics["best_val_acc"],
            epochs_trained=metrics["epochs_trained"],
            elapsed_seconds=metrics["elapsed_seconds"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

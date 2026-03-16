"""Pipeline: train on your data (or built-in) then optionally rerank."""

from fastapi import APIRouter, HTTPException

from api.schemas import PipelineRequest, PipelineResponse, RerankResponse, TrainResponse

router = APIRouter()


def _resolve_tokenizer(name: str | None) -> str:
    if not name:
        return "gpt2"
    from certainty.models.supported_models import resolve_tokenizer_name
    return resolve_tokenizer_name(name)


@router.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline(req: PipelineRequest):
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
        train_resp = TrainResponse(
            model_path=metrics["model_path"],
            best_val_acc=metrics["best_val_acc"],
            epochs_trained=metrics["epochs_trained"],
            elapsed_seconds=metrics["elapsed_seconds"],
        )

        rerank_resp = None
        if req.candidates:
            best, best_idx, energies = pipeline.rerank(req.candidates, "")
            rerank_resp = RerankResponse(
                best_candidate=best,
                best_index=best_idx,
                all_energies=energies,
            )

        return PipelineResponse(train=train_resp, rerank=rerank_resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""Pipeline: train on your data (or built-in) then optionally rerank."""

from fastapi import APIRouter, HTTPException

from api.schemas import PipelineRequest, PipelineResponse, RerankResponse, TrainRequest, TrainResponse

router = APIRouter()


@router.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline(req: PipelineRequest):
    from api.routes.train import train_model
    from certainty.pipeline import CertaintyPipeline

    try:
        train_req = TrainRequest(
            data_path=req.data_path,
            data=req.data,
            tokenizer_name=req.tokenizer_name,
            gpu=req.gpu,
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
        train_resp = await train_model(train_req)

        rerank_resp = None
        if req.candidates:
            pipeline = CertaintyPipeline()
            pipeline.load_model(train_resp.model_path)
            best, best_idx, energies = pipeline.rerank(req.candidates, "")
            rerank_resp = RerankResponse(
                best_candidate=best,
                best_index=best_idx,
                all_energies=energies,
            )

        return PipelineResponse(train=train_resp, rerank=rerank_resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""Rerank LLM candidate outputs with a trained TransEBM; score outputs for verifiable/interpretable AI (logging, audit)."""

import os

from fastapi import APIRouter, HTTPException

from api.schemas import RerankRequest, RerankResponse, ScoreRequest, ScoreResponse

router = APIRouter()


@router.post("/rerank", response_model=RerankResponse)
async def rerank(req: RerankRequest):
    from certainty.inference.reranker import ConstraintReranker
    from certainty.data.sampler import OpenAISampler, HuggingFaceInferenceSampler
    from certainty.models.supported_models import resolve_tokenizer_name

    candidates = list(req.candidates) if req.candidates else []

    if not candidates and (req.openai_api_key or (req.hf_model and req.hf_token)):
        if req.hf_model and req.hf_token:
            model_id = resolve_tokenizer_name(req.hf_model)
            sampler = HuggingFaceInferenceSampler(model_id=model_id, token=req.hf_token)
            candidates = sampler.sample(req.prompt, n=max(1, req.n_candidates), temperature=0.9)
        else:
            sampler = OpenAISampler(
                model=req.openai_model or "gpt-4o",
                api_key=req.openai_api_key,
                base_url=req.openai_base_url,
            )
            candidates = sampler.sample(req.prompt, n=max(1, req.n_candidates), temperature=0.9)
    if not candidates:
        raise HTTPException(
            status_code=400,
            detail="Provide non-empty candidates, or set openai_api_key or (hf_model + hf_token) to generate candidates.",
        )

    if not os.path.exists(req.model_path):
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_path}")

    try:
        reranker = ConstraintReranker(
            model_path=req.model_path, tokenizer_path=req.tokenizer_path
        )
        best, best_idx, energies = reranker.rerank(candidates, req.prompt)
        return RerankResponse(
            best_candidate=best,
            best_index=best_idx,
            all_energies=energies,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score", response_model=ScoreResponse)
async def score_outputs(req: ScoreRequest):
    """Return EBM energy scores for given outputs. Use for logging, confidence tracking, and audit (verifiable/interpretable AI). Lower energy = higher confidence / more constraint-satisfying."""
    from certainty.inference.reranker import ConstraintReranker

    if not req.texts:
        raise HTTPException(status_code=400, detail="texts must be a non-empty list of strings.")

    if not os.path.exists(req.model_path):
        raise HTTPException(status_code=404, detail=f"Model not found: {req.model_path}")

    try:
        reranker = ConstraintReranker(
            model_path=req.model_path,
            tokenizer_path=req.tokenizer_path,
        )
        energies = reranker.score_all(req.texts, req.prompt)
        return ScoreResponse(energies=energies)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

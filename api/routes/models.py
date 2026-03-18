"""Model download endpoint — bundle model.pt and tokenizer for reuse."""

import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from fastapi.responses import StreamingResponse

router = APIRouter()

# Resolve workspace root (same as Modal mount)
_WORKSPACE = Path("/app/certainty_workspace")
if not _WORKSPACE.exists():
    _WORKSPACE = Path("./certainty_workspace").resolve()


def _derive_tokenizer_path(model_path: str) -> Path:
    """ebm_certainty_model.pt -> ebm_certainty_tokenizer"""
    p = Path(model_path)
    stem = p.stem  # ebm_certainty_model
    if stem.endswith("_model"):
        base = stem[:-6]  # ebm_certainty
    else:
        base = stem
    return p.parent / f"{base}_tokenizer"


@router.get("/models/download")
async def download_model(
    path: str = Query(..., description="Server path to model.pt (e.g. ./certainty_workspace/model/ebm_certainty_model.pt)"),
):
    """Download trained model and tokenizer as a zip for local reuse."""
    # Resolve and validate path
    resolved = Path(path).resolve()
    workspace_model = (_WORKSPACE / "model").resolve()

    # Ensure path is under certainty_workspace/model/
    try:
        resolved.relative_to(workspace_model)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Model path must be under certainty_workspace/model/. Got: {path}",
        )

    if not resolved.exists():
        raise HTTPException(status_code=404, detail=f"Model not found: {path}")

    tokenizer_path = _derive_tokenizer_path(str(resolved))
    if not tokenizer_path.exists():
        tokenizer_path = None

    # Build zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(resolved, "model.pt")
        if tokenizer_path and tokenizer_path.is_dir():
            for fp in tokenizer_path.rglob("*"):
                if fp.is_file():
                    arcname = f"tokenizer/{fp.relative_to(tokenizer_path)}"
                    zf.write(fp, arcname)

        # Include metrics if present
        metrics_path = resolved.parent / f"{resolved.stem.replace('_model', '')}_metrics.json"
        if not metrics_path.exists():
            metrics_path = resolved.parent / "ebm_certainty_metrics.json"
        if metrics_path.exists():
            zf.write(metrics_path, "metrics.json")

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=certainty_model.zip"},
    )

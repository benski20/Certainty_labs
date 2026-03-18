"""Certainty Labs API -- FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

from fastapi import Depends, FastAPI, Request

# Load .env from project root (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, etc.)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.auth import require_api_key
from api.schemas import HealthResponse
from api.routes import train, infer, pipeline, keys, models, usage
from api.usage_meter import path_to_endpoint, record_usage


@asynccontextmanager
async def lifespan(app: FastAPI):
    (_PROJECT_ROOT / "certainty_workspace").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Certainty Labs API",
    version="0.1.0",
    description=(
        "Train TransEBM energy models on your own data and rerank LLM outputs "
        "for constraint-correct responses. Bring your own EORM-format data or use the built-in dataset."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def usage_metering_middleware(request, call_next):
    """Record usage for successful requests to metered endpoints."""
    response = await call_next(request)
    if 200 <= response.status_code < 300 and hasattr(request.state, "key_id"):
        endpoint = path_to_endpoint(request.url.path)
        if endpoint:
            try:
                record_usage(request.state.key_id, endpoint)
            except Exception:
                pass  # Don't fail the request if metering fails
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error_type": type(exc).__name__},
    )


# Root: so Render/default health checks (GET /) get 200 instead of 404
@app.get("/")
async def root():
    return {"service": "Certainty Labs API", "docs": "/docs", "health": "/health"}


# Public routes (no auth required)
app.include_router(keys.router, tags=["api-keys"])

# Protected routes (auth required when API keys exist)
_auth = [Depends(require_api_key)]
app.include_router(train.router, tags=["train"], dependencies=_auth)
app.include_router(infer.router, tags=["inference"], dependencies=_auth)
app.include_router(pipeline.router, tags=["pipeline"], dependencies=_auth)
app.include_router(models.router, tags=["models"], dependencies=_auth)
app.include_router(usage.router, tags=["usage"], dependencies=_auth)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")

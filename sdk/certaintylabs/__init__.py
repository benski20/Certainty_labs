"""Certainty Labs Python SDK."""

from certaintylabs.async_client import AsyncCertainty
from certaintylabs.client import Certainty
from certaintylabs.exceptions import APIError, CertaintyError, ConnectionError, TimeoutError
from certaintylabs.types import (
    HealthResponse,
    PipelineResponse,
    RerankResponse,
    ScoreResponse,
    TrainResponse,
    TrainingParams,
)

__all__ = [
    "Certainty",
    "AsyncCertainty",
    "CertaintyError",
    "APIError",
    "ConnectionError",
    "TimeoutError",
    "HealthResponse",
    "TrainResponse",
    "TrainingParams",
    "RerankResponse",
    "ScoreResponse",
    "PipelineResponse",
]

__version__ = "0.1.1"

# Enable verbose logs: logging.getLogger("certaintylabs").setLevel(logging.DEBUG)

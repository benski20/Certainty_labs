"""Exception types for the Certainty SDK."""

from __future__ import annotations

from typing import Optional


class CertaintyError(Exception):
    """Base exception for all Certainty SDK errors."""


class APIError(CertaintyError):
    """The API returned a non-2xx response."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_type: Optional[str] = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_type = error_type
        msg = f"[{status_code}] {detail}"
        if error_type:
            msg = f"[{status_code}] {error_type}: {detail}"
        super().__init__(msg)


class ConnectionError(CertaintyError):
    """Could not connect to the Certainty API server."""

    def __init__(self, base_url: str, cause: Optional[Exception] = None):
        self.base_url = base_url
        self.cause = cause
        super().__init__(f"Could not connect to {base_url}: {cause}")


class TimeoutError(CertaintyError):
    """The request timed out."""

    def __init__(self, timeout: float, endpoint: str):
        self.timeout = timeout
        self.endpoint = endpoint
        super().__init__(
            f"Request to {endpoint} timed out after {timeout}s. "
            f"Training can be slow — try increasing timeout."
        )

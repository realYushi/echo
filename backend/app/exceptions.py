from __future__ import annotations


class AppError(Exception):
    """Base application error with structured error info."""

    def __init__(self, message: str, code: str, status_code: int = 500) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, "NOT_FOUND", 404)


class ValidationError(AppError):
    """Business rule violation (422). Not for input parsing — Pydantic handles that."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR", 422)


class ExternalServiceError(AppError):
    """External service failure (502). Use for Claude API, Qdrant, or CLIP failures."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__(f"{service}: {message}", "EXTERNAL_ERROR", 502)

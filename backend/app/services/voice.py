from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.exceptions import ExternalServiceError

if TYPE_CHECKING:
    from app.config import Settings

logger = structlog.get_logger(__name__)


async def create_ephemeral_token(*, settings: Settings) -> tuple[str, str]:
    """Create a Gemini ephemeral token for Live API WebSocket connection.

    Returns (token_string, model_name).
    """
    if not settings.gemini_api_key:
        raise ExternalServiceError("gemini", "Gemini API key is not configured")

    try:
        from datetime import UTC, datetime, timedelta

        from google import genai  # late import: only needed at call time

        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={"api_version": "v1alpha"},
        )

        model = settings.gemini_live_model
        now = datetime.now(tz=UTC)
        expire_time = now + timedelta(minutes=5)

        response = client.auth_tokens.create(
            config={
                "uses": 1,
                "expire_time": expire_time.isoformat(),
                "new_session_expire_time": (now + timedelta(minutes=2)).isoformat(),
                "live_connect_constraints": {"model": model},
            },
        )

        token: str = response.name
        await logger.ainfo("gemini_ephemeral_token_created", model=model)
        return token, model

    except ExternalServiceError:
        raise
    except Exception as exc:
        await logger.aerror("gemini_token_creation_failed", error=str(exc))
        raise ExternalServiceError("gemini", f"Failed to create ephemeral token: {exc}") from exc

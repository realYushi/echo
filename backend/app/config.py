from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/echo"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "products"
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    gemini_live_model: str = "gemini-3.1-flash-live-preview"
    anthropic_model: str = "claude-3-5-sonnet-latest"
    anthropic_post_process_model: str = "claude-haiku-4-20250414"
    clip_model: str = "ViT-B-32"
    recommendation_limit: int = 6
    recommendation_score_threshold: float = 0.45
    min_recommendation_signals: int = 2
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

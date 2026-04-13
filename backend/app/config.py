from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/echo"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "products"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-latest"
    clip_model: str = "ViT-B-32"
    recommendation_limit: int = 6
    recommendation_score_threshold: float = 0.45
    min_recommendation_signals: int = 2
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

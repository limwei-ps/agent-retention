"""Application settings, loaded from the environment via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central config. Values come from env vars / `.env` (see `.env.example`)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Time Internet Retention API"
    app_timezone: str = "Asia/Kuala_Lumpur"

    # Data
    database_url: str = "sqlite:///./retention.db"

    # LLM — mock-first; real Gemini behind the flag (see spec §4.9)
    llm_mode: str = "mock"  # "mock" | "gemini"
    gemini_api_key: str | None = None
    gemini_model_primary: str = "gemini-2.5-pro"
    gemini_model_secondary: str = "gemini-2.5-flash"

    # Streaming pace: 0 in tests; a small delay in dev makes the mock stream visibly (spec §4.10).
    sse_token_chunk_delay_ms: int = 0

    # Bulk generation backpressure (spec §4.5)
    bulk_concurrency: int = 4


settings = Settings()

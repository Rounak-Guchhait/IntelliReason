from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "IntelliReason"
    app_env: str = "development"
    log_level: str = "INFO"
    max_steps: int = 8

    # LLM provider
    llm_provider: str = "groq"  # groq | google | openai | openai_compatible
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.2

    groq_api_key: str | None = None
    google_api_key: str | None = None
    openai_api_key: str | None = None
    llm_base_url: str | None = None

    # Vector store
    vector_store: str = "memory"  # memory | pgvector
    ingestion_dir: str = "knowledge_docs"
    database_url: str | None = None

    # Code-execution sandbox (external, free APIs)
    piston_url: str = "https://emkc.org/api/v2/piston"
    judge0_url: str = ""
    judge0_api_key: str | None = None
    code_engine: str = "piston"  # piston | judge0

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
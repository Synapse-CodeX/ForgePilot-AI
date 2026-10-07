from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "ForgePilot AI"
    app_env: str = "development"
    debug: bool = True

    api_prefix: str = "/api"

    groq_api_key: str = ""
    github_token: str = ""

    database_url: str = "sqlite:///./forgepilot.db"
    vector_store_path: str = "./data/vectorstore"

    max_agent_iterations: int = 3
    sandbox_timeout: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()

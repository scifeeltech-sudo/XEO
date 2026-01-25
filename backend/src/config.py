"""Application configuration."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_env: str = "development"
    app_debug: bool = True

    # Sela API
    sela_api_base_url: str = ""
    sela_api_key: str = ""
    sela_principal_id: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""

    # OpenAI
    openai_api_key: str = ""

    # Anthropic (Claude API for polish)
    anthropic_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS (comma-separated origins for production)
    cors_origins: str = "*"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

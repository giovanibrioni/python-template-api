from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings. Environment variables override the .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "python-template"
    environment: str = "local"
    log_level: str = "INFO"
    log_json: bool = False
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    otel_service_name: str = "python-template"
    otel_exporter_otlp_endpoint: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()

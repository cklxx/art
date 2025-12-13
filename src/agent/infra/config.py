"""Configuration model for the agent stack."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    openrouter_model: str = "openrouter/auto"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_referer: str | None = None
    openrouter_title: str | None = None
    google_api_key: str | None = None
    google_model: str = "gemini-1.5-flash"
    google_image_model: str = "imagen-3.5-flash"
    state_db_path: str = ":memory:"
    state_log_path: str = ".data/state_log.jsonl"
    object_store_path: str = ".data/object_store"
    model_config = SettingsConfigDict(env_file=".env")


def load_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

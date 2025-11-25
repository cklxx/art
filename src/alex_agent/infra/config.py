"""Configuration model for the agent stack."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    google_api_key: str | None = None
    google_model: str = "gemini-1.5-flash"
    google_image_model: str = "imagen-3.5-flash"
    supabase_url: str | None = None
    supabase_key: str | None = None
    model_config = SettingsConfigDict(env_file=".env")


def load_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

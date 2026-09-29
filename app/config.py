from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FitBuddy – AI Fitness Plan Generator"
    database_url: str = "sqlite:///./data/fitbuddy.db"
    gemini_api_key: str | None = None
    gemini_workout_model: str = "gemini-3.1-pro-preview"
    gemini_flash_model: str = "gemini-3.8-flash"
    ai_enabled: bool = True
    admin_token: str = "change-me"
    max_feedback_length: int = 1000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

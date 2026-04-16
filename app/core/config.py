import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:QYgkiqCSPhykgsPfYRMkkrPrZMsVyhkG@nozomi.proxy.rlwy.net:49544/railway",
    )
    APP_NAME: str = "Drug Interaction Tracker"
    DEBUG: bool = True
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

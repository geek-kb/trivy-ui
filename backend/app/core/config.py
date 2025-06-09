# File: backend/app/core/config.py

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment settings
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "").lower() == "true"

    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "trivy-ui"

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]

    # Storage settings
    DB_BACKEND: str = os.getenv("DB_BACKEND", "filesystem")

    # PostgreSQL settings (only used if DB_BACKEND is "postgres")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "trivy")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # Optional timezone setting
    TIMEZONE: Optional[str] = os.getenv("TIMEZONE")

    class Config:
        case_sensitive = True


settings = Settings()


def get_settings() -> Settings:
    """Return the settings instance."""
    return settings

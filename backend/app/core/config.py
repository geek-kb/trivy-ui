# File: backend/app/core/config.py

import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings

# Load environment variables from .env file first
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

class Settings(BaseSettings):
    ENV: str = "development"
    UVICORN_HOST: str = "0.0.0.0"
    UVICORN_PORT: int = 8000
    DB_BACKEND: str = ""  # filesystem, sqlite, postgres
    FILESYSTEM_STORAGE_DIR: str = "backend/app/storage/reports"
    SQLITE_PATH: str = "backend/trivy_ui.db"
    POSTGRES_URL: str = ""
    TIMEZONE: str = ""

    class Config:
        extra = "ignore"  # Allow extra env vars without throwing validation errors

# Initialize settings
settings = Settings()

# Shortcut variables for easier imports elsewhere
DB_BACKEND = settings.DB_BACKEND.lower()
FILESYSTEM_REPORTS_DIR = Path(settings.FILESYSTEM_STORAGE_DIR)
SQLITE_PATH = settings.SQLITE_PATH
POSTGRES_URL = settings.POSTGRES_URL
TIMEZONE = settings.TIMEZONE

# backend/app/core/database.py

import os
from typing import Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)

from app.core.config import DB_BACKEND, POSTGRES_URL, SQLITE_PATH

# --- Global variables ---
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None

# --- Database Initialization ---


def init_db_engine():
    global engine, async_session_factory

    db_backend = DB_BACKEND.lower()

    if db_backend == "postgres":
        if not POSTGRES_URL:
            raise ValueError("POSTGRES_URL is required for Postgres backend")
        engine = create_async_engine(POSTGRES_URL, echo=False)

    elif db_backend == "sqlite":
        if not SQLITE_PATH:
            raise ValueError("SQLITE_PATH is required for SQLite backend")
        engine = create_async_engine(
            f"sqlite+aiosqlite:///{SQLITE_PATH}",
            echo=False,
        )

    else:
        # Filesystem backend: no database connection needed
        engine = None
        async_session_factory = None
        return

    async_session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


def get_session() -> AsyncSession:
    if async_session_factory is None:
        raise RuntimeError(
            "Database session requested but DB_BACKEND is not a database backend"
        )
    return async_session_factory()

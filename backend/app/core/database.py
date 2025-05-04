# backend/app/core/database.py

import os
from typing import Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import DB_BACKEND, POSTGRES_URL, SQLITE_PATH

# --- Global variables ---
Base = declarative_base()
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None
from app.core.config import DB_BACKEND, POSTGRES_URL, SQLITE_PATH

# --- Global variables ---
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None

# --- Database Initialization ---


def get_cluster_domain(resolv_conf_path="/etc/resolv.conf") -> str:
    try:
        with open(resolv_conf_path, "r") as f:
            for line in f:
                if line.startswith("search"):
                    words = line.strip().split()
                    if len(words) > 1:
                        return words[-1]  # Last word
        return "cluster.local"  # fallback default
    except Exception as e:
        print(f"Failed to parse {resolv_conf_path}: {e}")
        return "cluster.local"  # fallback default


def init_db_engine():
    from urllib.parse import quote

    global engine, async_session_factory
    cluster_domain = get_cluster_domain()

    db_backend = DB_BACKEND.lower()
    namespace = os.getenv("POD_NAMESPACE")

    if db_backend == "postgres":
        db_user = os.getenv("DB_APP_USER")
        db_pass = quote(str(os.getenv("DB_APP_PASSWORD")))
        if not db_user or not db_pass:
            raise ValueError("DB_APP_USER, and POSTGRES_PASSWORD must all be set")
        db_name = os.getenv("POSTGRES_DB")
        db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@postgres.{namespace}.svc.{cluster_domain}:5432/{db_name}"
        engine = create_async_engine(f"{db_url}", echo=False)

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

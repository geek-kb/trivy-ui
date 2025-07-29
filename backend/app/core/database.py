from typing import Optional, AsyncGenerator
import re
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings
from app.core.logging import logger

# Configure logging
logger = logging.getLogger("app")

# Base class for SQLAlchemy models
Base = declarative_base()

# Global variables for database connection
engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None


async def init_db_engine() -> Optional[AsyncEngine]:
    """Initialize database engine and session factory based on configuration."""
    global engine, async_session_factory

    try:
        settings = get_settings()

        # Early return for filesystem backend
        if settings.DB_BACKEND == "filesystem":
            logger.info(
                "Using filesystem backend - no database initialization required"
            )
            return None

        # For PostgreSQL backend
        if not hasattr(settings, "POSTGRES_URL"):
            raise ValueError("POSTGRES_URL setting is required for PostgreSQL backend")

        db_url = settings.POSTGRES_URL
        if not db_url:
            raise ValueError("Database URL cannot be empty")

        # Log sanitized URL for debugging
        sanitized_url = re.sub(r"://[^:]+:[^@]+@", "://<user>:<pass>@", db_url)
        logger.debug(f"Initializing database with URL: {sanitized_url}")

        # Create engine with reasonable defaults
        engine = create_async_engine(
            db_url,
            echo=settings.ENV == "development",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )

        # Create session factory
        async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")

        return engine

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise RuntimeError(f"Failed to initialize database: {str(e)}") from e


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session if using PostgreSQL backend."""
    settings = get_settings()

    if settings.DB_BACKEND == "filesystem":
        raise RuntimeError(
            "Database sessions not available when using filesystem backend"
        )

    if async_session_factory is None:
        raise RuntimeError(
            "Database session factory not initialized. Call init_db_engine first."
        )

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise


async def close_db_connection() -> None:
    """Close database connection if one exists."""
    global engine
    if engine:
        await engine.dispose()
        engine = None
        logger.info("Database connection closed")

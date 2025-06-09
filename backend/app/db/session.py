from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Build database URL
def get_database_url() -> str:
    port_env = settings.POSTGRES_PORT
    # Handle tcp:// style ports from k8s
    if isinstance(port_env, str) and port_env.startswith("tcp://"):
        host = port_env.split("//")[1].split(":")[0]
        port = port_env.split(":")[-1]
    else:
        host = settings.POSTGRES_SERVER
        port = port_env

    return (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@{host}:{port}/{settings.POSTGRES_DB}"
    )


# Create async engine
engine = create_async_engine(
    get_database_url(),
    echo=False,
    future=True,
    poolclass=NullPool,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

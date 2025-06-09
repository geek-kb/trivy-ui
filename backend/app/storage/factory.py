# File: backend/app/storage/factory.py

from typing import Optional
from app.core.config import settings
from app.core.logging import logger
from .base import StorageBackend
from app.storage.filesystem import FilesystemStorage
from app.storage.sqlite import SQLiteStorage
from app.storage.postgres import PostgresStorage

_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """
    Get or create a storage backend instance based on configuration.
    Uses singleton pattern to maintain a single instance.
    """
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    backend = settings.DB_BACKEND.lower()
    try:
        if backend == "filesystem":
            logger.info("Initializing FilesystemStorage backend")
            _storage_instance = FilesystemStorage()

        elif backend == "sqlite":
            logger.info("Initializing SQLiteStorage backend")
            _storage_instance = SQLiteStorage()

        elif backend == "postgres":
            logger.info("Initializing PostgresStorage backend")
            _storage_instance = PostgresStorage()

        else:
            error_msg = f"Unknown storage backend '{backend}'"
            logger.error(error_msg)
            raise ValueError(error_msg)

        return _storage_instance

    except Exception as e:
        logger.error(f"Failed to initialize '{backend}' storage backend: {str(e)}")
        raise RuntimeError(f"Storage backend initialization failed: {str(e)}")


def reset_storage() -> None:
    """
    Reset the storage instance.
    Useful for testing or reinitializing with different settings.
    """
    global _storage_instance
    _storage_instance = None
    logger.debug("Storage backend instance reset")

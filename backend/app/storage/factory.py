# File: backend/app/storage/factory.py

import os
from app.storage.base import StorageBackend
from app.storage.filesystem import FilesystemStorage
from app.storage.sqlite import SQLiteStorage
from app.storage.postgres import PostgresStorage

_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    backend = os.getenv("DB_BACKEND", "filesystem").lower()

    if backend == "filesystem":
        _storage_instance = FilesystemStorage()
    elif backend == "sqlite":
        _storage_instance = SQLiteStorage()
    elif backend == "postgres":
        _storage_instance = PostgresStorage()
    else:
        raise ValueError(f"Unsupported DB_BACKEND '{backend}'")

    return _storage_instance


def reset_storage():
    global _storage_instance
    _storage_instance = None

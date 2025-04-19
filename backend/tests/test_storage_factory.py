# backend/tests/test_storage_factory.py

import os
import pytest

from app.storage.factory import get_storage, reset_storage
from app.storage.filesystem import FileSystemStorage
from app.storage.sqlite import SQLiteStorage
from app.storage.postgres import PostgresStorage


@pytest.mark.parametrize(
    "backend_env, expected_class",
    [
        ("filesystem", FileSystemStorage),
        ("sqlite", SQLiteStorage),
        ("postgres", PostgresStorage),
    ],
)
def test_get_storage_backend(monkeypatch, backend_env, expected_class):
    reset_storage()
    monkeypatch.setenv("DB_BACKEND", backend_env)
    instance = get_storage()
    assert isinstance(
        instance, expected_class
    ), f"Expected {expected_class}, got {type(instance)}"

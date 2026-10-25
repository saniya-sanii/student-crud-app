"""Pytest configuration and shared fixtures for test isolation (PRD Section 17.1)."""

from collections.abc import Generator
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.database import get_connection, get_db, init_db
from app.main import app


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
    """Create a temporary SQLite database initialized with schema for each test."""
    db_path = str(tmp_path / "test_isolated.db")
    init_db(db_path)
    return db_path


@pytest.fixture
def client(temp_db: str) -> Generator[TestClient, None, None]:
    """TestClient fixture overriding get_db to connect to the isolated temp database."""
    def override_get_db() -> Generator[sqlite3.Connection, None, None]:
        conn = get_connection(temp_db)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

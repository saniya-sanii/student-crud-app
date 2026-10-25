"""Database connection and initialization module using standard library sqlite3."""

import os
import sqlite3
from collections.abc import Generator
from pathlib import Path
from typing import Optional

from app import config

# Schema DDL from PRD Section 12.2
SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 2 AND 100),
    date_of_birth TEXT NOT NULL CHECK (date_of_birth GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    email TEXT UNIQUE COLLATE NOCASE CHECK (email IS NULL OR length(email) <= 254),
    phone TEXT CHECK (phone IS NULL OR length(phone) BETWEEN 10 AND 16),
    course TEXT CHECK (course IS NULL OR length(trim(course)) BETWEEN 2 AND 100),
    address TEXT CHECK (address IS NULL OR length(address) <= 255),
    enrollment_date TEXT CHECK (enrollment_date IS NULL OR enrollment_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_students_course ON students (course);
CREATE INDEX IF NOT EXISTS idx_students_dob ON students (date_of_birth);
"""


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a new SQLite connection with dictionary row access.

    Args:
        db_path: Optional path to the database file; defaults to config.DATABASE_PATH.

    Returns:
        sqlite3.Connection configured with sqlite3.Row factory.
    """
    path = db_path or config.DATABASE_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the database schema if not already present.

    Ensures the parent directory exists, creates tables and indexes.
    """
    path = db_path or config.DATABASE_PATH
    parent_dir = Path(path).parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    with get_connection(path) as conn:
        conn.executescript(SCHEMA_SQL)


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency that yields a database connection per request.

    Closes the connection cleanly after the request completes.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

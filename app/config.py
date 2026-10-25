"""Configuration settings for the Students Database CRUD Application."""

import os
from pathlib import Path

# Base directory of the repository
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "students.db"))

# Application server defaults
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))

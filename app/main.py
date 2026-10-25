"""FastAPI Application entrypoint for Students Database CRUD API."""

from fastapi import FastAPI

app = FastAPI(
    title="Students Database CRUD Application",
    description="A backend REST API that stores and manages student records in SQLite.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get(
    "/health",
    summary="Health check",
    description="Returns the health status of the API server without touching the database.",
    tags=["System"],
)
def health_check() -> dict[str, str]:
    """Return health status of the application."""
    return {"status": "ok"}

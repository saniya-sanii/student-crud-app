"""FastAPI Application entrypoint for Students Database CRUD API."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers import students

# Set up logging for server-side observability without PII (PRD SEC-07, NFR-09)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Execute startup and shutdown logic for the application."""
    # Ensure database tables and indexes exist on startup (FR-DB-02)
    init_db()
    yield


app = FastAPI(
    title="Students Database CRUD Application",
    description="A backend REST API that stores and manages student records in SQLite.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global fallback exception handler for unexpected server errors.

    Logs error details internally without leaking PII, file paths, or stack traces
    to the client (PRD FR-E-03, SEC-06).
    """
    logger.error("Unhandled exception processing request path=%s: %s", request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Register routers
app.include_router(students.router)


@app.get(
    "/health",
    summary="Health check",
    description="Returns the health status of the API server without touching the database.",
    tags=["System"],
)
def health_check() -> dict[str, str]:
    """Return health status of the application."""
    return {"status": "ok"}

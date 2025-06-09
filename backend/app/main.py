import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.database import init_db_engine, Base, close_db_connection
from app.storage.factory import get_storage
from app.core.exception_handlers import (
    custom_http_exception_handler,
    custom_validation_exception_handler,
    generic_exception_handler,
)
from app.storage.factory import get_storage
from app.core.exception_handlers import (
    custom_http_exception_handler,
    custom_validation_exception_handler,
    generic_exception_handler,
)

# Configure logging
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI app."""
    settings = get_settings()
    logger.info("Initializing database connection...")

    try:
        # Initialize database engine (returns None for filesystem backend)
        db_engine = await init_db_engine()

        # Only run migrations if we're using a database backend
        if settings.DB_BACKEND != "filesystem":
            logger.info("Running database migrations...")
            async with db_engine.begin() as conn:  # type: ignore
                await conn.run_sync(Base.metadata.create_all)

        yield

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    finally:
        if settings.DB_BACKEND != "filesystem":
            await close_db_connection()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Trivy Report API",
        description="API for managing Trivy vulnerability scan reports",
        version="1.0.0",
        lifespan=lifespan,
    )

    # /healthz endpoint
    @app.get("/healthz")
    async def healthz():
        backend = settings.DB_BACKEND.lower()
        try:
            storage = get_storage()
            if backend == "filesystem":
                return {"app": "alive", "database": "filesystem", "backend": backend}
            elif backend in ("postgres", "sqlite"):
                await storage.count_reports()
                return {"app": "alive", "database": "ok", "backend": backend}
            else:
                return {
                    "app": "alive",
                    "database": f"unrecognized backend: {backend}",
                    "backend": backend,
                }
        except Exception as e:
            return {
                "app": "alive",
                "database": f"unhealthy ({backend})",
                "error": str(e),
                "backend": backend,
            }

    # Configure CORS
    if settings.ENV == "development":
        logger.info("Running in development mode with open CORS policy")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        logger.info("Running in production mode with restricted CORS policy")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )

    # Add security middlewares
    # Add security middlewares
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=getattr(
            settings, "ALLOWED_HOSTS", ["*"]
        ),  # Default to allowing all hosts if not specified
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add exception handlers with proper type annotations
    app.add_exception_handler(
        HTTPException,
        custom_http_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        RequestValidationError,
        custom_validation_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        Exception,
        generic_exception_handler,  # type: ignore[arg-type]
    )
    # Include routers
    app.include_router(router)

    # Log configuration
    logger.info(f"Running with DB_BACKEND={settings.DB_BACKEND}")

    return app


# Create the FastAPI application instance
app = create_app()

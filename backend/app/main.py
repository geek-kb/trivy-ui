# File: backend/app/main.py

import os
import logging
import logging.config
import yaml
from dotenv import load_dotenv
import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse, Response
from typing import Callable, Awaitable, cast
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import create_async_engine

from app.api.routes import router
from app.core.database import init_db_engine, get_cluster_domain
from app.models.report import Base
from app.core import exception_handlers
from app.core.config import settings, DB_BACKEND
from app.storage.factory import get_storage

# --- Load Environment Variables ---
load_dotenv()

# --- Setup Logging ---
LOGGING_CONFIG_PATH = "./logging.yaml"
if os.path.exists(LOGGING_CONFIG_PATH):
    try:
        with open(LOGGING_CONFIG_PATH, "r") as f:
            logging_config = yaml.safe_load(f)
            logging.config.dictConfig(logging_config)
    except Exception as e:
        print(f"Failed to load logging config: {e}")

logger = logging.getLogger("app")
ENVIRONMENT = settings.ENV.lower()

# --- Initialize FastAPI ---
app = FastAPI(
    title="Trivy UI Backend",
    description="Backend service for exposing Trivy data to the frontend.",
    version="0.1.0",
)

# --- Middleware ---
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# --- Initialize DB Engine ---
init_db_engine()

@app.on_event("startup")
async def on_startup():
    logger.info("Attempting database initialization...")
    try:
        user = os.getenv("DB_APP_USER")
        raw_password = os.getenv("DB_APP_PASSWORD")
        namespace = os.getenv("POD_NAMESPACE", "default")
        db = os.getenv("POSTGRES_DB")

        if not all([user, raw_password, db]):
            raise ValueError("Missing DB_APP_USER, DB_APP_PASSWORD, POSTGRES_DB")

        host = f"postgres.{namespace}.svc.{get_cluster_domain()}"
        password = quote_plus(str(raw_password))
        db_url = f"postgresql+asyncpg://{user}:{password}@{host}:5432/{db}"

        print(f"Connecting to database at {db_url}")
        tmp_engine = create_async_engine(db_url, echo=False, future=True)

        async with tmp_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await tmp_engine.dispose()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Skipping DB init due to error: {e}")

@app.get("/healthz")
async def healthz():
    backend = DB_BACKEND  # from config alias, lowercased
    try:
        storage = get_storage()
        if backend == "filesystem":
            return {"app": "alive", "database": "filesystem", "backend": backend}
        elif backend in ("postgres", "sqlite"):
            await storage.count_reports()
            return {"app": "alive", "database": "ok", "backend": backend}
        else:
            return {"app": "alive", "database": f"unrecognized backend: {backend}", "backend": backend}
    except Exception as e:
        return {"app": "alive", "database": f"unhealthy ({backend})", "error": str(e), "backend": backend}

# --- Exception Handlers ---
app.add_exception_handler(
    StarletteHTTPException,
    cast(
        Callable[[Request, Exception], Awaitable[Response]],
        exception_handlers.custom_http_exception_handler,
    ),
)
app.add_exception_handler(
    RequestValidationError,
    cast(
        Callable[[Request, Exception], Awaitable[Response]],
        exception_handlers.custom_validation_exception_handler,
    ),
)
app.add_exception_handler(
    Exception,
    cast(
        Callable[[Request, Exception], Awaitable[Response]],
        exception_handlers.generic_exception_handler,
    ),
)

# --- CORS ---
if ENVIRONMENT == "development":
    logger.info("Running in development mode with open CORS policy")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    allowed_origins = [
        "http://frontend.trivy-ui.svc.cluster.local",
        "https://frontend.trivy-ui.svc.cluster.local",
    ]
    logger.info(f"Running in production mode. Allowed origins: {allowed_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

app.include_router(router, prefix="/api")

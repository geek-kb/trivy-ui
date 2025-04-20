import os
import logging
import logging.config
import yaml

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse, Response
from typing import Callable, Awaitable, cast

from app.api.routes import router
from app.core.database import init_db_engine, engine
from app.models.report import Base
from app.core import exception_handlers

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

# --- Detect Environment ---
ENVIRONMENT = os.getenv("ENV", "production").lower()

# --- Initialize FastAPI ---
app = FastAPI(
    title="Trivy UI Backend",
    description="Backend service for exposing Trivy data to the frontend.",
    version="0.1.0",
)

# --- Add Middleware ---
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# --- Initialize DB Engine ---
init_db_engine()


# --- App Startup Hook ---
@app.on_event("startup")
async def on_startup():
    if engine is not None:
        logger.info("Running database initialization...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


# --- Register Exception Handlers ---
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
# --- Configure CORS ---
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
        "http://trivy-ui.trivy-ui.svc.cluster.local",
        "https://trivy-ui.trivy-ui.svc.cluster.local",
    ]
    logger.info(f"Running in production mode. Allowed origins: {allowed_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

# --- Include API Router ---
app.include_router(router, prefix="/api")


# --- Health Check Endpoint ---
@app.get("/")
async def root_status():
    logger.info("Health check on / endpoint")
    return {"message": "Trivy UI backend is running"}


# --- Optional Uvicorn Run ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("UVICORN_HOST", "0.0.0.0"),
        port=int(os.getenv("UVICORN_PORT", 8000)),
        reload=(ENVIRONMENT == "development"),
    )

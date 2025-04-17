# backend/app/main.py

import os
import logging
import logging.config
import yaml

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router
from app.core.exception_handlers import (
    generic_exception_handler,
)

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

# --- Global Error Handlers ---
from fastapi.exception_handlers import (
    http_exception_handler as fastapi_http_exception_handler,
    request_validation_exception_handler as fastapi_validation_exception_handler,
)

app.add_exception_handler(StarletteHTTPException, fastapi_http_exception_handler)
app.add_exception_handler(RequestValidationError, fastapi_validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

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
        "http://trivy-ui.default.svc.cluster.local",
        "https://trivy-ui.default.svc.cluster.local",
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


# --- Health Check ---
@app.get("/")
def root_status():
    logger.info("Health check on / endpoint")
    return {"message": "Trivy UI backend is running"}


# --- Run with Uvicorn if needed ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("UVICORN_HOST", "0.0.0.0"),
        port=int(os.getenv("UVICORN_PORT", 8000)),
        reload=(ENVIRONMENT == "development"),
    )

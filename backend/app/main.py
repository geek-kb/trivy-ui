# backend/app/main.py

import os
import logging
import logging.config
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

# Load environment variables from .env file
load_dotenv()

# Load logging config from YAML
LOGGING_CONFIG_PATH = "backend/logging.yaml"
try:
    with open(LOGGING_CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    # Detect environment
    ENVIRONMENT = os.getenv("ENV", "production").lower()

    # Adjust logging levels dynamically
    if ENVIRONMENT == "development":
        config["loggers"]["app"]["level"] = "DEBUG"
        config["root"]["level"] = "INFO"
    else:
        config["loggers"]["app"]["level"] = "INFO"
        config["root"]["level"] = "WARNING"

    logging.config.dictConfig(config)
except Exception as e:
    print(f"Failed to load logging config: {e}")

logger = logging.getLogger("app")

# Initialize FastAPI app
app = FastAPI(
    title="Trivy UI Backend",
    description="Backend service for exposing Trivy data to the frontend.",
    version="0.1.0",
)

# Configure CORS
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

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
def root_status():
    logger.info("Health check on / endpoint")
    return {"message": "Trivy UI backend is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("UVICORN_HOST", "0.0.0.0"),
        port=int(os.getenv("UVICORN_PORT", 8000)),
        reload=(ENVIRONMENT == "development"),
    )

from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Trivy UI Backend",
    description="Backend service for exposing Trivy data to the frontend.",
    version="0.1.0",
)

app.include_router(router, prefix="/api")

# backend/app/main.py

from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Trivy UI Backend",
    description="Backend service for exposing Trivy data to the frontend.",
    version="0.1.0",
)

# Mount the API routes under /api
app.include_router(router, prefix="/api")


# Optional: Define a basic root-level route for sanity check
@app.get("/")
def root_status():
    return {"message": "Trivy UI backend is running"}


# Allow running directly with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

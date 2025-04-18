
# backend/Dockerfile

# Use slim Python base image
FROM python:3.11-slim

# Environment optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install minimal system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend /app/backend

# Create reports storage (even if using volumes later)
RUN mkdir -p /app/storage/reports

# Expose FastAPI default port
EXPOSE 8000

# Default: Run dev server (can override in docker-compose.yml if needed)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

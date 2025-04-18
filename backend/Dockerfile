
# backend/Dockerfile

# Use slim Python base image
FROM python:3.11-slim

# Environment optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install minimal system packages (add tzdata for timezone support)
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  tzdata \
  && rm -rf /var/lib/apt/lists/*

# Set a DEFAULT timezone environment variable (can be overridden by Docker Compose or CLI)
ENV TZ=${TZ:-UTC}

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend /app/backend

# Create storage directories
RUN mkdir -p /app/storage/reports

# Expose FastAPI default port
EXPOSE 8000

# Default command: Development server with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

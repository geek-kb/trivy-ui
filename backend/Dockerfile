
# File: backend/Dockerfile

FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  TZ=${TZ:-UTC}

# Set work directory inside container
WORKDIR /app/backend

# Copy everything from local backend/ folder into container /app/backend/
COPY . .

# Install system packages needed (e.g., tzdata for timezones)
RUN apt-get update && apt-get install -y --no-install-recommends tree tzdata \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Expose FastAPI default port
EXPOSE 8000

# Start Uvicorn server (correct import path!)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


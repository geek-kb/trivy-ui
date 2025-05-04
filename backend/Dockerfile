
# File: backend/Dockerfile

FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  PYTHONPATH=/app/backend \
  TZ=${TZ:-UTC}

# Set working directory inside container
WORKDIR /app/backend

# Copy backend code
COPY . .

# Install system packages (e.g. tzdata)
RUN apt-get update && apt-get install -y --no-install-recommends \
  tzdata \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI default port
EXPOSE 8000

# Add entrypoint script
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use the secure entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

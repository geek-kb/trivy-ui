
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  TZ=${TZ:-UTC}

WORKDIR /app/backend

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
  tzdata \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create the storage folder where FileSystemStorage writes:
RUN mkdir -p app/storage/reports

# (We don't COPY the code here in dev, the volume mount will overlay ./backend → /app/backend)

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

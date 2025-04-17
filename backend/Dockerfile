
# Dockerfile

# Use slim Python image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY app ./app
COPY logging.yaml .
COPY reports ./reports

# Copy production environment file and rename to `.env`
COPY .env.production .env

# Expose API port
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Phase 3: Add monitoring dependencies
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/monitoring /mlflow

# Expose API port
EXPOSE 8000

# Default command (overridden in docker-compose)
CMD ["uvicorn", "src.api_mlflow:app", "--host", "0.0.0.0", "--port", "8000"]
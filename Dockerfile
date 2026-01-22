# ============================================================
# Multi-purpose Docker image for ML services
# Supports: Training, API, Monitoring
# ============================================================
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/data \
             /app/models \
             /app/monitoring/reference \
             /app/monitoring/predictions \
             /app/monitoring/labels \
             /app/monitoring/metrics \
             /app/monitoring/reports \
             /app/monitoring/retraining/shadow_models \
             /app/monitoring/retraining/evaluation_results \
             /app/monitoring/retraining/decisions \
             /mlflow

# Expose API port
EXPOSE 8000

# Default command (overridden in docker-compose)
CMD ["uvicorn", "src.api_mlflow:app", "--host", "0.0.0.0", "--port", "8000"]

# ─── Smart Documentation Architect — Backend Dockerfile ───
# Works with Render, Railway, Fly.io, and any Docker-based host.

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pymupdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create tmp dirs for serverless file storage
RUN mkdir -p /tmp/uploads /tmp/outputs

# Expose port (Render/Railway use $PORT)
EXPOSE 8000

# Start with uvicorn — $PORT is injected by most PaaS providers
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

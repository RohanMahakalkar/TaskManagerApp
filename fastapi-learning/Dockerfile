# Multi-stage build for production
# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies to /install directory
COPY requirements.txt ./
RUN mkdir -p /install && pip install --target /install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /app/dependencies

# Set PYTHONPATH to include dependencies
ENV PYTHONPATH=/app/dependencies:$PYTHONPATH

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 fastapi && chown -R fastapi:fastapi /app

USER fastapi

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

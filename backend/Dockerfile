# ONYX Backend - Fly.io Dockerfile
# Full-featured build with all scanning and ML capabilities

# ============================================================================
# Stage 1: Builder - Install Python dependencies
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages (includes all features)
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================
# Stage 2: Production - Runtime image with full features
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder (includes numpy, scipy, scanning tools)
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PORT=8080

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with single worker to minimize memory usage
# --max-requests helps prevent memory leaks by recycling workers
CMD ["gunicorn", "app:app", \
     "-w", "1", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8080", \
     "--timeout", "120", \
     "--max-requests", "500", \
     "--max-requests-jitter", "50", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5"]

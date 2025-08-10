# Multi-stage Docker build for SecureDevOps AI Platform
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r securedevops && \
    useradd -r -g securedevops -d /app -s /bin/bash securedevops

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    wget \
    unzip \
    gnupg \
    software-properties-common \
    build-essential \
    netcat-openbsd \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Security scanners installation stage
FROM base as scanners

# Install Node.js for Semgrep
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Semgrep
RUN pip install semgrep==1.45.0

# Install Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.47.0

# Install GitLeaks
RUN wget https://github.com/zricethezav/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz \
    && tar -xzf gitleaks_8.18.0_linux_x64.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/gitleaks \
    && rm gitleaks_8.18.0_linux_x64.tar.gz

# Install Lynis
RUN wget https://downloads.cisofy.com/lynis/lynis-3.0.8.tar.gz \
    && tar -xzf lynis-3.0.8.tar.gz \
    && mv lynis /opt/lynis \
    && ln -s /opt/lynis/lynis /usr/local/bin/lynis \
    && chmod +x /opt/lynis/lynis \
    && rm lynis-3.0.8.tar.gz

# Verify scanner installations
RUN semgrep --version && \
    trivy --version && \
    gitleaks version && \
    lynis --version

# Application stage
FROM scanners as app

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY --chown=securedevops:securedevops requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=securedevops:securedevops . .

# Create necessary directories
RUN mkdir -p /app/logs /app/temp && \
    chown -R securedevops:securedevops /app

# Create scanner cache directories
RUN mkdir -p /home/securedevops/.cache/semgrep \
             /home/securedevops/.cache/trivy \
    && chown -R securedevops:securedevops /home/securedevops

# Switch to non-root user
USER securedevops

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production startup script
COPY --chown=securedevops:securedevops start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]

# Production image with minimal footprint
FROM app as production

# Remove unnecessary packages to reduce image size
USER root
RUN apt-get remove -y \
    build-essential \
    software-properties-common \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /root/.cache

USER securedevops

# Multi-architecture build support
# docker buildx build --platform linux/amd64,linux/arm64 -t securedevops-platform .

# Build arguments for customization
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Labels for container metadata
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="SecureDevOps AI Platform" \
      org.label-schema.description="Production-ready security scanning platform with AI analysis" \
      org.label-schema.url="https://github.com/your-org/securedevops-platform" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-org/securedevops-platform" \
      org.label-schema.vendor="SecureDevOps Team" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Environment variables with defaults
ENV APP_NAME="SecureDevOps AI Platform" \
    APP_VERSION="1.0.0" \
    HOST="0.0.0.0" \
    PORT="8000" \
    WORKERS="4" \
    LOG_LEVEL="INFO" \
    TEMP_DIR="/app/temp" \
    LOG_FILE="/app/logs/app.log" \
    SEMGREP_PATH="semgrep" \
    TRIVY_PATH="trivy" \
    GITLEAKS_PATH="gitleaks" \
    LYNIS_PATH="lynis"

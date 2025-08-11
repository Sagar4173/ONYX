#!/bin/bash

# SecureDevOps Backend Startup Script
# Production deployment with Gunicorn + Uvicorn workers

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Wait for dependencies
wait_for_dependency() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=60
    local attempt=0

    log "Waiting for $service_name at $host:$port..."
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log "$service_name is ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    error "$service_name failed to become available within timeout"
}

# Environment setup
setup_environment() {
    log "Setting up environment..."
    
    # Create necessary directories
    mkdir -p /app/logs
    mkdir -p /app/temp
    mkdir -p /app/workspace
    mkdir -p /app/.cache
    
    # Set proper permissions (only for directories we can control)
    chown -R securedevops:securedevops /app/logs 2>/dev/null || true
    chown -R securedevops:securedevops /app/temp 2>/dev/null || true
    # Skip workspace and cache permissions for Docker volumes
    # chown -R securedevops:securedevops /app/workspace
    # chown -R securedevops:securedevops /app/.cache
    
    # Verify scanner installations
    log "Verifying security scanners..."
    
    if command -v semgrep >/dev/null 2>&1; then
        log "✓ Semgrep available"
    else
        warn "✗ Semgrep not found - SAST scanning disabled"
    fi
    
    if command -v trivy >/dev/null 2>&1; then
        log "✓ Trivy available"
    else
        warn "✗ Trivy not found - dependency scanning disabled"
    fi
    
    if command -v gitleaks >/dev/null 2>&1; then
        log "✓ GitLeaks available"
    else
        warn "✗ GitLeaks not found - secrets scanning disabled"
    fi
    
    if command -v lynis >/dev/null 2>&1; then
        log "✓ Lynis available"
    else
        warn "✗ Lynis not found - system scanning disabled"
    fi
}

# Database connection check
check_database() {
    log "Checking database connection..."
    
    # Extract MongoDB host from MONGODB_URI
    if [ -n "$MONGODB_URI" ]; then
        # Parse mongodb://user:pass@host:port/db format
        MONGO_HOST=$(echo "$MONGODB_URI" | sed -n 's|mongodb://[^@]*@\([^:]*\):.*|\1|p')
        MONGO_PORT=$(echo "$MONGODB_URI" | sed -n 's|mongodb://[^@]*@[^:]*:\([0-9]*\)/.*|\1|p')
        
        if [ -n "$MONGO_HOST" ] && [ -n "$MONGO_PORT" ]; then
            wait_for_dependency "MongoDB" "$MONGO_HOST" "$MONGO_PORT"
        else
            warn "Could not parse MongoDB connection details from MONGODB_URI"
        fi
    else
        warn "MONGODB_URI not set - assuming MongoDB is available"
    fi
}

# Pre-flight checks
preflight_checks() {
    log "Running pre-flight checks..."
    
    # Check required environment variables
    if [ -z "$OPENAI_API_KEY" ]; then
        warn "OPENAI_API_KEY not set - AI analysis features will be disabled"
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        error "SECRET_KEY is required but not set"
    fi
    
    # Validate configuration
    if [ -z "$HOST" ]; then
        export HOST="0.0.0.0"
        warn "HOST not set, defaulting to 0.0.0.0"
    fi
    
    if [ -z "$PORT" ]; then
        export PORT="8000"
        warn "PORT not set, defaulting to 8000"
    fi
    
    if [ -z "$WORKERS" ]; then
        export WORKERS="4"
        warn "WORKERS not set, defaulting to 4"
    fi
    
    log "Configuration validated"
}

# Start application
start_application() {
    log "Starting SecureDevOps AI Platform Backend..."
    log "Configuration:"
    log "  Host: $HOST"
    log "  Port: $PORT"
    log "  Workers: $WORKERS"
    log "  Environment: ${ENVIRONMENT:-development}"
    log "  Log Level: ${LOG_LEVEL:-INFO}"
    
    # Start gunicorn (already running as securedevops user from Dockerfile)
    exec gunicorn \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers "$WORKERS" \
        --bind "$HOST:$PORT" \
        --timeout 120 \
        --keep-alive 2 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --preload \
        --access-logfile /app/logs/access.log \
        --error-logfile /app/logs/error.log \
        --log-level "${LOG_LEVEL:-info}" \
        --capture-output \
        --enable-stdio-inheritance \
        app:app
}

# Main execution
main() {
    log "Initializing SecureDevOps AI Platform Backend..."
    
    setup_environment
    check_database
    preflight_checks
    start_application
}

# Signal handlers for graceful shutdown
trap 'log "Received SIGTERM, shutting down gracefully..."; kill -TERM $PID; wait $PID' TERM
trap 'log "Received SIGINT, shutting down gracefully..."; kill -INT $PID; wait $PID' INT

# Check if we're being sourced or executed
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@" &
    PID=$!
    wait $PID
fi

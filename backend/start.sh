#!/bin/bash
# Render startup script for ONYX Backend

echo "🚀 Starting ONYX Security Intelligence Platform Backend"
echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"

# Start the application with gunicorn
echo "🚀 Starting FastAPI with Gunicorn..."
exec gunicorn app:app -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000}

#!/bin/bash
# Railway startup script with virtual environment

echo "🚀 Starting SecureDevOps AI Platform Backend"
echo "📁 Current directory: $(pwd)"

# Activate virtual environment
source /opt/venv/bin/activate

echo "🐍 Python version: $(python --version)"
echo "📦 Pip version: $(pip --version)"

# Start the application
echo "🚀 Starting FastAPI application..."
python main.py

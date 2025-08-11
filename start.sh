#!/bin/bash
# Railway startup script

echo "🚀 Starting SecureDevOps AI Platform Backend"
echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "📦 Pip version: $(pip --version)"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Start the application
echo "🚀 Starting FastAPI application..."
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port $PORT

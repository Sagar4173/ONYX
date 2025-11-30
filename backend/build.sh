#!/usr/bin/env bash
# Render build script for ONYX Backend

set -o errexit

echo "🔧 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build complete!"

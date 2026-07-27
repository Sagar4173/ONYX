# ONYX Backend - Development entry point
# For production, use: gunicorn app:app -k uvicorn.workers.UvicornWorker

import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the backend application
if __name__ == "__main__":
    try:
        # Import the FastAPI app
        import uvicorn

        from app import app
        
        port = int(os.environ.get("PORT", 8000))
        host = "0.0.0.0"
        
        try:
            print(f"🚀 Starting server on {host}:{port}")
        except UnicodeEncodeError:
            print(f"[START] Starting server on {host}:{port}")
        try:
            print(f"📍 Working directory: {os.getcwd()}")
        except UnicodeEncodeError:
            print(f"[DIR] Working directory: {os.getcwd()}")
        try:
            print(f"🏥 Health check will be available at: http://{host}:{port}/health")
        except UnicodeEncodeError:
            print(f"[HEALTH] Health check will be available at: http://{host}:{port}/health")
        
        # Start development server
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        try:
            print(f"❌ Failed to start application: {e}")
        except UnicodeEncodeError:
            print(f"[ERROR] Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

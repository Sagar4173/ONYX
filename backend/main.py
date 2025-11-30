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
        from app import app
        import uvicorn
        
        port = int(os.environ.get("PORT", 8000))
        host = "0.0.0.0"
        
        print(f"🚀 Starting server on {host}:{port}")
        print(f"📍 Working directory: {os.getcwd()}")
        print(f"🏥 Health check will be available at: http://{host}:{port}/health")
        
        # Start development server
        uvicorn.run(
            app, 
            host=host, 
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

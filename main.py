# Railway deployment entry point
# This file helps Railway detect this as a Python project
# The actual application is in backend/app.py

import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Change working directory to backend for relative imports
os.chdir(str(backend_path))

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
        
        # Start with minimal configuration for Railway
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

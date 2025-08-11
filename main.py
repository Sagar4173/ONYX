# Railway deployment entry point
# This file helps Railway detect this as a Python project
# The actual application is in backend/app.py

import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and run the backend application
if __name__ == "__main__":
    from backend.app import app
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

#!/usr/bin/env python3
"""
Railway Deployment Entry Point for SecureDevOps AI Platform Backend
This file ensures Railway detects this as a Python project
"""

import os
import sys
import subprocess

def main():
    """Start the FastAPI backend"""
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    # Get port from environment
    port = os.environ.get('PORT', '8000')
    
    # Start uvicorn server
    cmd = [
        sys.executable, '-m', 'uvicorn', 
        'app:app', 
        '--host', '0.0.0.0', 
        '--port', port,
        '--workers', '1'
    ]
    
    print(f"🚀 Starting SecureDevOps AI Platform on port {port}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()

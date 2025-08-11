#!/usr/bin/env python3
"""
Railway Environment Variables Setup Helper
Run this to see the exact environment variables you need to set in Railway dashboard
"""

def print_railway_env_vars():
    env_vars = {
        "MONGODB_URI": "mongodb+srv://Ghost4173:Ghost%405555@securedevopsai-db.munpiyz.mongodb.net/securedevops?retryWrites=true&w=majority&appName=SecureDevOpsAI-DB",
        "SECRET_KEY": "85M$$wWl2YR8tS!5aX62cx1$$6dhdSQOWLc+kaxgzYFe4jiCk1aF2CZi3hjeHBox3w",
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "CORS_ORIGINS": "https://secure-dev-ops-ai-platform.vercel.app,http://localhost:5173,http://localhost:3000",
        "OPENAI_API_KEY": "your_openai_api_key_here"
    }
    
    print("🚀 Railway Environment Variables Setup")
    print("=" * 50)
    print("Copy these to your Railway dashboard:")
    print()
    
    for key, value in env_vars.items():
        print(f"{key}={value}")
    
    print()
    print("📝 Instructions:")
    print("1. Go to your Railway project dashboard")
    print("2. Click on 'Variables' tab")
    print("3. Add each variable above")
    print("4. Redeploy your service")

if __name__ == "__main__":
    print_railway_env_vars()

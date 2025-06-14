#!/usr/bin/env python3
"""
Arasaka Neural-Net Trading Matrix - API Server Launcher
Starts the FastAPI backend server
"""
import os
import sys
import uvicorn

def main():
    # Set working directory to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 60)
    print("Starting Arasaka API Server...")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    
    # Check if database directory exists
    os.makedirs("logs", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    
    # Import settings
    from config.settings import settings
    
    print(f"API will run on: http://{settings.API_HOST}:{settings.API_PORT}")
    print("=" * 60)
    
    try:
        # Import and run API
        from api.app import app
        uvicorn.run(
            app, 
            host=settings.API_HOST, 
            port=settings.API_PORT,
            log_level=settings.LOG_LEVEL.lower()
        )
    except Exception as e:
        print(f"\nError: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()

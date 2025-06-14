#!/usr/bin/env python3
"""
Arasaka API Launcher - Ensures proper Python path setup
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now import and run the API
if __name__ == "__main__":
    from api.app import app
    import uvicorn
    
    print("=" * 60)
    print("Starting Arasaka Neural-Net Trading Matrix API...")
    print("=" * 60)
    
    # Get settings
    from config.settings import settings
    
    # Run the API
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
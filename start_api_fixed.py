#!/usr/bin/env python3
"""
Fixed API Launcher for Arasaka Neural-Net Trading Matrix
No Unicode issues!
"""
import sys
import os
import time

# Add project root to Python path
sys.path.insert(0, os.getcwd())

print("\n" + "="*60)
print("ARASAKA NEURAL-NET API SERVER")
print("="*60 + "\n")

try:
    # Import the FastAPI app
    from api.app import app
    import uvicorn
    
    print("[OK] All imports successful")
    print("[OK] Starting API server on http://localhost:8000")
    print("[OK] API Docs available at http://localhost:8000/docs")
    print("\n" + "-"*60)
    print("Leave this window open while using the trading bot")
    print("Press Ctrl+C to stop the server")
    print("-"*60 + "\n")
    
    # Start the server
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000,
        log_level="info"
    )
    
except ImportError as e:
    print(f"\n[ERROR] Import failed: {e}")
    print("\nTrying to fix imports...")
    
    # Try alternative import method
    try:
        import api.app
        import uvicorn
        
        print("[OK] Alternative import successful")
        uvicorn.run(
            "api.app:app",
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except Exception as e2:
        print(f"\n[FATAL] Could not start API: {e2}")
        print("\nPlease ensure you're in the Night-City-Trader directory")
        print("and all requirements are installed:")
        print("  pip install -r requirements.txt")
        
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    
input("\nPress Enter to exit...")
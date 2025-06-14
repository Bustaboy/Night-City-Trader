#!/usr/bin/env python3
"""
Create the missing launcher files for Night-City-Trader
"""
import os

# File contents
run_gui_content = '''#!/usr/bin/env python3
"""
Arasaka Neural-Net Trading Matrix - GUI Launcher
Ensures proper working directory and environment setup
"""
import os
import sys
import subprocess

def main():
    # Set working directory to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 60)
    print("Starting Arasaka Neural-Net Trading Matrix...")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    
    # Check if database directory exists
    os.makedirs("logs", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    
    # Patch Canvas if needed
    import tkinter as tk
    canvas_create_rounded_rectangle = lambda self, x1, y1, x2, y2, radius, **kwargs: self.create_polygon(
        [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
         (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
         (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
         (x1 + radius, y2), (x1, y2), (x1, y2 - radius)],
        smooth=True, **kwargs
    )
    
    if not hasattr(tk.Canvas, 'create_rounded_rectangle'):
        tk.Canvas.create_rounded_rectangle = canvas_create_rounded_rectangle
        print("Canvas methods patched")
    
    print("Default PIN: 2077")
    print("=" * 60)
    print("\\nIMPORTANT: Make sure the API server is running!")
    print("In another terminal, run: python run_api.py")
    print("=" * 60)
    
    try:
        # Import and run main GUI
        from gui.main import main
        main()
    except Exception as e:
        print(f"\\nError: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''

run_api_content = '''#!/usr/bin/env python3
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
        print(f"\\nError: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''

batch_file_content = '''@echo off
title Arasaka Neural-Net Trading Matrix Launcher
color 0A

echo ============================================================
echo     ARASAKA NEURAL-NET TRADING MATRIX v2.0
echo     Stack Eddies in the Net!
echo ============================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

echo Starting API Server...
start "Arasaka API Server" cmd /k "cd /d %~dp0 && python run_api.py"

:: Wait for API to start
echo Waiting for API to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Starting Trading Matrix GUI...
start "Arasaka Trading GUI" cmd /k "cd /d %~dp0 && python run_gui.py"

echo.
echo ============================================================
echo Both windows should now be open:
echo - API Server (keep this running)
echo - Trading GUI (use PIN: 2077)
echo.
echo To stop: Close both windows
echo ============================================================
echo.
pause
'''

# Create files
files = [
    ("run_gui.py", run_gui_content),
    ("run_api.py", run_api_content),
    ("START_TRADING_MATRIX.bat", batch_file_content)
]

print("Creating launcher files...")

for filename, content in files:
    try:
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✓ Created {filename}")
    except Exception as e:
        print(f"✗ Failed to create {filename}: {e}")

print("\nDone! You can now run:")
print("  python run_api.py     (in one terminal)")
print("  python run_gui.py     (in another terminal)")
print("\nOr just double-click START_TRADING_MATRIX.bat")

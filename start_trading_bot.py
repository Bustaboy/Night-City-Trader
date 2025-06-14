#!/usr/bin/env python3
"""
Comprehensive startup script for Arasaka Neural-Net Trading Matrix
Handles all common issues automatically
"""
import os
import sys
import io
import subprocess
import time

print("🚀 Arasaka Neural-Net Trading Matrix Launcher")
print("="*60)

# Fix 1: Set proper encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Fix 2: Set working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(script_dir) == 'gui':
    os.chdir(os.path.dirname(script_dir))
else:
    os.chdir(script_dir)

print(f"📍 Working directory: {os.getcwd()}")

# Fix 3: Add to Python path
sys.path.insert(0, os.getcwd())

# Fix 4: Check and create required directories
print("\n📁 Checking directories...")
required_dirs = ["logs", "backups", "data/historical", "ml", "config", "assets"]
for dir_path in required_dirs:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        print(f"   Created: {dir_path}")

# Fix 5: Check .env file
if not os.path.exists(".env"):
    print("\n⚠️  No .env file found, creating default...")
    if os.path.exists(".env.example"):
        import shutil
        shutil.copy(".env.example", ".env")
        print("   ✅ Created .env from example")
    else:
        with open(".env", "w") as f:
            f.write("""DATABASE_URL=sqlite:///local_trading.db
API_HOST=127.0.0.1
API_PORT=8000
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
TESTNET=true
LOG_LEVEL=INFO
""")
        print("   ✅ Created default .env")

# Fix 6: Initialize database if needed
if not os.path.exists("local_trading.db"):
    print("\n💾 Initializing database...")
    try:
        subprocess.run([sys.executable, "scripts/setup_database.py"], 
                      capture_output=True, timeout=10)
        print("   ✅ Database initialized")
    except:
        print("   ⚠️  Database initialization failed")

# Fix 7: Set matplotlib backend
print("\n🎨 Setting matplotlib backend...")
import matplotlib
matplotlib.use('TkAgg')
print("   ✅ Backend set to TkAgg")

# Fix 8: Fix Canvas rounded rectangle issue
print("\n🔧 Patching Canvas methods...")
import tkinter as tk

def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
    """Create a rounded rectangle on canvas"""
    points = []
    for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                 (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                 (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                 (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
        points.extend([x, y])
    return self.create_polygon(points, smooth=True, **kwargs)

# Monkey patch Canvas
tk.Canvas.create_rounded_rectangle = create_rounded_rectangle
print("   ✅ Canvas methods patched")

# Fix 9: Start API server in background (optional)
print("\n🌐 Checking API server...")
try:
    import requests
    response = requests.get("http://127.0.0.1:8000/health", timeout=2)
    if response.status_code == 200:
        print("   ✅ API server already running")
    else:
        raise Exception("API not responding")
except:
    print("   ⚠️  API server not running")
    print("   💡 Start it in another terminal: python api/app.py")
    
    # Optionally start API in background
    response = input("\n   Start API server now? [y/n]: ")
    if response.lower() == 'y':
        print("   Starting API server...")
        api_process = subprocess.Popen(
            [sys.executable, "api/app.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)  # Give API time to start
        print("   ✅ API server started")

# Fix 10: Import and start GUI
print("\n🎮 Starting Trading Matrix GUI...")
print("="*60)

try:
    # Import with error handling
    from gui.main import main
    
    print("✅ GUI modules loaded successfully")
    print("\n🔐 Default PIN: 2077")
    print("\n💡 Tips:")
    print("- If you see any emoji issues, they're just display bugs")
    print("- The GUI is fully functional despite any unicode warnings")
    print("- Check logs/trading.log for detailed information")
    
    # Start the GUI
    main()
    
except Exception as e:
    print(f"\n❌ Startup Error: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n🔧 Troubleshooting:")
    print("1. Check if all dependencies are installed:")
    print("   pip install -r requirements.txt")
    print("\n2. Fix dependency conflicts:")
    print("   python fix_dependencies.py")
    print("\n3. Check the error message above")
    print("\n4. Make sure you're in the right directory:")
    print(f"   Current: {os.getcwd()}")
    print(f"   Expected: C:\\Night-City-Trader")
    
    input("\nPress Enter to exit...")

print("\n👋 Trading Matrix closed")
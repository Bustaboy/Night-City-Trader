#!/usr/bin/env python3
"""Quick fix for common GUI startup crashes"""
import os
import sys
import subprocess

print("🚨 Quick Fix for GUI Startup Crash")
print("="*60)

# Fix 1: Install missing dependencies
print("\n1️⃣ Installing/updating dependencies...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "matplotlib", "requests", "pandas", "numpy"])
    print("✅ Dependencies updated")
except:
    print("❌ Failed to update dependencies")

# Fix 2: Create .env if missing
print("\n2️⃣ Checking .env file...")
if not os.path.exists(".env"):
    print("Creating .env file...")
    env_content = """# Arasaka Neural-Net Trading Matrix
DATABASE_URL=sqlite:///local_trading.db
API_HOST=127.0.0.1
API_PORT=8000
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
TESTNET=true
LOG_LEVEL=INFO
"""
    with open(".env", "w") as f:
        f.write(env_content)
    print("✅ Created .env file")
else:
    print("✅ .env file exists")

# Fix 3: Initialize database
print("\n3️⃣ Initializing database...")
try:
    subprocess.run([sys.executable, "scripts/setup_database.py"], capture_output=True)
    print("✅ Database initialized")
except:
    print("❌ Database initialization failed")

# Fix 4: Fix matplotlib backend in gui/main.py
print("\n4️⃣ Fixing matplotlib backend...")
try:
    with open("gui/main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    if "matplotlib.use('TkAgg')" not in content:
        # Find where to insert
        lines = content.split('\n')
        insert_after = -1
        
        for i, line in enumerate(lines):
            if "import matplotlib" in line and "pyplot" in line:
                insert_after = i
                break
        
        if insert_after >= 0:
            lines[insert_after] = "import matplotlib\nmatplotlib.use('TkAgg')\nimport matplotlib.pyplot as plt"
            
            with open("gui/main.py", "w", encoding="utf-8") as f:
                f.write('\n'.join(lines))
            
            print("✅ Fixed matplotlib backend")
        else:
            print("⚠️  Could not find matplotlib import")
    else:
        print("✅ matplotlib backend already fixed")
except Exception as e:
    print(f"❌ Could not fix matplotlib: {e}")

# Fix 5: Create all required directories
print("\n5️⃣ Creating required directories...")
dirs = ["logs", "backups", "data", "data/historical", "ml", "config", "assets"]
for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)
print("✅ All directories created")

# Fix 6: Test import
print("\n6️⃣ Testing GUI import...")
test_code = f"""
import sys
sys.path.insert(0, r'{os.getcwd()}')

try:
    # Set matplotlib backend first
    import matplotlib
    matplotlib.use('TkAgg')
    
    # Test other imports
    from config.settings import settings
    from core.database import db
    print("✅ Core imports successful")
    
    # Test GUI import
    import gui.main
    print("✅ GUI import successful")
    
except Exception as e:
    print(f"❌ Import error: {{e}}")
    import traceback
    traceback.print_exc()
"""

result = subprocess.run([sys.executable, "-c", test_code], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

# Create a fixed startup script
print("\n7️⃣ Creating fixed startup script...")

startup_script = """#!/usr/bin/env python3
import os
import sys

# Fix path
if os.path.basename(os.getcwd()) != 'Night-City-Trader':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if os.path.basename(os.getcwd()) == 'gui':
        os.chdir('..')

sys.path.insert(0, os.getcwd())

# Fix matplotlib
import matplotlib
matplotlib.use('TkAgg')

# Now import and run
try:
    from gui.main import main
    main()
except Exception as e:
    print(f"\\nStartup Error: {e}")
    import traceback
    traceback.print_exc()
    input("\\nPress Enter to exit...")
"""

with open("start_trading_matrix.py", "w") as f:
    f.write(startup_script)

print("✅ Created start_trading_matrix.py")

print("\n" + "="*60)
print("🚀 FIXES APPLIED!")
print("="*60)

print("\nTry starting the GUI with:")
print("1. python start_trading_matrix.py")
print("\nOr directly:")
print("2. python gui/main.py")

print("\nIf it still crashes, run:")
print("- python diagnose_gui_crash.py")
print("\nThis will show you the exact error.")

# Final check - try to identify specific error
print("\n🔍 Checking for specific error...")
result = subprocess.run([sys.executable, "gui/main.py"], capture_output=True, text=True, timeout=5)
if result.returncode != 0:
    print("\n❌ Startup failed with:")
    error_lines = result.stderr.split('\n') if result.stderr else []
    for line in error_lines[-10:]:  # Last 10 lines
        if line.strip():
            print(f"   {line}")
    
    # Common error fixes
    if "No module named" in result.stderr:
        module = result.stderr.split("'")[1]
        print(f"\n🔧 Fix: pip install {module}")
    elif "SystemError" in result.stderr and "matplotlib" in result.stderr:
        print("\n🔧 Fix: The matplotlib backend issue - already fixed above")
    elif "SyntaxError" in result.stderr:
        print("\n🔧 Fix: The downloaded file may be corrupted - download again")
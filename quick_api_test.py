#!/usr/bin/env python3
"""Quick API diagnostic and fix script"""
import subprocess
import sys
import os
import time
import socket

def check_port(port=8000):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0  # True if port is free

def find_free_port(start=8000):
    """Find a free port starting from 8000"""
    for port in range(start, start + 100):
        if check_port(port):
            return port
    return None

def test_imports():
    """Test if all imports work"""
    print("Testing critical imports...")
    
    try:
        sys.path.insert(0, os.getcwd())
        
        # Test each import
        imports = [
            ("Settings", "from config.settings import settings"),
            ("Database", "from core.database import db"),
            ("FastAPI", "import fastapi"),
            ("Uvicorn", "import uvicorn"),
        ]
        
        for name, import_str in imports:
            try:
                exec(import_str)
                print(f"✅ {name} imported successfully")
            except Exception as e:
                print(f"❌ {name} import failed: {e}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def start_api_with_free_port():
    """Start API on first available port"""
    print("\n🔍 Checking for available port...")
    
    # Check if default port is free
    if check_port(8000):
        port = 8000
        print(f"✅ Port 8000 is available")
    else:
        print(f"⚠️  Port 8000 is in use")
        port = find_free_port(8001)
        if port:
            print(f"✅ Found free port: {port}")
        else:
            print("❌ No free ports available!")
            return False
    
    print(f"\n🚀 Starting API server on port {port}...")
    
    # Create a simple launcher script
    launcher_code = f'''
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from api.app import app
    import uvicorn
    
    print("\\n" + "="*60)
    print(f"ARASAKA API SERVER STARTING ON PORT {port}")
    print("="*60 + "\\n")
    
    uvicorn.run(app, host="127.0.0.1", port={port}, log_level="info")
    
except Exception as e:
    print(f"❌ Failed to start API: {{e}}")
    import traceback
    traceback.print_exc()
'''
    
    # Write launcher
    with open("temp_api_launcher.py", "w") as f:
        f.write(launcher_code)
    
    try:
        # Start API
        process = subprocess.Popen(
            [sys.executable, "temp_api_launcher.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        print(f"\n✅ API server starting in new window...")
        print(f"📍 API URL: http://localhost:{port}")
        print(f"📍 Docs: http://localhost:{port}/docs")
        
        # Wait a bit
        time.sleep(3)
        
        # Test if API is responding
        try:
            import requests
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"\n🎉 API SERVER IS RUNNING!")
                print(f"✅ Health check passed: {response.json()}")
            else:
                print(f"\n⚠️  API started but health check failed")
        except:
            print(f"\n⚠️  API might be starting slowly. Check the new window for details.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to start API: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists("temp_api_launcher.py"):
            try:
                os.remove("temp_api_launcher.py")
            except:
                pass

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                  ARASAKA API DIAGNOSTIC TOOL                  ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Test imports
    if not test_imports():
        print("\n❌ Import errors detected. Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\n✅ Requirements installed. Please run this script again.")
        return
    
    # Step 2: Start API
    if start_api_with_free_port():
        print("\n" + "="*60)
        print("📋 NEXT STEPS:")
        print("="*60)
        print("1. Leave the API server running")
        print("2. Open a NEW terminal")
        print("3. Run: python gui/main.py")
        print("4. Login with PIN: 2077")
        print("\n✨ Your Neural-Net Trading Matrix is ready!")
    else:
        print("\n❌ Failed to start API. Check the error messages above.")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
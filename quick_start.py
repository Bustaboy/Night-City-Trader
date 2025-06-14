# quick_start.py
"""
Quick Start Script for the Arasaka Neural-Net Trading Matrix
This script helps you set up and run the trading bot quickly
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print cyberpunk banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ▄▄▄       ██▀███   ▄▄▄        ██████  ▄▄▄       ██ ▄█▀  ║
    ║    ▒████▄    ▓██ ▒ ██▒▒████▄    ▒██    ▒ ▒████▄     ██▄█▒   ║
    ║    ▒██  ▀█▄  ▓██ ░▄█ ▒▒██  ▀█▄  ░ ▓██▄   ▒██  ▀█▄  ▓███▄░   ║
    ║    ░██▄▄▄▄██ ▒██▀▀█▄  ░██▄▄▄▄██   ▒   ██▒░██▄▄▄▄██ ▓██ █▄   ║
    ║     ▓█   ▓██▒░██▓ ▒██▒ ▓█   ▓██▒▒██████▒▒ ▓█   ▓██▒▒██▒ █▄  ║
    ║                                                               ║
    ║          NEURAL-NET TRADING MATRIX - QUICK START              ║
    ║                  Stack Eddies in the Net!                     ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print("\033[95m" + banner + "\033[0m")

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required. You have:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    return True

def check_venv():
    """Check if running in virtual environment"""
    if sys.prefix == sys.base_prefix:
        print("⚠️  Not in virtual environment")
        return False
    print("✅ Virtual environment active")
    return True

def create_directories():
    """Create necessary directories"""
    dirs = [
        "logs",
        "data/historical",
        "backups",
        "ml",
        "config"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from example")
            print("⚠️  Please edit .env and add your API keys!")
            return False
        else:
            print("❌ No .env file found")
            return False
    print("✅ Environment file exists")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("   Try: pip install -r requirements.txt")
        return False

def setup_database():
    """Initialize database"""
    print("\n🗄️  Setting up database...")
    try:
        subprocess.check_call([sys.executable, "scripts/setup_database.py"])
        print("✅ Database initialized")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to setup database")
        return False

def run_tests():
    """Run system tests"""
    print("\n🧪 Running system tests...")
    try:
        subprocess.check_call([sys.executable, "tests/test_system.py"])
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Some tests failed - check output above")
        return False

def start_services():
    """Start API and GUI"""
    print("\n🚀 Starting services...")
    
    # Start API server
    print("Starting API server...")
    api_process = subprocess.Popen(
        [sys.executable, "api/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a moment for API to start
    import time
    time.sleep(3)
    
    # Start GUI
    print("Starting GUI...")
    try:
        subprocess.run([sys.executable, "gui/main.py"])
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        api_process.terminate()

def main():
    """Main quick start flow"""
    print_banner()
    
    print("\n🔍 Checking system requirements...\n")
    
    # Run checks
    checks = [
        ("Python Version", check_python_version),
        ("Directories", create_directories),
        ("Environment File", check_env_file),
    ]
    
    all_good = True
    for check_name, check_func in checks:
        if not check_func():
            all_good = False
    
    if not all_good:
        print("\n❌ Some checks failed. Please fix the issues above.")
        
        # Offer to create venv
        if not check_venv():
            response = input("\nCreate virtual environment? (y/n): ")
            if response.lower() == 'y':
                print("Creating virtual environment...")
                subprocess.check_call([sys.executable, "-m", "venv", "venv"])
                print("\n✅ Virtual environment created!")
                print("\nActivate it with:")
                print("  Windows: venv\\Scripts\\activate")
                print("  Mac/Linux: source venv/bin/activate")
                print("\nThen run this script again.")
                return
    
    # Check for virtual environment
    if not check_venv():
        print("\n⚠️  Strongly recommend using a virtual environment!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Install dependencies
    response = input("\nInstall dependencies? (y/n): ")
    if response.lower() == 'y':
        if not install_dependencies():
            return
    
    # Setup database
    response = input("\nSetup database? (y/n): ")
    if response.lower() == 'y':
        if not setup_database():
            print("⚠️  Database setup failed but continuing...")
    
    # Run tests
    response = input("\nRun system tests? (y/n): ")
    if response.lower() == 'y':
        run_tests()
    
    # Final checks
    if not os.path.exists(".env"):
        print("\n❌ Please create .env file with your API keys!")
        print("   Copy .env.example to .env and edit it")
        return
    
    # Check if API keys are set
    with open(".env", "r") as f:
        env_content = f.read()
        if "your_binance_api_key_here" in env_content:
            print("\n⚠️  Please edit .env and add your Binance API keys!")
            print("   Get them from: https://www.binance.com/en/my/settings/api-management")
            response = input("\nStart anyway in demo mode? (y/n): ")
            if response.lower() != 'y':
                return
    
    # Start services
    print("\n" + "="*60)
    print("✅ Setup complete! Ready to jack into the Matrix!")
    print("="*60)
    print("\nStarting Arasaka Neural-Net Trading Matrix...")
    print("\nDefault PIN: 2077")
    print("Press Ctrl+C to stop\n")
    
    try:
        start_services()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTry starting services manually:")
        print("  Terminal 1: python api/app.py")
        print("  Terminal 2: python gui/main.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Disconnecting from the Matrix...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

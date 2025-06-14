#!/usr/bin/env python3
"""
Arasaka Neural-Net Trading Matrix - Quick Start Script
This script automates the entire setup process
"""
import os
import sys
import subprocess
import shutil
import platform
import time
from pathlib import Path

class Colors:
    """Cyberpunk color scheme for terminal output"""
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Print cyberpunk ASCII banner"""
    banner = f"""{Colors.MAGENTA}
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
    {Colors.RESET}"""
    print(banner)

def print_status(message, status="info"):
    """Print colored status messages"""
    if status == "success":
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    elif status == "error":
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")
    else:
        print(f"{Colors.CYAN}→ {message}{Colors.RESET}")

def check_python_version():
    """Check if Python version is 3.9+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} detected", "success")
        return True
    else:
        print_status(f"Python 3.9+ required. You have {version.major}.{version.minor}", "error")
        return False

def check_virtual_env():
    """Check if running in virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_status("Virtual environment active", "success")
        return True
    else:
        print_status("Not in virtual environment", "warning")
        return False

def create_virtual_env():
    """Create virtual environment"""
    print_status("Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print_status("Virtual environment created", "success")

        # Get activation command based on OS
        if platform.system() == "Windows":
            activate_cmd = "venv\\Scripts\\activate"
        else:
            activate_cmd = "source venv/bin/activate"

        print_status(f"Activate with: {activate_cmd}", "info")
        return True
    except Exception as e:
        print_status(f"Failed to create virtual environment: {e}", "error")
        return False

def create_directory_structure():
    """Create all necessary directories"""
    directories = [
        "api", "config", "core", "emergency", "gui", "market",
        "ml", "scripts", "tests", "trading", "utils",
        "data/historical", "logs", "backups", "docs"
    ]

    print_status("Creating directory structure...")

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

        # Create __init__.py for Python packages
        if "/" not in directory and directory not in ["logs", "backups", "docs"]:
            init_file = Path(directory) / "__init__.py"
            init_file.touch(exist_ok=True)

    print_status("Directory structure created", "success")

def create_env_file():
    """Create .env file from example"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print_status("Created .env from example", "success")
            print_status("Please edit .env and add your API keys!", "warning")
        else:
            # Create basic .env file
            env_content = """# Arasaka Neural-Net Trading Matrix Configuration
# Add your API keys here

# Binance API (Get from https://www.binance.com/en/my/settings/api-management)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# Trading Mode
TESTNET=true

# Other APIs (Optional)
CRYPTOPANIC_API_KEY=
X_API_KEY=
X_API_SECRET=
X_ACCESS_TOKEN=
X_ACCESS_TOKEN_SECRET=
"""
            with open(".env", "w") as f:
                f.write(env_content)
            print_status("Created default .env file", "success")
            print_status("Edit .env and add your Binance API keys!", "warning")
    else:
        print_status(".env file already exists", "success")

def install_dependencies():
    """Install Python dependencies"""
    print_status("Installing dependencies...")

    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print_status("Dependencies installed", "success")

        # Special note for TA-Lib
        print_status("Note: TA-Lib may require system-level installation", "warning")
        if platform.system() == "Windows":
            print_status("Windows: Download TA-Lib from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib", "info")
        elif platform.system() == "Darwin":
            print_status("macOS: Run 'brew install ta-lib' first", "info")
        else:
            print_status("Linux: Run 'sudo apt-get install ta-lib' first", "info")

        return True

    except subprocess.CalledProcessError as e:
        print_status(f"Dependency installation failed: {e}", "error")
        print_status("Try manually: pip install -r requirements.txt", "info")
        return False

def setup_database():
    """Initialize the database"""
    print_status("Setting up database...")

    try:
        # Run database setup script
        subprocess.check_call([sys.executable, "scripts/setup_database.py"])
        print_status("Database initialized", "success")
        return True
    except Exception as e:
        print_status(f"Database setup failed: {e}", "error")
        print_status("Will be created on first run", "warning")
        return True  # Not critical

def download_sample_data():
    """Download sample historical data"""
    print_status("Preparing historical data directory...")

    # Create sample data info file
    sample_info = """# Historical Data Directory

Place your historical OHLCV data CSV files here.

## Recommended Sources:
1. CryptoDataDownload (Free): https://www.cryptodatadownload.com
2. Binance Data: https://data.binance.vision/

## CSV Format Required:
timestamp,open,high,low,close,volume

## File Naming:
- Binance_BTCUSDT_hourly.csv
- Binance_ETHUSDT_hourly.csv

The bot will automatically import these on startup.
"""

    with open("data/historical/README.md", "w") as f:
        f.write(sample_info)

    print_status("Historical data directory ready", "success")
    print_status("Download data from CryptoDataDownload.com", "info")

def run_system_test():
    """Run basic system tests"""
    print_status("Running system tests...")

    try:
        result = subprocess.run([sys.executable, "tests/test_system.py"],
                                capture_output=True, text=True)

        if result.returncode == 0:
            print_status("System tests passed", "success")
            return True
        else:
            print_status("Some tests failed - check output", "warning")
            print(result.stdout)
            return False
    except Exception as e:
        print_status(f"Test execution failed: {e}", "warning")
        return True  # Not critical

def launch_application():
    """Launch the trading application"""
    print_status("Launching Arasaka Neural-Net Trading Matrix...")

    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.MAGENTA}SYSTEM READY - JACK INTO THE MATRIX!{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    print_status("Starting API server...", "info")

    # Start API server in background
    api_process = subprocess.Popen([sys.executable, "api/app.py"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

    # Wait for API to start
    time.sleep(3)

    print_status("Starting GUI...", "info")
    print_status(f"Default PIN: {Colors.BOLD}2077{Colors.RESET}", "warning")

    try:
        # Launch GUI
        subprocess.run([sys.executable, "gui/main.py"])
    except KeyboardInterrupt:
        print_status("\nShutting down...", "info")
    finally:
        # Cleanup
        api_process.terminate()

def main():
    """Main setup flow"""
    print_banner()

    print(f"\n{Colors.CYAN}Starting Automated Setup...{Colors.RESET}\n")

    # System checks
    checks = [
        ("Python Version", check_python_version),
        ("Directory Structure", create_directory_structure),
        ("Environment File", create_env_file),
    ]

    all_good = True
    for check_name, check_func in checks:
        if not check_func():
            all_good = False

    if not all_good:
        print_status("\nSome checks failed. Fix issues and run again.", "error")
        sys.exit(1)

    # Virtual environment check
    if not check_virtual_env():
        response = input(f"\n{Colors.YELLOW}Create virtual environment? (recommended) [y/n]: {Colors.RESET}")
        if response.lower() == 'y':
            if create_virtual_env():
                print(f"\n{Colors.GREEN}Virtual environment created!{Colors.RESET}")
                print(f"{Colors.YELLOW}Please activate it and run this script again.{Colors.RESET}")
                sys.exit(0)

    # Install dependencies
    response = input(f"\n{Colors.CYAN}Install dependencies? [y/n]: {Colors.RESET}")
    if response.lower() == 'y':
        if not install_dependencies():
            print_status("Fix dependency issues and run again", "error")
            sys.exit(1)

    # Setup database
    response = input(f"\n{Colors.CYAN}Initialize database? [y/n]: {Colors.RESET}")
    if response.lower() == 'y':
        setup_database()

    # Prepare data directory
    download_sample_data()

    # Run tests
    response = input(f"\n{Colors.CYAN}Run system tests? [y/n]: {Colors.RESET}")
    if response.lower() == 'y':
        run_system_test()

    # Final launch
    print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Setup Complete!{Colors.RESET}")
    print(f"{Colors.GREEN}{'='*60}{Colors.RESET}\n")

    # Check if API keys are configured
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()
            if "your_api_key_here" in content:
                print_status("Don't forget to add your Binance API keys to .env!", "warning")
                print_status("Get them from: https://www.binance.com/en/my/settings/api-management", "info")

    response = input(f"\n{Colors.MAGENTA}Launch Trading Matrix? [y/n]: {Colors.RESET}")
    if response.lower() == 'y':
        launch_application()
    else:
        print(f"\n{Colors.CYAN}To start manually:{Colors.RESET}")
        print("1. Terminal 1: python api/app.py")
        print("2. Terminal 2: python gui/main.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
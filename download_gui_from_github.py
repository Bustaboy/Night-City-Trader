#!/usr/bin/env python3
"""Download gui/main.py from your GitHub repository"""
import os
import requests
import shutil
from datetime import datetime

print("🌐 GitHub GUI Downloader for Arasaka Trading Matrix")
print("="*60)

# Get GitHub details from user
print("\n📋 Please provide your GitHub repository details:")
print("Example: If your repo URL is https://github.com/johndoe/arasaka-trading")
print("Then username is 'johndoe' and repo name is 'arasaka-trading'\n")

username = input("Enter your GitHub username: ").strip()
repo_name = input("Enter your repository name: ").strip()
branch = input("Enter branch name (press Enter for 'main'): ").strip() or "main"

# Construct the raw file URL
raw_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/{branch}/gui/main.py"

print(f"\n🔗 Downloading from: {raw_url}")

# Backup current file if it exists
gui_file = "gui/main.py"
if os.path.exists(gui_file):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"gui/main.py.backup_{timestamp}"
    shutil.copy2(gui_file, backup_file)
    print(f"📁 Backed up current file to: {backup_file}")

try:
    # Download the file
    print("\n⬇️  Downloading gui/main.py...")
    response = requests.get(raw_url, timeout=30)
    
    if response.status_code == 200:
        # Check if it's actually the GUI file
        content = response.text
        if "Arasaka Neural-Net Trading Matrix GUI" in content and "class TradingApp" in content:
            # Save the file
            with open(gui_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Get file stats
            lines = content.count('\n')
            size_kb = len(content) / 1024
            
            print(f"\n✅ Successfully downloaded gui/main.py!")
            print(f"📊 File stats:")
            print(f"   - Lines: {lines:,}")
            print(f"   - Size: {size_kb:.1f} KB")
            
            # Verify key components
            components = [
                ("Login system", "def _create_login_screen"),
                ("Trading tab", "def _create_trading_tab"),
                ("Dashboard tab", "def _create_dashboard_tab"),
                ("DeFi tab", "def _create_defi_tab"),
                ("Settings tab", "def _create_settings_tab"),
                ("Onboarding tab", "def _create_onboarding_tab"),
                ("P&L Display", "class ProfitLossDisplay"),
                ("Auto-trading", "class AutoTradingIndicator"),
                ("Trade notifications", "class TradeNotification"),
                ("Cyberpunk theme", "_apply_modern_cyberpunk_theme")
            ]
            
            print("\n🔍 Verifying components:")
            for name, signature in components:
                if signature in content:
                    print(f"   ✓ {name}")
                else:
                    print(f"   ✗ {name} (missing)")
            
            print("\n🚀 You can now run: python gui/main.py")
            print("📌 Default PIN: 2077")
            
        else:
            print("\n❌ Downloaded file doesn't appear to be the GUI file")
            print("   It might be a different file or the repository structure is different")
            
            # Try alternative paths
            print("\n🔍 Trying alternative paths...")
            alt_paths = [
                f"https://raw.githubusercontent.com/{username}/{repo_name}/{branch}/gui/main.py",
                f"https://raw.githubusercontent.com/{username}/{repo_name}/{branch}/src/gui/main.py",
                f"https://raw.githubusercontent.com/{username}/{repo_name}/{branch}/Night-City-Trader/gui/main.py"
            ]
            
            for alt_url in alt_paths:
                if alt_url != raw_url:
                    print(f"   Trying: {alt_url}")
                    try:
                        alt_response = requests.get(alt_url, timeout=10)
                        if alt_response.status_code == 200 and "TradingApp" in alt_response.text:
                            print(f"   ✓ Found at: {alt_url}")
                            with open(gui_file, 'w', encoding='utf-8') as f:
                                f.write(alt_response.text)
                            print("\n✅ Successfully downloaded from alternative path!")
                            break
                    except:
                        continue
            
    elif response.status_code == 404:
        print("\n❌ File not found (404)")
        print("\nPossible issues:")
        print("1. Check your username and repository name")
        print("2. Make sure the repository is public")
        print("3. Verify the branch name (main vs master)")
        print("4. Check if gui/main.py exists in your repo")
        
        # Provide direct link for manual check
        repo_url = f"https://github.com/{username}/{repo_name}"
        print(f"\n🌐 Check your repository: {repo_url}")
        
    else:
        print(f"\n❌ Download failed with status code: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ Network error: {e}")
    print("\nTroubleshooting:")
    print("1. Check your internet connection")
    print("2. Verify the repository exists and is public")
    print("3. Try accessing the URL in your browser:")
    print(f"   {raw_url}")

# Offer alternative download method
print("\n" + "="*60)
print("📝 Alternative Manual Download Method:")
print("="*60)
print(f"\n1. Go to: https://github.com/{username}/{repo_name}")
print("2. Navigate to: gui/main.py")
print("3. Click the 'Raw' button")
print("4. Save the page as: C:\\Night-City-Trader\\gui\\main.py")

# Create a batch script for Windows users
batch_content = f"""@echo off
echo Downloading gui/main.py from GitHub...
curl -L -o gui\\main.py {raw_url}
if %errorlevel% == 0 (
    echo Successfully downloaded!
) else (
    echo Download failed!
)
pause
"""

with open("download_gui.bat", "w") as f:
    f.write(batch_content)

print(f"\n💾 Created download_gui.bat for Windows command prompt")

# Create a PowerShell script as well
ps_content = f"""Write-Host "Downloading gui/main.py from GitHub..." -ForegroundColor Cyan
try {{
    Invoke-WebRequest -Uri "{raw_url}" -OutFile "gui\\main.py"
    Write-Host "Successfully downloaded!" -ForegroundColor Green
}} catch {{
    Write-Host "Download failed: $_" -ForegroundColor Red
}}
Read-Host "Press Enter to continue"
"""

with open("download_gui.ps1", "w") as f:
    f.write(ps_content)

print(f"💾 Created download_gui.ps1 for PowerShell")
print("\n🎯 You can also try:")
print("   - Windows: .\\download_gui.bat")
print("   - PowerShell: .\\download_gui.ps1")
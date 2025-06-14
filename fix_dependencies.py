#!/usr/bin/env python3
"""Fix all dependency conflicts for the trading bot"""
import subprocess
import sys

print("🔧 Fixing Dependency Conflicts")
print("="*60)

# The issue: numpy 2.3.0 is incompatible with tensorflow and scipy
print("\n📋 Current issues:")
print("- numpy 2.3.0 is too new for TensorFlow and scipy")
print("- ml-dtypes version mismatch")
print("- tensorboard version mismatch")

print("\n🚀 Installing compatible versions...")

# First, uninstall problematic packages
print("\n1️⃣ Cleaning up conflicting packages...")
packages_to_reinstall = [
    "numpy",
    "tensorflow",
    "scipy",
    "ml-dtypes",
    "tensorboard"
]

for package in packages_to_reinstall:
    print(f"   Uninstalling {package}...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Install compatible versions
print("\n2️⃣ Installing compatible versions...")
compatible_packages = [
    "numpy==1.26.4",  # Compatible with both TensorFlow 2.17 and scipy
    "scipy==1.14.1",
    "tensorflow==2.17.0",  # More stable version
    "ml-dtypes==0.5.0",
    "tensorboard==2.17.0",
    "matplotlib==3.9.2",
    "pandas==2.2.3",
    "requests==2.32.3",
    "ccxt==4.3.24",
    "scikit-learn==1.5.1",
    "xgboost==2.1.1"
]

for package in compatible_packages:
    print(f"   Installing {package}...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ⚠️  Warning: {package} installation had issues")
    else:
        print(f"   ✅ {package} installed")

print("\n3️⃣ Verifying installation...")
# Test imports
test_imports = [
    "numpy",
    "pandas", 
    "matplotlib",
    "tensorflow",
    "scipy",
    "sklearn",
    "xgboost"
]

all_good = True
for module in test_imports:
    try:
        __import__(module)
        print(f"   ✅ {module} - OK")
    except ImportError as e:
        print(f"   ❌ {module} - FAILED: {e}")
        all_good = False

if all_good:
    print("\n✅ All dependencies fixed!")
else:
    print("\n⚠️  Some imports still failing")
    print("Try: pip install -r requirements.txt")

print("\n" + "="*60)
print("🎮 Next Steps:")
print("="*60)
print("\n1. Run the Canvas fix:")
print("   python fix_canvas_methods.py")
print("\n2. Start the GUI:")
print("   python start_matrix.py")
print("\n3. Or directly:")
print("   python gui/main.py")
print("\n📌 Default PIN: 2077")
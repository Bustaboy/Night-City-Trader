#!/usr/bin/env python3
"""Quick fix for GUI startup issues"""
import os
import shutil

print("🔧 ARASAKA GUI QUICK FIX")
print("="*50)

# Fix 1: Clean up tax_rates.csv
print("\n1. Fixing tax_rates.csv...")
tax_content = """country,rate
US,0.30
Germany,0.25
UK,0.20
Portugal,0.00
France,0.30
Japan,0.20
Canada,0.50
Australia,0.45
Italy,0.26
Spain,0.19
Netherlands,0.30
Switzerland,0.00
Brazil,0.15
Mexico,0.20
Argentina,0.35
South Africa,0.45
India,0.30
Singapore,0.00
China,0.20
Russia,0.13
"""

# Backup original
if os.path.exists("config/tax_rates.csv"):
    shutil.copy("config/tax_rates.csv", "config/tax_rates.csv.backup")

# Write fixed version
with open("config/tax_rates.csv", "w") as f:
    f.write(tax_content)
print("✅ Tax rates fixed!")

# Fix 2: Add Canvas patch to gui/main.py
print("\n2. Patching Canvas method...")

# Read current gui/main.py
with open("gui/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Check if patch already exists
if "tk.Canvas.create_rounded_rectangle" not in content:
    # Find where to insert (after imports)
    import_end = content.find("class Colors:")
    if import_end == -1:
        import_end = content.find("class ProfitLossDisplay")
    
    # Create patch
    patch = '''
# Canvas monkey patch for rounded rectangles
def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
    """Create a rounded rectangle on canvas"""
    points = []
    for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                 (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                 (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                 (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
        points.extend([x, y])
    return self.create_polygon(points, smooth=True, **kwargs)

tk.Canvas.create_rounded_rectangle = create_rounded_rectangle

'''
    
    # Insert patch
    content = content[:import_end] + patch + content[import_end:]
    
    # Backup and write
    shutil.copy("gui/main.py", "gui/main.py.backup")
    with open("gui/main.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Canvas method patched!")
else:
    print("✅ Canvas patch already exists!")

print("\n" + "="*50)
print("✅ ALL FIXES APPLIED!")
print("\nNow run: python gui/main.py")
print("\nPIN: 2077")
print("="*50)
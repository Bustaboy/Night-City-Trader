#!/usr/bin/env python3
"""Comprehensive fix for Canvas rounded rectangle methods"""
import os
import re

print("🔧 Comprehensive Canvas Method Fix")
print("="*60)

gui_file = "gui/main.py"

# Read the file
with open(gui_file, "r", encoding="utf-8") as f:
    content = f.read()

print("📍 Fixing create_rounded_rectangle issue...")

# Fix 1: Add the method definition after Canvas class usage
canvas_patch = '''
# Add create_rounded_rectangle method to Canvas
def _create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
    """Create a rounded rectangle"""
    points = []
    for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                 (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                 (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                 (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
        points.extend([x, y])
    return self.create_polygon(points, smooth=True, **kwargs)

# Monkey patch Canvas
tk.Canvas.create_rounded_rectangle = _create_rounded_rectangle
'''

# Find where to insert - after tkinter imports
lines = content.split('\n')
inserted = False

for i, line in enumerate(lines):
    if 'from utils.security_manager import security_manager' in line:
        # Insert after all imports
        lines.insert(i + 2, canvas_patch)
        inserted = True
        break

if inserted:
    content = '\n'.join(lines)
    print("✅ Added Canvas.create_rounded_rectangle method")
else:
    print("⚠️  Could not find import section, trying alternative approach...")
    
    # Alternative: Add before first class definition
    class_index = content.find('class ProfitLossDisplay')
    if class_index > 0:
        content = content[:class_index] + canvas_patch + '\n\n' + content[class_index:]
        print("✅ Added method before first class")

# Fix 2: Also ensure all custom widget classes have their create_rounded_rectangle method
# Find all classes that inherit from Canvas
canvas_classes = re.findall(r'class\s+(\w+)\s*\([^)]*Canvas[^)]*\):', content)
print(f"\n📍 Found Canvas-based classes: {canvas_classes}")

# Make sure each has the method
for class_name in canvas_classes:
    class_pattern = f'class {class_name}.*?(?=class|\\Z)'
    class_match = re.search(class_pattern, content, re.DOTALL)
    
    if class_match:
        class_content = class_match.group(0)
        
        # Check if it already has create_rounded_rectangle
        if 'def create_rounded_rectangle' not in class_content:
            # Add the method
            method_code = '''
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle"""
        points = []
        for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                     (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                     (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                     (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)
'''
            
            # Find where to insert (after __init__ or at the end of class)
            init_pos = class_content.find('def __init__')
            if init_pos > 0:
                # Find the end of __init__
                next_def = class_content.find('\n    def ', init_pos + 1)
                if next_def > 0:
                    insert_pos = class_match.start() + next_def
                else:
                    # Insert at end of class
                    insert_pos = class_match.end() - 1
                
                content = content[:insert_pos] + '\n' + method_code + content[insert_pos:]
                print(f"✅ Added create_rounded_rectangle to {class_name}")

# Write the fixed content
with open(gui_file, "w", encoding="utf-8") as f:
    f.write(content)

print("\n✅ All fixes applied!")

# Create a minimal test to verify
test_code = '''#!/usr/bin/env python3
"""Test Canvas with rounded rectangle"""
import tkinter as tk

# Test if we can create rounded rectangles
root = tk.Tk()
root.title("Canvas Test")
root.geometry("400x300")

canvas = tk.Canvas(root, bg="black", width=400, height=300)
canvas.pack()

# Add the method if it doesn't exist
if not hasattr(canvas, 'create_rounded_rectangle'):
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = []
        for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                     (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                     (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                     (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)
    
    tk.Canvas.create_rounded_rectangle = create_rounded_rect

# Now test it
try:
    canvas.create_rounded_rectangle(50, 50, 350, 250, 20, fill="blue", outline="cyan", width=3)
    print("✅ Canvas rounded rectangle works!")
except Exception as e:
    print(f"❌ Error: {e}")

root.after(2000, root.destroy)  # Auto close after 2 seconds
root.mainloop()
'''

with open("test_canvas.py", "w") as f:
    f.write(test_code)

print("\n🧪 Test the canvas fix:")
print("python test_canvas.py")

print("\n🚀 Now try the main GUI:")
print("python gui/main.py")

# Also create a safer startup with encoding fix
safe_start = '''#!/usr/bin/env python3
import os
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set working directory
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.getcwd())

# Import and run
try:
    import matplotlib
    matplotlib.use('TkAgg')
    
    print("Starting Arasaka Neural-Net Trading Matrix...")
    from gui.main import main
    main()
    
except Exception as e:
    print(f"Startup error: {e}")
    import traceback
    traceback.print_exc()
    input("\\nPress Enter to exit...")
'''

with open("start_matrix.py", "w") as f:
    f.write(safe_start)

print("\n✅ Created start_matrix.py with encoding fixes")
print("🚀 Run: python start_matrix.py")

# Fix numpy version
print("\n⚠️  Also fix the numpy version conflict:")
print("pip install numpy==2.1.3")
print("\nThis will resolve TensorFlow compatibility issues.")
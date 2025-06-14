#!/usr/bin/env python3
"""Restore the original gui/main.py from backup or recreate it"""
import os
import shutil

print("🔄 Restoring original GUI file...")

gui_file = "gui/main.py"
backup_file = "gui/main.py.backup"

# First, try to restore from backup
if os.path.exists(backup_file):
    print("📂 Found backup file, restoring...")
    shutil.copy2(backup_file, gui_file)
    print("✅ Restored from backup!")
else:
    print("❌ No backup found")
    print("📥 Please restore gui/main.py from your GitHub repository")
    print("\nInstructions:")
    print("1. Go to your GitHub repository")
    print("2. Navigate to gui/main.py")
    print("3. Click 'Raw' button")
    print("4. Copy all content")
    print("5. Replace your local gui/main.py with this content")
    print("\nOR download directly:")
    print("1. In GitHub, navigate to gui/main.py")
    print("2. Click the download button")
    print("3. Save to C:\\Night-City-Trader\\gui\\main.py")
    
    # Create a minimal working GUI as emergency fallback
    response = input("\nCreate emergency minimal GUI? [y/n]: ")
    if response.lower() == 'y':
        print("\n🚨 Creating emergency minimal GUI...")
        
        minimal_gui = '''#!/usr/bin/env python3
"""Emergency Minimal GUI - Basic Trading Interface"""
import tkinter as tk
from tkinter import messagebox
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MinimalTradingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Arasaka Trading Matrix - Emergency Mode")
        self.root.geometry("800x600")
        self.root.configure(bg="#0a0a23")
        
        # Header
        header = tk.Label(
            root,
            text="ARASAKA NEURAL-NET TRADING MATRIX",
            bg="#0a0a23",
            fg="#ff00ff",
            font=("Consolas", 20, "bold")
        )
        header.pack(pady=20)
        
        # Status
        status = tk.Label(
            root,
            text="⚠️ Running in Emergency Mode ⚠️",
            bg="#0a0a23",
            fg="#ff0066",
            font=("Consolas", 16)
        )
        status.pack(pady=10)
        
        # Info
        info_text = """
The main GUI file is corrupted.

To restore full functionality:
1. Download the original gui/main.py from your GitHub repository
2. Replace the corrupted file
3. Restart the application

This emergency GUI provides basic functionality only.
        """
        
        info = tk.Label(
            root,
            text=info_text,
            bg="#0a0a23",
            fg="#00ffcc",
            font=("Consolas", 12),
            justify=tk.LEFT
        )
        info.pack(pady=20, padx=40)
        
        # Basic buttons
        button_frame = tk.Frame(root, bg="#0a0a23")
        button_frame.pack(pady=20)
        
        # Test API button
        test_btn = tk.Button(
            button_frame,
            text="Test API Connection",
            bg="#ff00ff",
            fg="#0a0a23",
            font=("Consolas", 14, "bold"),
            padx=20,
            pady=10,
            command=self.test_api
        )
        test_btn.pack(pady=10)
        
        # Exit button
        exit_btn = tk.Button(
            button_frame,
            text="Exit",
            bg="#ff0066",
            fg="#ffffff",
            font=("Consolas", 14, "bold"),
            padx=40,
            pady=10,
            command=root.quit
        )
        exit_btn.pack(pady=10)
        
    def test_api(self):
        """Test API connection"""
        try:
            import requests
            response = requests.get("http://127.0.0.1:8000/health", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Success", "API is running!")
            else:
                messagebox.showwarning("Warning", f"API returned status {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"API connection failed: {str(e)}")

def main():
    root = tk.Tk()
    app = MinimalTradingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
'''
        
        # Save emergency GUI
        emergency_file = "gui/main_emergency.py"
        with open(emergency_file, "w", encoding="utf-8") as f:
            f.write(minimal_gui)
        
        # Replace main.py with emergency version
        shutil.copy2(emergency_file, gui_file)
        
        print(f"✅ Created emergency GUI at {gui_file}")
        print("🚀 You can now run: python gui/main.py")
        print("\n⚠️  Remember to restore the full GUI from GitHub when possible!")

print("\n📋 Next steps:")
print("1. If backup restored: python gui/main.py")
print("2. If no backup: Follow instructions above to restore from GitHub")
print("3. Emergency GUI: Will provide basic functionality")
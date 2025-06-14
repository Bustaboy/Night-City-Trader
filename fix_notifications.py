#!/usr/bin/env python3
"""Quick fix for notifications appearing when minimized"""
import os

print("🔧 Fixing notification issue...")

gui_file = "gui/main.py"

# Read the current file
with open(gui_file, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: Main notification method
old_notification = """def _show_notification(self, message, type="info"):
        \"\"\"Show modern notification popup\"\"\"
        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)"""

new_notification = """def _show_notification(self, message, type="info"):
        \"\"\"Show modern notification popup\"\"\"
        # Don't show if minimized
        if self.root.state() == 'iconic' or self.root.state() == 'withdrawn':
            return
            
        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', False)  # Changed to False"""

content = content.replace(old_notification, new_notification)

# Fix 2: Trade notifications
old_trade_notif = """class TradeNotification(tk.Toplevel):
    \"\"\"Animated trade notification popup\"\"\"
    def __init__(self, parent, trade_data):
        super().__init__(parent)
        
        self.overrideredirect(True)
        self.attributes('-topmost', True)"""

new_trade_notif = """class TradeNotification(tk.Toplevel):
    \"\"\"Animated trade notification popup\"\"\"
    def __init__(self, parent, trade_data):
        super().__init__(parent)
        
        # Don't show if minimized
        if parent.state() == 'iconic' or parent.state() == 'withdrawn':
            self.destroy()
            return
            
        self.overrideredirect(True)
        self.attributes('-topmost', False)  # Changed to False"""

content = content.replace(old_trade_notif, new_trade_notif)

# Fix 3: Auto-trading notifications in _start_auto_trading
old_auto_trading = """# Show trade notification
                    TradeNotification(self.root, trade_data)"""

new_auto_trading = """# Show trade notification (only if not minimized)
                    if self.root.state() not in ['iconic', 'withdrawn']:
                        TradeNotification(self.root, trade_data)"""

content = content.replace(old_auto_trading, new_auto_trading)

# Fix 4: Update the notification positioning to be less intrusive
old_position = """# Position in top-right corner
        notification.update_idletasks()
        width = notification.winfo_width()
        height = notification.winfo_height()
        x = self.root.winfo_x() + self.root.winfo_width() - width - 30
        y = self.root.winfo_y() + 120"""

new_position = """# Position in top-right corner (only if window is visible)
        notification.update_idletasks()
        width = notification.winfo_width()
        height = notification.winfo_height()
        
        # Get screen dimensions
        screen_width = notification.winfo_screenwidth()
        screen_height = notification.winfo_screenheight()
        
        # Position relative to app window if visible, otherwise use screen corner
        if self.root.state() == 'normal':
            x = self.root.winfo_x() + self.root.winfo_width() - width - 30
            y = self.root.winfo_y() + 120
        else:
            x = screen_width - width - 30
            y = 120"""

content = content.replace(old_position, new_position)

# Save the fixed file
with open(gui_file, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Notifications fixed!")
print("\n📋 Changes made:")
print("- Notifications won't show when app is minimized")
print("- Removed 'always on top' behavior") 
print("- Trade notifications check window state")
print("- Better positioning logic for notifications")
print("\n🚀 Restart the GUI to apply changes!")
print("\nRun: python gui/main.py")
#!/usr/bin/env python3
"""
Arasaka Neural-Net Trading Matrix - GUI Launcher
Ensures proper working directory and environment setup
"""
import os
import sys
import subprocess

def main():
    # Set working directory to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 60)
    print("Starting Arasaka Neural-Net Trading Matrix...")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    
    # Check if database directory exists
    os.makedirs("logs", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    
    # Patch Canvas if needed
    import tkinter as tk
    canvas_create_rounded_rectangle = lambda self, x1, y1, x2, y2, radius, **kwargs: self.create_polygon(
        [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
         (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
         (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
         (x1 + radius, y2), (x1, y2), (x1, y2 - radius)],
        smooth=True, **kwargs
    )
    
    if not hasattr(tk.Canvas, 'create_rounded_rectangle'):
        tk.Canvas.create_rounded_rectangle = canvas_create_rounded_rectangle
        print("Canvas methods patched")
    
    print("Default PIN: 2077")
    print("=" * 60)
    print("\nIMPORTANT: Make sure the API server is running!")
    print("In another terminal, run: python run_api.py")
    print("=" * 60)
    
    try:
        # Import and run main GUI
        from gui.main import main
        main()
    except Exception as e:
        print(f"\nError: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()

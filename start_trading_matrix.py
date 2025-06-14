#!/usr/bin/env python3
import os
import sys

# Fix path
if os.path.basename(os.getcwd()) != 'Night-City-Trader':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if os.path.basename(os.getcwd()) == 'gui':
        os.chdir('..')

sys.path.insert(0, os.getcwd())

# Fix matplotlib
import matplotlib
matplotlib.use('TkAgg')

# Now import and run
try:
    from gui.main import main
    main()
except Exception as e:
    print(f"\nStartup Error: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")

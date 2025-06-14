#!/bin/bash

# Arasaka Neural-Net Trading Matrix Launcher for Mac/Linux

echo "============================================================"
echo "     ARASAKA NEURAL-NET TRADING MATRIX v2.0"
echo "     Stack Eddies in the Net!"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3.9+ first"
    exit 1
fi

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Start API server in background
echo "Starting API Server..."
gnome-terminal --title="Arasaka API Server" -- bash -c "cd '$DIR' && python3 run_api.py; exec bash" 2>/dev/null || \
xterm -title "Arasaka API Server" -e "cd '$DIR' && python3 run_api.py; bash" 2>/dev/null || \
osascript -e "tell app \"Terminal\" to do script \"cd '$DIR' && python3 run_api.py\"" 2>/dev/null || \
(python3 run_api.py &)

# Wait for API to start
echo "Waiting for API to initialize..."
sleep 5

# Start GUI
echo ""
echo "Starting Trading Matrix GUI..."
gnome-terminal --title="Arasaka Trading GUI" -- bash -c "cd '$DIR' && python3 run_gui.py; exec bash" 2>/dev/null || \
xterm -title "Arasaka Trading GUI" -e "cd '$DIR' && python3 run_gui.py; bash" 2>/dev/null || \
osascript -e "tell app \"Terminal\" to do script \"cd '$DIR' && python3 run_gui.py\"" 2>/dev/null || \
python3 run_gui.py

echo ""
echo "============================================================"
echo "Both windows should now be open:"
echo "- API Server (keep this running)"
echo "- Trading GUI (use PIN: 2077)"
echo ""
echo "To stop: Close both windows or press Ctrl+C"
echo "============================================================"
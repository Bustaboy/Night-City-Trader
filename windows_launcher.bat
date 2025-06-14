@echo off
title Arasaka Neural-Net Trading Matrix Launcher
color 0A

echo ============================================================
echo     ARASAKA NEURAL-NET TRADING MATRIX v2.0
echo     Stack Eddies in the Net!
echo ============================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

echo Starting API Server...
start "Arasaka API Server" cmd /k "cd /d %~dp0 && python run_api.py"

:: Wait for API to start
echo Waiting for API to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Starting Trading Matrix GUI...
start "Arasaka Trading GUI" cmd /k "cd /d %~dp0 && python run_gui.py"

echo.
echo ============================================================
echo Both windows should now be open:
echo - API Server (keep this running)
echo - Trading GUI (use PIN: 2077)
echo.
echo To stop: Close both windows
echo ============================================================
echo.
pause
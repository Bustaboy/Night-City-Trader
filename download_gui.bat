@echo off
echo Downloading gui/main.py from GitHub...
curl -L -o gui\main.py https://raw.githubusercontent.com/Bustaboy/Night-City-Trader/main/gui/main.py
if %errorlevel% == 0 (
    echo Successfully downloaded!
) else (
    echo Download failed!
)
pause

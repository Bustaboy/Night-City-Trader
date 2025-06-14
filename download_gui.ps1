Write-Host "Downloading gui/main.py from GitHub..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Bustaboy/Night-City-Trader/main/gui/main.py" -OutFile "gui\main.py"
    Write-Host "Successfully downloaded!" -ForegroundColor Green
} catch {
    Write-Host "Download failed: $_" -ForegroundColor Red
}
Read-Host "Press Enter to continue"

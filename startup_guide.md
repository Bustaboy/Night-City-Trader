# 🚀 Arasaka Neural-Net Trading Matrix - Startup Guide

## Quick Start (2 Steps)

### Step 1: Start the API Server
Open a terminal/command prompt:
```bash
cd C:\Night-City-Trader
python run_api.py
```
Leave this running! You should see:
```
Starting Arasaka API Server...
API will run on: http://127.0.0.1:8000
```

### Step 2: Start the GUI
Open a **SECOND** terminal/command prompt:
```bash
cd C:\Night-City-Trader
python run_gui.py
```

**Default PIN: 2077**

---

## Common Issues & Solutions

### 1. "unable to open database file"
**Solution**: The launcher scripts now handle this. Just use `run_gui.py` instead of running `gui/main.py` directly.

### 2. "Training failed: 500 Server Error"
**Solution**: Make sure the API server is running FIRST (Step 1 above).

### 3. "NameError: cannot access free variable 'e'"
**Solution**: This has been fixed in the updated GUI code. The lambda functions now properly capture exception messages.

### 4. Missing dependencies
```bash
pip install -r requirements.txt
```

---

## First Time Setup

1. **Configure API Keys** (in GUI):
   - Go to Onboarding tab
   - Enter your Binance API credentials
   - Select risk level
   - Click "JACK INTO THE MATRIX"

2. **Enable Features**:
   - Go to Netrunner Dashboard
   - Check "Enable Auto-Trading"
   - Other features are pre-enabled

3. **Start Trading**:
   - Go to Trading Matrix tab
   - Click "SCAN OPTIMAL" to find best pair
   - Use BUY/SELL buttons or let auto-trading handle it

---

## File Structure Required

Make sure you have these launcher files in `C:\Night-City-Trader`:
- `run_api.py` - Starts the backend server
- `run_gui.py` - Starts the GUI interface

---

## Troubleshooting

### GUI won't start?
1. Check Python version: `python --version` (need 3.9+)
2. Check if API is running on http://127.0.0.1:8000
3. Check logs in `logs/trading.log`

### API won't start?
1. Check if port 8000 is already in use
2. Make sure all dependencies are installed
3. Check `.env` file exists (copy from `.env.example`)

### Can't login?
- Default PIN is **2077**
- PIN is case-sensitive
- After 5 failed attempts, wait 5 minutes

---

## Pro Tips

1. **Always start API first, then GUI**
2. **Use testnet mode** until you're comfortable
3. **Monitor the logs** in `logs/trading.log`
4. **Backup regularly** - the bot does this daily but manual backups are good too
5. **Start small** - use minimum amounts until you trust the system

---

## Emergency Stop

If something goes wrong:
1. Click the **red KILL SWITCH button** in the GUI
2. Or delete the file `EMERGENCY_STOP_ACTIVE` to unlock
3. Or just close both terminal windows

---

Ready to jack into the Matrix and stack those Eddies! 🤖💰
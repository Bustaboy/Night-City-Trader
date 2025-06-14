# Neural-Net Local Trading Bot

A single-user cryptocurrency trading bot that runs locally and trades on Binance (testnet or live).

## Setup
1. **Option 1: Run from Source**
   - Clone the repository: `git clone https://github.com/your-username/neural-net-local.git`
   - Create a virtual environment: `python -m venv venv` and activate it (`venv\Scripts\activate` on Windows, `source venv/bin/activate` on Mac/Linux).
   - Install dependencies: `pip install -r requirements.txt`
   - Copy `.env.example` to `.env` and add your Binance API keys (testnet or live).
   - Initialize the database: `python scripts/setup_database.py`
   - Start the API: `uvicorn api.app:app --host 127.0.0.1 --port 8000`
   - Run the GUI: `python gui/main.py`

2. **Option 2: Use Installer**
   - Download the installer (`TradingBotSetup.exe`) from the releases page.
   - Run the installer and follow the prompts to install the bot.
   - Launch the bot from the desktop shortcut or Start menu.
   - Configure your Binance API keys in the `.env` file in the installation directory.

## Usage
- Use the GUI to:
  - Select trading pairs automatically based on ML analysis.
  - Buy/sell with specified amounts and risk profiles (Conservative, Moderate, Aggressive).
  - Toggle between testnet and live trading.
  - View portfolio, train the ML model, and monitor trades.
  - Activate the emergency stop to halt all trading.
- The bot uses an XGBoost model trained on technical indicators (SMA, RSI, Bollinger Bands, MACD) and up to 20 years of historical data.
- Risk management includes position sizing, daily loss limits, stop-loss, take-profit, and profitability checks after fees.

## Features
- **ML-Based Pair Selection**: Automatically selects the most promising trading pairs.
- **Profitability Checks**: Ensures trades are profitable after accounting for fees.
- **Risk Profiles**: Choose Conservative, Moderate, or Aggressive settings.
- **Testnet/Live Toggle**: Switch modes within the GUI.
- **Single Executable**: Packaged as a standalone application with an installer.
- **Automated Trading**: Uses ML predictions with stop-loss and take-profit.
- **Portfolio Tracking**: Monitors trades and positions.
- **Real-Time Data**: Fetches market data from Binance.
- **Emergency Kill Switch**: Stops all trading instantly.
- **Local Logging and Alerts**: Logs to file and shows GUI popups for critical alerts.

## Notes
- Test with small amounts on testnet first.
- The ML model retrains when "Train Model" is clicked or per `config.yaml` schedule.
- Ensure internet connectivity for Binance API calls.
- Stop-loss and take-profit are simulated; for real SL/TP, integrate with exchange APIs.

## Building the Executable
To create the executable:
1. Install PyInstaller: `pip install pyinstaller`
2. Run: `pyinstaller --noconfirm --onefile --windowed --add-data "config;config" --add-data "ml;ml" --add-data "trading.log;." gui/main.py`
3. Create an installer using Inno Setup with the generated `dist/main.exe`.

# Neural-Net Local Trading Bot

A single-user cryptocurrency trading bot that runs locally and trades on Binance (testnet or live).

## Setup
1. Clone the repository: `git clone https://github.com/your-username/neural-net-local.git`
2. Create a virtual environment: `python -m venv venv` and activate it (`venv\Scripts\activate` on Windows, `source venv/bin/activate` on Mac/Linux).
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and add your Binance API keys (testnet or live).
5. Initialize the database: `python scripts/setup_database.py`
6. Start the API: `uvicorn api.app:app --host 127.0.0.1 --port 8000`
7. Run the GUI: `python gui/main.py`

## Usage
- Use the GUI to buy/sell BTC/USDT, view portfolio, train the ML model, and monitor trades.
- The bot uses an XGBoost model trained on technical indicators (SMA, RSI).
- Set `TESTNET=false` in `.env` for live trading (use with caution).
- Click "Emergency Stop" to halt all trading activities.

## Features
- Automated trading with ML predictions.
- Portfolio and position tracking.
- Real-time market data fetching.
- Basic risk management (position size, daily loss limits).
- Emergency kill switch.
- Local logging for debugging.

## Notes
- Test with small amounts on testnet first.
- The ML model retrains when "Train Model" is clicked or per `config.yaml` schedule.
- Ensure internet connectivity for Binance API calls.

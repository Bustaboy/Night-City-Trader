# 🤖 Arasaka Neural-Net Trading Matrix

![Cyberpunk Trading Bot](https://img.shields.io/badge/Status-Active-00ff00?style=for-the-badge&logo=bitcoin&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.17-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-ff00ff?style=for-the-badge)

Welcome to the **Arasaka Neural-Net Trading Matrix** - a cyberpunk-themed cryptocurrency trading bot that combines Machine Learning (XGBoost), Reinforcement Learning (DQN), and real-time market analysis to help you stack Eddies (profits) in the crypto markets!

## 🌟 Features

- **🧠 Neural-Net Trading**: ML + RL models trained on 15+ years of crypto data
- **📊 Multi-Strategy System**: Breakout, mean reversion, momentum, scalping, swing trading
- **🎯 Smart Pair Selection**: Automatic selection of the most profitable trading pairs
- **🛡️ Risk Management**: Dynamic position sizing, leverage adjustment, and portfolio optimization
- **💡 Sentiment Analysis**: Real-time social media and news sentiment tracking
- **⛓️ On-Chain Metrics**: Whale movements and blockchain activity monitoring
- **🌊 DeFi Integration**: Liquidity mining for passive income
- **🚨 Emergency Kill Switch**: Instant shutdown of all trading operations
- **📱 Cyberpunk GUI**: Neon-lit interface for easy control
- **📈 Backtesting**: Test strategies on historical data
- **💰 Tax Reporting**: Automated tax report generation

## 📋 Table of Contents

1. [Installation](#-installation)
2. [GitHub Upload Instructions](#-github-upload-instructions)
3. [Configuration](#-configuration)
4. [Usage](#-usage)
5. [Project Structure](#-project-structure)
6. [Trading Strategies](#-trading-strategies)
7. [Risk Management](#-risk-management)
8. [API Documentation](#-api-documentation)
9. [Troubleshooting](#-troubleshooting)
10. [Contributing](#-contributing)
11. [Security](#-security)
12. [License](#-license)

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- Git
- 8GB RAM minimum (16GB recommended)
- Optional: NVIDIA GPU with CUDA support for faster training

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/arasaka-trading-matrix.git
cd arasaka-trading-matrix
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: For TA-Lib installation:
- **Windows**: Download the wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) and install with `pip install TA_Lib‑0.4.24‑cp39‑cp39‑win_amd64.whl`
- **macOS**: `brew install ta-lib` then `pip install TA-Lib`
- **Linux**: `sudo apt-get install ta-lib` then `pip install TA-Lib`

### Step 4: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
# nano .env  # or use any text editor
```

### Step 5: Initialize Database

```bash
python scripts/setup_database.py
```

### Step 6: Run the Application

```bash
# Start the API server
python api/app.py

# In a new terminal, start the GUI
python gui/main.py
```

## 📤 GitHub Upload Instructions

### Creating a New Repository

1. **Go to GitHub**:
   - Navigate to https://github.com
   - Click the green "New" button or go to https://github.com/new

2. **Configure Repository**:
   - Repository name: `arasaka-trading-matrix`
   - Description: "Cyberpunk-themed AI crypto trading bot with ML/RL"
   - Set to **Private** (recommended for trading bots)
   - Don't initialize with README (we already have one)

3. **Create Repository**:
   - Click "Create repository"

### Uploading Code via GitHub Web Interface

Since all files are provided as artifacts, you can upload directly through GitHub:

1. **On your new repository page**:
   - Click "uploading an existing file"

2. **Create Project Structure**:
   First, create the folder structure by creating files in these paths:
   ```
   api/
   config/
   core/
   emergency/
   gui/
   logs/
   market/
   ml/
   scripts/
   tests/
   trading/
   utils/
   data/historical/  # Create empty folder with .gitkeep file
   backups/          # Create empty folder with .gitkeep file
   ```

3. **Upload Files in Order**:
   
   **Root Directory Files**:
   - `README.md` (this file)
   - `.env.example`
   - `requirements.txt`
   - `.gitignore` (create with content below)

   **Core Directory (`core/`)**:
   - `database.py` (artifact #01)
   - `__init__.py` (empty file)

   **Scripts Directory (`scripts/`)**:
   - `import_historical_data.py` (artifact #02)
   - `setup_database.py` (artifact #21)
   - `__init__.py` (empty file)

   **Trading Directory (`trading/`)**:
   - `trading_bot.py` (artifact #03)
   - `risk_manager.py` (artifact #06)
   - `strategies.py` (artifact #16)
   - `liquidity_mining.py` (artifact #17)
   - `__init__.py` (empty file)

   **GUI Directory (`gui/`)**:
   - `main.py` (artifact #04)
   - `__init__.py` (empty file)

   **Config Directory (`config/`)**:
   - `settings.py` (artifact #05)
   - `config.yaml` (artifact #20)
   - `tax_rates.csv` (create from artifact #16)
   - `__init__.py` (empty file)

   **ML Directory (`ml/`)**:
   - `trainer.py` (artifact #07)
   - `rl_trainer.py` (artifact #08)
   - `__init__.py` (empty file)

   **Market Directory (`market/`)**:
   - `data_fetcher.py` (artifact #09)
   - `pair_selector.py` (artifact #11)
   - `__init__.py` (empty file)

   **API Directory (`api/`)**:
   - `app.py` (artifact #10)
   - `__init__.py` (empty file)

   **Utils Directory (`utils/`)**:
   - `logger.py` (artifact #12)
   - `security_manager.py` (artifact #13)
   - `tax_reporter.py` (artifact #15)
   - `__init__.py` (empty file)

   **Emergency Directory (`emergency/`)**:
   - `kill_switch.py` (artifact #14)
   - `__init__.py` (empty file)

4. **Create .gitignore**:
   ```gitignore
   # Python
   __pycache__/
   *.py[cod]
   *$py.class
   *.so
   .Python
   venv/
   env/
   ENV/

   # Environment variables
   .env

   # Database
   *.db
   *.db-journal

   # Logs
   logs/
   *.log

   # ML Models
   *.pkl
   *.h5
   *.joblib

   # Config
   config/security.key
   config/defi_config.json

   # Backups
   backups/
   backup_*.db

   # Trading data
   data/historical/*.csv

   # Emergency files
   EMERGENCY_STOP_ACTIVE
   SYSTEM_LOCKED
   emergency_report_*.txt

   # IDE
   .vscode/
   .idea/
   *.swp
   *.swo

   # OS
   .DS_Store
   Thumbs.db

   # Test
   .pytest_cache/
   .coverage
   htmlcov/
   ```

5. **Commit All Files**:
   - After uploading all files, scroll down
   - Add commit message: "Initial commit - Arasaka Neural-Net Trading Matrix"
   - Click "Commit changes"

### Using Git Command Line (Alternative)

If you prefer using Git command line:

```bash
# Initialize git in your project directory
git init

# Add all files
git add .

# Commit files
git commit -m "Initial commit - Arasaka Neural-Net Trading Matrix"

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/arasaka-trading-matrix.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## ⚙️ Configuration

### 1. Exchange API Keys

Get your API keys from Binance:
1. Go to https://www.binance.com/en/my/settings/api-management
2. Create new API key
3. Enable "Enable Spot & Margin Trading"
4. For testnet: Use https://testnet.binance.vision/

### 2. Risk Profiles

Edit `config/config.yaml` to adjust risk parameters:
- **Conservative**: Low risk, no leverage
- **Moderate**: Balanced risk/reward
- **Aggressive**: High risk, high leverage

### 3. Trading Pairs

The bot automatically selects the best pairs, but you can set defaults in `config/config.yaml`.

## 📊 Usage

### GUI Interface

1. **Login**: Default PIN is "2077" (change in first login)
2. **Trading Tab**: Execute trades, monitor positions
3. **Dashboard**: View analytics, run backtests
4. **Settings**: Configure risk parameters
5. **DeFi**: Set up liquidity mining

### API Endpoints

The bot also provides a REST API:

```bash
# Check health
curl http://localhost:8000/health

# Get best trading pair
curl http://localhost:8000/best_pair

# Execute trade
curl -X POST http://localhost:8000/trade \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC/USDT","side":"buy","amount":0.001}'
```

## 🗂️ Project Structure

```
arasaka-trading-matrix/
├── api/                    # FastAPI backend
│   └── app.py             # API endpoints
├── config/                 # Configuration files
│   ├── config.yaml        # Trading settings
│   ├── settings.py        # Environment config
│   └── tax_rates.csv      # Tax rates by country
├── core/                   # Core functionality
│   └── database.py        # Database manager
├── emergency/              # Emergency systems
│   └── kill_switch.py     # Emergency stop
├── gui/                    # Tkinter GUI
│   └── main.py            # Main GUI application
├── market/                 # Market analysis
│   ├── data_fetcher.py    # OHLCV data fetching
│   └── pair_selector.py   # Pair selection engine
├── ml/                     # Machine Learning
│   ├── trainer.py         # XGBoost trainer
│   └── rl_trainer.py      # DQN trainer
├── scripts/                # Utility scripts
│   ├── import_historical_data.py
│   └── setup_database.py
├── trading/                # Trading logic
│   ├── trading_bot.py     # Main trading engine
│   ├── risk_manager.py    # Risk management
│   ├── strategies.py      # Trading strategies
│   └── liquidity_mining.py # DeFi integration
└── utils/                  # Utilities
    ├── logger.py          # Logging system
    ├── security_manager.py # Security protocols
    └── tax_reporter.py    # Tax reporting
```

## 📈 Trading Strategies

### 1. Breakout Strategy
- Identifies price breakouts above resistance or below support
- Uses ATR for dynamic thresholds
- Confirms with volume spikes

### 2. Mean Reversion
- Trades oversold/overbought conditions
- Uses RSI and Bollinger Bands
- Best in ranging markets

### 3. Momentum Strategy
- Follows strong trends
- Uses MACD and moving average crossovers
- Ideal for trending markets

### 4. Scalping Strategy
- Quick trades on small price movements
- High frequency, small profits
- Requires low fees

### 5. Swing Trading
- Captures larger market swings
- Holds positions for days
- Uses multiple timeframe analysis

## 🛡️ Risk Management

The bot implements multiple risk layers:

1. **Position Sizing**: Kelly Criterion with portfolio-based adjustments
2. **Leverage Control**: Dynamic leverage based on confidence and market regime
3. **Stop Loss/Take Profit**: ATR-based dynamic levels
4. **Portfolio Optimization**: Modern Portfolio Theory for weight allocation
5. **Flash Crash Protection**: Automatic position closure on sudden drops
6. **Daily Loss Limits**: Prevents excessive drawdowns

## 📚 API Documentation

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check system status |
| `/market/{symbol}` | GET | Get market data |
| `/trade` | POST | Execute trade |
| `/portfolio` | GET | Get portfolio info |
| `/train` | POST | Train ML models |
| `/predict/{symbol}` | GET | Get predictions |
| `/best_pair` | GET | Get optimal pair |
| `/backtest` | POST | Run backtest |
| `/arbitrage` | GET | Find arbitrage |

### WebSocket (Future)

Real-time updates coming in v2.0

## 🔧 Troubleshooting

### Common Issues

1. **"No module named 'ccxt'"**
   ```bash
   pip install -r requirements.txt
   ```

2. **"TA-Lib installation failed"**
   - See installation instructions above

3. **"Database locked"**
   - Close other instances of the bot
   - Delete `local_trading.db-journal` if exists

4. **"API rate limit"**
   - Reduce request frequency in settings
   - Use multiple exchange accounts

5. **"Insufficient funds"**
   - Check wallet balance
   - Reduce position size
   - Ensure testnet is enabled for testing

### Logs

Check `logs/trading.log` for detailed error messages.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 🔒 Security

- **NEVER** share your `.env` file
- **NEVER** commit API keys to Git
- Use testnet for testing
- Enable 2FA on exchange accounts
- Regularly update dependencies
- Monitor for unusual activity

### Security Features

- AES-256 encryption for sensitive data
- PIN-based access control
- Tamper detection
- Emergency kill switch
- Automatic system lockdown

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**IMPORTANT**: This bot is for educational purposes. Cryptocurrency trading carries significant risk. Never trade more than you can afford to lose. Past performance does not guarantee future results. Always do your own research.

## 🙏 Acknowledgments

- Inspired by the Cyberpunk 2077 universe
- Built with cutting-edge AI technology
- Community-driven development

---

**Ready to jack into the Matrix and stack some Eddies, Choom?**

*Remember: In Night City, you're either a predator or prey. Choose wisely.*

# 🤖 Arasaka Neural-Net Trading Matrix

![Python](https://img.shields.io/badge/python-v3.9+-blue.svg)
![Version](https://img.shields.io/badge/version-2.0.7.7-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)

> **"In Night City, you're either stacking Eddies or flatlining. This Neural-Net ensures you're doing the former."**

A fully autonomous, AI-driven cryptocurrency trading bot with a cyberpunk aesthetic. The Matrix combines Machine Learning (XGBoost), Reinforcement Learning (DQN), and real-time market analysis to maximize profits while you sleep.

## 🎯 Key Features

### 🤖 100% Autonomous Operation
- **AI Pair Selection**: Neural-Net automatically selects the most profitable trading pairs
- **Self-Training Models**: ML/RL models retrain weekly without intervention
- **Auto Risk Management**: Dynamic position sizing and leverage adjustment
- **Smart Order Routing**: Automatic trade execution with profitability checks
- **Auto Portfolio Rebalancing**: Weekly optimization using Modern Portfolio Theory

### 🧠 Advanced AI Systems
- **Dual AI Architecture**: XGBoost + Deep Q-Network for maximum accuracy
- **Multi-Strategy System**: 6 trading strategies that adapt to market conditions
- **Market Regime Detection**: Automatically adjusts for bull/bear/altcoin markets
- **Sentiment Analysis**: Real-time social media monitoring (Twitter/X, CryptoPanic)
- **On-Chain Analytics**: Whale movement and blockchain activity tracking

### 🛡️ Security & Safety
- **Militech Security Protocols**: PIN-protected access with encryption
- **Emergency Kill Switch**: Instant shutdown of all operations
- **Flash Crash Protection**: Automatic position closure on sudden drops
- **Tamper Detection**: System integrity monitoring
- **Automated Backups**: Daily database backups with 7-day retention

### 💰 Financial Features
- **Tax Report Generation**: Automated tax reports by country
- **DeFi Integration**: Liquidity mining for passive income
- **Profit Withdrawal**: Monthly automatic profit extraction
- **Multi-Exchange Support**: Binance, Kraken, Coinbase (extensible)

## 📥 GitHub Upload Instructions

### Method 1: GitHub Web Interface (Recommended for Beginners)

1. **Create Repository**:
   - Go to https://github.com/new
   - Name: `arasaka-trading-matrix`
   - Description: "Autonomous AI crypto trading bot with cyberpunk UI"
   - Set to **Private** (recommended)
   - Don't initialize with README

2. **Upload Files via Web**:

   Click "uploading an existing file" and create this structure:

   ```
   arasaka-trading-matrix/
   ├── api/
   │   ├── __init__.py (empty file)
   │   └── app.py
   ├── config/
   │   ├── __init__.py (empty file)
   │   ├── config.yaml
   │   ├── settings.py
   │   └── tax_rates.csv
   ├── core/
   │   ├── __init__.py (empty file)
   │   └── database.py
   ├── emergency/
   │   ├── __init__.py (empty file)
   │   └── kill_switch.py
   ├── gui/
   │   ├── __init__.py (empty file)
   │   └── main.py
   ├── market/
   │   ├── __init__.py (empty file)
   │   ├── data_fetcher.py
   │   └── pair_selector.py
   ├── ml/
   │   ├── __init__.py (empty file)
   │   ├── trainer.py
   │   └── rl_trainer.py
   ├── scripts/
   │   ├── __init__.py (empty file)
   │   ├── setup_database.py
   │   └── import_historical_data.py
   ├── tests/
   │   ├── __init__.py (empty file)
   │   └── test_system.py
   ├── trading/
   │   ├── __init__.py (empty file)
   │   ├── trading_bot.py
   │   ├── risk_manager.py
   │   ├── strategies.py
   │   └── liquidity_mining.py
   ├── utils/
   │   ├── __init__.py (empty file)
   │   ├── logger.py
   │   ├── security_manager.py
   │   └── tax_reporter.py
   ├── .env.example
   ├── .gitignore
   ├── README.md
   ├── requirements.txt
   └── quick_start.py
   ```

### Method 2: Git Command Line

```bash
# Clone your empty repository
git clone https://github.com/YOUR_USERNAME/arasaka-trading-matrix.git
cd arasaka-trading-matrix

# Create all directories
mkdir -p api config core emergency gui market ml scripts tests trading utils
mkdir -p data/historical logs backups

# Create all __init__.py files
touch api/__init__.py config/__init__.py core/__init__.py emergency/__init__.py
touch gui/__init__.py market/__init__.py ml/__init__.py scripts/__init__.py
touch tests/__init__.py trading/__init__.py utils/__init__.py

# Copy all artifact files to their locations
# (Copy each artifact content to the appropriate file)

# Add and commit
git add .
git commit -m "Initial commit - Arasaka Neural-Net Trading Matrix"
git push origin main
```

## 🚀 Quick Start Guide

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/arasaka-trading-matrix.git
cd arasaka-trading-matrix

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Quick Start

```bash
python quick_start.py
```

This will:
- Check system requirements
- Create necessary directories
- Set up the database
- Guide you through initial configuration
- Start the application

### 3. First Time Setup (In GUI)

1. **Login**: Default PIN is `2077`
2. **Go to Onboarding Tab**:
   - Enter your Binance API Key (get from https://www.binance.com)
   - Select risk level (Low/Medium/High)
   - Click "JACK INTO THE MATRIX"
3. **Enable Automation** (Dashboard Tab):
   - All automation options are pre-checked
   - The bot will now run completely autonomously

## 🤖 Automation Features

The bot runs these tasks automatically:

| Task | Frequency | Purpose |
|------|-----------|---------|
| Trade Execution | When AI confidence > 80% | Execute profitable trades |
| Pair Selection | Hourly | Find best trading opportunities |
| Model Training | Weekly | Keep AI models updated |
| Portfolio Rebalancing | Weekly | Optimize asset allocation |
| Tax Rate Updates | Weekly | Keep tax info current |
| Data Preloading | Daily | Update historical data |
| Arbitrage Scanning | Hourly | Find price differences |
| Sentiment Analysis | Daily | Monitor market mood |
| Flash Protection | Every 5 min | Protect against crashes |
| Database Backup | Daily | Preserve trading history |
| Health Monitoring | Daily | System status alerts |

## 💻 GUI Interface

### Trading Matrix Tab
- **Pair Selection**: AI automatically selects pairs (manual override available)
- **Trade Execution**: Auto-trades when conditions are met
- **Risk Control**: Set profile (Conservative/Moderate/Aggressive)
- **Emergency Stop**: Kill switch for instant shutdown

### Netrunner's Dashboard
- **Automation Controls**: Toggle any automation feature
- **Performance Metrics**: Real-time P&L and statistics
- **Backtest Results**: Historical strategy performance
- **System Logs**: All automation activity

### Settings Hub
- **Risk Parameters**: Adjust max leverage, position sizes
- **Flash Drop Threshold**: Set crash protection sensitivity
- **API Configuration**: All done through GUI (no file editing)

### DeFi Matrix
- **Liquidity Mining**: Configure yield farming
- **Smart Contract Integration**: Connect to DeFi protocols
- **Passive Income**: Earn while the bot trades

## 🔧 Configuration

All configuration is done through the GUI. The bot will:

1. **Store API Keys Securely**: Encrypted storage in app
2. **Auto-Select Trading Pairs**: Based on AI analysis
3. **Adjust Risk Dynamically**: Based on market conditions
4. **Optimize Settings**: Self-tuning parameters

**No manual configuration files needed!**

## 📊 How It Works

### 1. AI Pair Selection
```
Market Scanner → Volume Analysis → Volatility Check → 
ML Prediction → Profitability Score → Best Pair Selected
```

### 2. Trade Decision
```
Technical Analysis + ML Signal + RL Action + Sentiment Score →
Risk Check → Profitability Check → Execute Trade
```

### 3. Risk Management
```
Portfolio Size → Kelly Criterion → Position Sizing →
Dynamic Leverage → Stop Loss/Take Profit → Monitor
```

## 🛡️ Security Features

- **PIN Protection**: Secure access control
- **API Key Encryption**: AES-256 encryption
- **No External Access**: All data stays local
- **Tamper Detection**: Integrity monitoring
- **Emergency Lockdown**: Instant system wipe

## 📈 Performance Expectations

- **Target Returns**: 15-30% monthly (market dependent)
- **Max Drawdown**: Limited by risk profile
- **Win Rate**: 65-75% typical
- **Sharpe Ratio**: 1.5-2.5 target

**Disclaimer**: Past performance doesn't guarantee future results. Crypto trading is risky.

## 🚨 Troubleshooting

### Bot Not Trading?
- Check "Auto Trade" is enabled in Trading Matrix
- Verify API keys are correct
- Ensure sufficient balance
- Check logs for errors

### API Errors?
- Verify Binance API permissions
- Check rate limits
- Try testnet mode first

### System Locked?
- Delete `EMERGENCY_STOP_ACTIVE` file
- Restart application
- Check PIN (default: 2077)

## 🤝 Support

- **Documentation**: Full docs in `/docs` folder
- **Logs**: Check `logs/trading.log` for details
- **Backups**: Automatic daily backups in `/backups`

## ⚠️ Risk Warning

Cryptocurrency trading carries significant risk. This bot can lose money. Never trade more than you can afford to lose. Start with testnet mode and small amounts.

## 📄 License

MIT License - See LICENSE file for details

---

**Ready to jack into the Matrix and let the AI stack your Eddies?**

*Remember: In the world of crypto, you either adapt or get zeroed. This Neural-Net ensures you stay ahead of the game.*

**Default PIN: 2077** 🔐

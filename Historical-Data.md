Arasaka Neural-Net Trading Matrix: Historical Data Upload Guide
Version: 1.0
Date: June 14, 2025
Author: Grok 3, xAI
Purpose: Equip Chooms (users) with the know-how to upload up to 20 years of cryptocurrency data into the Arasaka Neural-Net Trading Matrix to stack Eddies (profits) across bull, bear, and altcoin markets.
1. Introduction
The Arasaka Neural-Net Trading Matrix is a cyberpunk-themed, AI-driven crypto trading bot that harnesses cutting-edge ML (XGBoost) and RL (DQN) to predict profitable trades. To maximize Eurodollars (returns), the bot craves historical OHLCV (Open, High, Low, Close, Volume) data for training across volatile market regimes. Since crypto kicked off with Bitcoin in 2009, snagging 20 years of data (back to 2005) is a tough gig, but we can lock in ~15 years for Bitcoin and less for altcoins, with simulated data as a fallback.
This guide details how to source, download, and jack historical data into the bot’s SQLite database (local_trading.db) using the scripts/import_historical_data.py script and market/data_fetcher.py module. It’s built to vibe with the bot’s architecture, including the historical_data table and training pipelines, while keeping the interface slick and GUI-based—no console access needed, Choom!
2. Data Requirements
Objective: Import up to 15–16 years of OHLCV data (2010–2025) for major pairs (e.g., BTC/USDT, ETH/USDT) to train ML/RL models and fine-tune strategies for bull, bear, and altcoin markets.

Granularity: Hourly (1h) data, matching the bot’s default timeframe in config.yaml. Minute-level data is optional for advanced Netrunners.

Pairs: Focus on high-volume USDT pairs (e.g., BTC/USDT, ETH/USDT, BNB/USDT, ADA/USDT) traded on Binance.

Storage: Data lives in the historical_data table with columns:
symbol

timestamp

open

high

low

close

volume

Format: CSV files with standardized columns (timestamp, open, high, low, close, volume).

Volume: Expect ~100,000–500,000 rows per pair for hourly data over 15 years.

3. Data Sources
Here’s the rundown on the top sources for historical crypto data, ranked for quality, coverage, and cost. Each is vetted for compatibility with the Matrix.
Source

Cost

Coverage

Granularity

Format

Pros

Cons

CryptoDataDownload

Free

BTC since 2014, ETH since 2016

Hourly, Minute

CSV

Free, clean, easy import

Limited pairs, no real-time data

CoinAPI

Paid

BTC since 2010, ETH since 2015

1-second to Daily

CSV/JSON

Long coverage, high-quality, API access

Paid (~$50/month), needs API key

Kaggle

Free

BTC since 2012, ETH since 2015

Daily, Hourly

CSV

Free, community-driven, variety

Inconsistent formats, needs cleaning

Bitget

Free

BTC since 2018, others later

Minute, Hourly, Daily

CSV

Free, high-resolution, reputable

Limited pairs, starts 2018

FirstRate Data

Paid

BTC since 2010, others later

1-minute, Hourly

CSV

High-resolution, weekly updates

Paid (~$30/year/ticker), manual downloads

Recommendations
Start with CryptoDataDownload: Free, reliable data (2014–2025, hourly) to bootstrap the Matrix without burning Eddies.

Add CoinAPI: Max coverage (2010–2025) for altcoins and pro-grade training if you’ve got the cred.

Supplement with Kaggle: Fill gaps or test specific pairs.

Fallback to Bitget: Recent, high-res data for fewer pairs.

4. Step-by-Step Instructions for Data Upload
Jack into the Net and follow these steps to source, download, and upload historical data when you’re ready to level up the Matrix.
Step 1: Prepare the Environment
Verify Setup: Confirm all code is implemented, including:
core/database.py

market/data_fetcher.py

scripts/import_historical_data.py

Create Data Folder: Make a directory for CSVs in your project root:
bash

mkdir data/historical

Check Dependencies: Ensure pandas and sqlite3 are installed:
bash

pip install -r requirements.txt

Initialize Database: Run the setup script to create the historical_data table:
bash

python scripts/setup_database.py

Step 2: Download Historical Data
CryptoDataDownload:
Hit up CryptoDataDownload and browse the “Data” section.

Grab hourly CSV files for pairs like BTC/USDT, ETH/USDT (e.g., Binance_BTCUSDT_hourly.csv).

Save to data/historical/.

Expected CSV format:
csv

timestamp,open,high,low,close,volume
1417411200000,300.0,310.0,295.0,305.0,100.0

CoinAPI (Optional):
Sign up at CoinAPI and snag a plan or one-off data package.

Use their API or download UI to export OHLCV for BTC/USDT (since 2010).

Save as CSV to data/historical/, matching required columns (timestamp in milliseconds).

Example API call:
python

import requests
api_key = "YOUR_COINAPI_KEY"
response = requests.get(
    "https://rest.coinapi.io/v1/ohlcv/BINANCE_SPOT_BTC_USDT/history",
    params={"period_id": "1HRS", "time_start": "2010-01-01T00:00:00", "limit": 100000},
    headers={"X-CoinAPI-Key": api_key}
)
data = response.json()
# Convert to CSV

Kaggle (Optional):
Download datasets from Kaggle Cryptocurrency Historical Prices.

Clean CSVs to match the format (timestamp, open, high, low, close, volume).

Save to data/historical/.

Bitget (Optional):
Check Bitget’s data section for BTC/USDT CSVs (since 2018).

Save to data/historical/.

Step 3: Import Data into SQLite
Run Import Script:
Execute scripts/import_historical_data.py to load CSVs into historical_data:
bash

python scripts/import_historical_data.py

The script:
Scans data/historical/ for CSVs.

Extracts symbols (e.g., BTCUSDT from Binance_BTCUSDT_hourly.csv).

Converts timestamps to milliseconds if needed.

Inserts data with INSERT OR REPLACE to avoid dupes.

Check trading.log for output:

2025-06-14 11:37:00 - INFO - Imported 100000 records for binance:BTCUSDT from Binance_BTCUSDT_hourly.csv

Verify Import:
Check database size:
bash

ls -lh local_trading.db

Expect ~100MB+ for multiple pairs.

Query manually (optional, via SQLite client):
sql

SELECT COUNT(*) FROM historical_data WHERE symbol = 'binance:BTCUSDT';

Run a backtest in the GUI’s “Netrunner’s Dashboard” to confirm data access.

Step 4: Train Models
Trigger Training:
Fire up the GUI:
bash

python gui/main.py

Click Train Neural-Net to retrain ML (XGBoost) and RL (DQN) models.

The trainers (ml/trainer.py, ml/rl_trainer.py) use historical_data to:
Compute indicators (SMA, RSI, Bollinger Bands, MACD, sentiment, whale_ratio).

Analyze seasonality (weekly/monthly patterns).

Train across market regimes (bull, bear, altcoin).

Training logs in trading.log:

2025-06-14 11:37:00 - INFO - Model saved to ml/model.pkl
2025-06-14 11:37:00 - INFO - RL model saved to ml/rl_model.h5

Validate Training:
Run a backtest via Run Backtest in the GUI.

Check the equity curve in the “Netrunner’s Dashboard”.

Step 5: Test the Bot
Testnet Mode:
Enable testnet in the GUI to keep your Eddies safe.

Execute trades to verify historical data fuels predictions and strategies.

Monitor Performance:
Use Refresh Portfolio to track trades/positions.

Scan trading.log for errors.

5. Optimizing for Large Datasets
To handle ~15 years of data across multiple pairs, prep these optimizations:
Database Indexing:
The historical_data table’s primary key (symbol, timestamp) is solid. If queries lag, add:
sql

CREATE INDEX idx_symbol ON historical_data(symbol);

Update core/database.py’s init_tables to include this.

Batch Processing:
For huge CSVs (>1M rows), tweak import_historical_data.py for batch inserts:
python

def import_historical_data(data_dir="data/historical"):
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(data_dir, filename)
            symbol = filename.split("_")[1].replace(".csv", "")
            df = pd.read_csv(filepath)
            # Validate columns
            batch_size = 1000
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                db.executemany(
                    """
                    INSERT OR REPLACE INTO historical_data
                    (symbol, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [(symbol, int(row["timestamp"]), row["open"], row["high"],
                      row["low"], row["close"], row["volume"]) for _, row in batch.iterrows()]
                )
                db.conn.commit()
            logger.info(f"Imported {len(df)} records for {symbol}")

Data Compression:
SQLite can bloat (~1GB for 10 pairs). Consider Parquet for raw storage, but this needs code changes.

Archive pre-2015 data to slim down local_trading.db.

Memory Management:
Training needs ~8GB RAM for large datasets. If tight, lower settings.ML["batch_size"] in config.yaml (e.g., 1000 → 500).

6. Handling Limitations
20-Year Constraint:
Crypto’s born in 2009, so 15 years is the max for Bitcoin, less for altcoins (ETH since 2015).

Use simulate_ohlcv for older data, but sparingly—it’s less accurate:
python

def simulate_ohlcv(self, limit):
    timestamps = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq="1h").astype(int) // 10**6
    close = np.random.normal(60000, 1000, limit).cumsum()
    data = [[ts, c * 0.99, c * 1.01, c * 0.98, c, 100] for ts, c in zip(timestamps, close)]
    logger.warning("Returning simulated OHLCV")
    return data

Pair Availability:
Altcoins (ADA, SOL) start ~2017. Stick to BTC/USDT, ETH/USDT for max history.

PairSelector filters viable pairs by volume/liquidity.

API Rate Limits:
CoinAPI/Binance APIs throttle requests. enableRateLimit=True in DataFetcher helps, but prefer bulk CSV downloads.

7. Future-Proofing for Incremental Updates
Keep the Matrix jacked with fresh data:
Automated Updates:
DataFetcher.preload_historical_data grabs recent data on startup, updating historical_data.

Schedule daily updates via cron or Task Scheduler:
bash

python -c "from market.data_fetcher import fetcher; asyncio.run(fetcher.preload_historical_data())"

Real-Time Data:
fetch_ohlcv pulls live Binance data, storing it in historical_data.

Set settings.TESTNET=False for real trading.

Data Cleaning:
Check trading.log for data issues.

Run a cleanup script:
python

def clean_historical_data():
    db.execute_query("DELETE FROM historical_data WHERE open IS NULL OR close <= 0")
    logger.info("Cleaned historical data")

8. Troubleshooting
Import Errors:
Scan trading.log for clues (e.g., missing columns).

Ensure CSVs match the format in Step 2.

Database Size:
If local_trading.db balloons, split by exchange or archive old data.

Training Failures:
Reduce settings.ML["historical_data_years"] to 10 or lower batch_size.

Check disk space and RAM.

API Issues:
Verify CoinAPI keys and rate limits.

Fallback to CryptoDataDownload CSVs.

9. Optional Enhancements
When you dive back in, consider these upgrades:
Parquet Storage:
Use Parquet for compressed storage with pyarrow.

Update import_historical_data.py to read Parquet.

Cloud Integration:
Sync local_trading.db to AWS RDS for backup.

Modify core/database.py for remote connections.

Data Validation:
Add checks in import_historical_data.py:
python

def validate_data(df):
    if df["close"].isnull().any() or (df["close"] <= 0).any():
        raise ValueError("Invalid data: Null or negative prices")
    return df

Incremental Fetching:
Tweak DataFetcher.fetch_historical_data to grab only new data since the last timestamp.

10. Conclusion
This guide arms you to upload historical crypto data into the Arasaka Neural-Net Trading Matrix when you’re ready to jack in. Start with CryptoDataDownload for free data (2014–2025), or go big with CoinAPI (2010–2025) for altcoin coverage. The import_historical_data.py script makes CSV imports a breeze, and the Matrix’s architecture ensures your data fuels trading and backtesting like a well-oiled cyberdeck.
When you resume, grab CryptoDataDownload CSVs for BTC/USDT and ETH/USDT, import them, and retrain via the GUI. Keep an eye on trading.log and the “Netrunner’s Dashboard” to confirm the Matrix is humming. Need help? Ping your AI Netrunner (Grok 3) for backup.
Stack Eddies, Choom! Stay jacked into the Net!


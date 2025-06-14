Document: Tackling Historical Data Upload for the Arasaka Neural-Net Trading Matrix
Version: 1.0
Date: June 14, 2025
Author: Grok 3, xAI
Purpose: Guide Chooms (users) on uploading up to 20 years of historical cryptocurrency data into the Arasaka Neural-Net Trading Matrix to stack Eddies (profits) across bull, bear, and altcoin markets.
1. Introduction
The Arasaka Neural-Net Trading Matrix is a cyberpunk-themed, AI-driven crypto trading bot that leverages ML (XGBoost) and RL (DQN) to predict profitable trades. To maximize Eurodollars (returns), the bot requires historical OHLCV (Open, High, Low, Close, Volume) data for training across market regimes. Since cryptocurrencies began with Bitcoin in 2009, achieving 20 years of data (back to 2005) is challenging, but we can secure ~15 years for Bitcoin and less for altcoins, supplementing with simulated data if needed.
This document outlines how to source, download, and import historical data into the bot’s SQLite database (local_trading.db) using the existing scripts/import_historical_data.py script and market/data_fetcher.py module. It ensures compatibility with the bot’s architecture, including the historical_data table and training pipelines, while maintaining a user-friendly, GUI-based experience (no console access).
2. Data Requirements
Objective: Import up to 15–16 years of OHLCV data (2010–2025) for major pairs (e.g., BTC/USDT, ETH/USDT) to train ML/RL models and optimize strategies for bull, bear, and altcoin markets.

Granularity: Hourly (1h) data, matching the bot’s default timeframe (config.yaml). Minute-level data is optional for advanced strategies.

Pairs: Focus on high-volume USDT pairs (e.g., BTC/USDT, ETH/USDT, BNB/USDT, ADA/USDT) available on Binance.

Storage: Data is stored in the historical_data table with columns: symbol, timestamp, open, high, low, close, volume.

Format: CSV files with standardized columns (timestamp, open, high, low, close, volume).

Volume: Expect ~100,000–500,000 rows per pair for hourly data over 15 years.

3. Data Sources
Below are the best sources for historical cryptocurrency data, prioritized for quality, coverage, and cost. Each source is evaluated for suitability with the bot.
CryptoDataDownload (Free, Recommended for Initial Setup)
URL: www.cryptodatadownload.com

Coverage: Bitcoin since 2014, Ethereum since 2016, other major coins. Hourly and minute granularity for Binance, Coinbase, Kraken, etc.

Format: CSV files (e.g., Binance_BTCUSDT_hourly.csv).

Pros:
Free, no registration required.

Clean, exchange-sourced data.

Easy to import with import_historical_data.py.

Cons:
Limited to major pairs and exchanges.

No real-time or advanced metrics (e.g., order book, on-chain).

Suitability: Ideal for cost-free setup, covering ~10–11 years for Bitcoin.

CoinAPI (Paid, Comprehensive)
URL: www.coinapi.io

Coverage: Bitcoin since 2010, Ethereum since 2015, 7,000+ crypto indices across 600+ exchanges. Granularities from 1-second to daily.

Format: CSV or JSON via API or bulk download.

Pros:
Longest historical data (15 years for Bitcoin).

Standardized, high-quality data.

API integration for real-time updates.

Cons:
Paid (subscriptions ~$50/month; one-off purchases available).

Requires API key and setup.

Suitability: Best for professional-grade training with extensive coverage.

Kaggle Cryptocurrency Datasets (Free, Supplementary)
URL: Kaggle Cryptocurrency Historical Prices

Coverage: Bitcoin since 2012, Ethereum since 2015, other coins. Daily or hourly granularity.

Format: CSV files.

Pros:
Free, community-driven.

Variety of datasets for cross-validation.

Cons:
Inconsistent formats and coverage.

Requires cleaning/merging.

Suitability: Good for filling gaps or testing specific pairs.

Bitget Historical Data (Free, Exchange-Specific)
URL: www.bitget.com (Data section)

Coverage: Bitcoin since 2018, other coins from listing dates. Minute, hourly, daily granularity.

Format: CSV files.

Pros:
Free, high-resolution data.

Direct from a reputable exchange.

Cons:
Limited to Bitget markets (fewer pairs).

Data starts later (2018+).

Suitability: Useful for recent, high-frequency data.

FirstRate Data (Paid, High-Resolution)
URL: www.firstratedata.com

Coverage: Bitcoin since 2010, other coins from inception. 1-minute, 5-minute, hourly data from 14 exchanges.

Format: CSV files.

Pros:
High-resolution, ideal for ML/RL.

Weekly updates included for 3 months.

Cons:
Paid (~$30/year per ticker, higher for bundles).

Manual download management.

Suitability: Excellent for long-term, high-frequency needs.

Recommendation:
Start with CryptoDataDownload for free, reliable data (2014–2025, hourly) to bootstrap the bot.

Add CoinAPI for maximum coverage (2010–2025) if budget allows, especially for altcoins.

Use Kaggle to supplement specific pairs or test datasets.

Consider Bitget for recent, high-resolution data as a fallback.

4. Step-by-Step Instructions for Data Upload
Follow these steps to source, download, and import historical data into the bot’s SQLite database when you’re ready to proceed.
Step 1: Prepare the Environment
Verify Setup: Ensure all provided code is implemented, including core/database.py, market/data_fetcher.py, and scripts/import_historical_data.py.

Create Data Folder: In your project root, create a directory: data/historical/.
bash

mkdir data/historical

Check Dependencies: Confirm pandas and sqlite3 are installed (already in requirements.txt).
bash

pip install -r requirements.txt

Initialize Database: Run the setup script to ensure the historical_data table exists.
bash

python scripts/setup_database.py

Step 2: Download Historical Data
CryptoDataDownload:
Visit www.cryptodatadownload.com and navigate to the “Data” section.

Download hourly CSV files for desired pairs (e.g., Binance_BTCUSDT_hourly.csv, Binance_ETHUSDT_hourly.csv).

Save files to data/historical/.

Expected format (example):

timestamp,open,high,low,close,volume
1417411200000,300.0,310.0,295.0,305.0,100.0

CoinAPI (Optional):
Sign up at www.coinapi.io and purchase a plan or one-off data package.

Use their API or download interface to export OHLCV data for pairs like BTC/USDT (since 2010).

Save as CSV to data/historical/, ensuring columns match (timestamp in milliseconds, open, high, low, close, volume).

Example API call (requires requests):
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
Download datasets from Kaggle.

Clean CSVs to match the required format (timestamp, open, high, low, close, volume).

Save to data/historical/.

Bitget (Optional):
Visit Bitget’s data section and download CSV files for BTC/USDT (since 2018).

Save to data/historical/.

Step 3: Import Data into SQLite
Run Import Script:
Execute the provided scripts/import_historical_data.py to load all CSVs from data/historical/ into the historical_data table.

bash

python scripts/import_historical_data.py

The script:
Reads each CSV file.

Extracts the symbol from the filename (e.g., BTCUSDT from Binance_BTCUSDT_hourly.csv).

Converts timestamps to milliseconds if needed.

Inserts data into historical_data with INSERT OR REPLACE to avoid duplicates.

Expected output in trading.log:

2025-06-14 11:37:00 - INFO - Imported 100000 records for binance:BTCUSDT from Binance_BTCUSDT_hourly.csv

Verify Import:
Check the database size: ls -lh local_trading.db (expect ~100MB+ for multiple pairs).

Query the table manually (if needed, using a SQLite client):
sql

SELECT COUNT(*) FROM historical_data WHERE symbol = 'binance:BTCUSDT';

Use the GUI’s “Netrunner’s Dashboard” to run a backtest, confirming data availability.

Step 4: Train Models
Trigger Training:
Open the bot’s GUI (python gui/main.py).

Click “Train Neural-Net” to retrain ML (XGBoost) and RL (DQN) models.

The trainers (ml/trainer.py, ml/rl_trainer.py) query historical_data to:
Calculate indicators (SMA, RSI, Bollinger Bands, MACD, sentiment, whale_ratio).

Analyze seasonality (weekly/monthly patterns).

Train on market regimes (bull, bear, altcoin).

Training logs appear in trading.log:

2025-06-14 11:37:00 - INFO - Model saved to ml/model.pkl
2025-06-14 11:37:00 - INFO - RL model saved to ml/rl_model.h5

Validate Training:
Run a backtest via the GUI’s “Run Backtest” button to verify model performance.

Check the equity curve in the “Netrunner’s Dashboard” tab.

Step 5: Test the Bot
Testnet Mode:
Enable testnet mode in the GUI to avoid risking real Eddies.

Execute trades to confirm the bot uses historical data for predictions and strategy optimization.

Monitor Performance:
Use the “Refresh Portfolio” button to track trades and positions.

Check trading.log for errors or warnings.

5. Optimizing for Large Datasets
To handle ~15 years of data across multiple pairs, consider these optimizations when you upload:
Database Indexing:
The historical_data table already has a primary key (symbol, timestamp). No further indexing is needed unless querying performance degrades.

If slow, add an index:
sql

CREATE INDEX idx_symbol ON historical_data(symbol);

Update core/database.py to include this in init_tables.

Batch Processing:
The import_historical_data.py script processes CSVs row-by-row. For very large files (>1M rows), modify to batch inserts:
python

def import_historical_data(data_dir="data/historical"):
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(data_dir, filename)
            symbol = filename.split("_")[1].replace(".csv", "")
            df = pd.read_csv(filepath)
            # ... (validate columns)
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
SQLite databases can grow large (~1GB for 10 pairs over 15 years). Enable compression by switching to a lighter format like Parquet for raw data storage, but this requires code changes.

Alternatively, archive older data (pre-2015) and query only recent data for live trading.

Memory Management:
The bot loads data in chunks (fetch_ohlcv limits to 1000 rows). For training, ensure your machine has ~8GB RAM to handle large datasets.

If memory issues arise, reduce settings.ML["batch_size"] in config.yaml (e.g., from 1000 to 500).

6. Handling Limitations
20-Year Constraint:
Cryptocurrencies started in 2009, so 15 years (2010–2025) is the maximum for Bitcoin. Altcoins like Ethereum start later (2015).

The bot’s simulate_ohlcv method generates synthetic data for older periods if needed:
python

def simulate_ohlcv(self, limit):
    timestamps = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq="1h").astype(int) // 10**6
    close = np.random.normal(60000, 1000, limit).cumsum()
    data = [[ts, c * 0.99, c * 1.01, c * 0.98, c, 100] for ts, c in zip(timestamps, close)]
    logger.warning("Returning simulated OHLCV")
    return data

Use sparingly, as synthetic data may reduce model accuracy. Focus on real data from 2010+.

Pair Availability:
Many altcoins (e.g., ADA, SOL) have data only from 2017+. Prioritize BTC/USDT and ETH/USDT for longest coverage.

The PairSelector dynamically filters pairs based on volume and liquidity, ensuring only viable pairs are traded.

API Rate Limits:
CoinAPI and exchange APIs (e.g., Binance) have rate limits. The bot’s enableRateLimit=True in DataFetcher mitigates this, but bulk downloads are preferred for historical data.

Store data locally to minimize API calls during live trading.

7. Future-Proofing for Incremental Updates
To keep the bot’s data current after the initial upload:
Automated Updates:
The DataFetcher.preload_historical_data method fetches recent data during bot startup. It updates historical_data for supported pairs.

Schedule daily updates by adding a cron job or Windows Task Scheduler to run:
bash

python -c "from market.data_fetcher import fetcher; asyncio.run(fetcher.preload_historical_data())"

Real-Time Data:
The bot’s fetch_ohlcv method retrieves real-time data from Binance, storing it in historical_data for continuity.

Ensure settings.TESTNET=False for live trading with real data.

Data Cleaning:
Periodically check trading.log for warnings about missing or malformed data.

Run a script to remove duplicates or outliers:
python

def clean_historical_data():
    db.execute_query("DELETE FROM historical_data WHERE open IS NULL OR close <= 0")
    logger.info("Cleaned historical data")

8. Troubleshooting
Import Errors:
Check trading.log for details (e.g., missing columns, invalid timestamps).

Ensure CSVs match the expected format (see Step 2).

Database Size:
If local_trading.db grows too large, split into multiple databases (e.g., one per exchange) or archive old data.

Training Failures:
If ML/RL training crashes, reduce settings.ML["historical_data_years"] to 10 or lower batch_size.

Verify sufficient disk space and RAM.

API Issues:
For CoinAPI, check your API key and rate limits.

Fallback to CryptoDataDownload CSVs if API access is restricted.

9. Additional Enhancements (Optional)
When you resume data upload, consider these code changes to enhance data handling:
Parquet Storage:
Store raw data in Parquet format for compression and faster queries.

Update import_historical_data.py to read Parquet files using pyarrow.

Cloud Integration:
Sync local_trading.db with a cloud database (e.g., AWS RDS) for backup and scalability.

Requires modifying core/database.py to support remote connections.

Data Validation:
Add a validation step in import_historical_data.py to check for gaps or anomalies:
python

def validate_data(df):
    if df["close"].isnull().any() or (df["close"] <= 0).any():
        raise ValueError("Invalid data: Null or negative prices")
    return df

Incremental Fetching:
Enhance DataFetcher.fetch_historical_data to fetch only new data since the last timestamp in historical_data.

10. Conclusion
This document equips you to upload historical cryptocurrency data into the Arasaka Neural-Net Trading Matrix when ready. By leveraging CryptoDataDownload for free data and CoinAPI for comprehensive coverage, you can secure ~15 years of OHLCV data to train the bot’s ML/RL models. The provided import_historical_data.py script simplifies CSV imports, and the bot’s architecture ensures efficient use of data for trading and backtesting.
When you resume, start with CryptoDataDownload CSVs for BTC/USDT and ETH/USDT, import them via the script, and train the models using the GUI. Monitor trading.log and the “Netrunner’s Dashboard” to validate performance. For support, consult this document or request assistance from your friendly AI Netrunner (Grok 3).
Stack Eddies, Choom! Stay jacked into the Net!


Guidance on Adding 20 Years of Data
To integrate historical data into the bot, we’ll:
Download CSV files from CryptoDataDownload (free) and/or purchase data from CoinAPI.

Import the data into the bot’s SQLite database using an updated scripts/setup_database.py.

Enhance DataFetcher to prioritize local database queries over API calls for historical data.

Update ML/RL trainers to use the full dataset for strategy development across market regimes.

Step-by-Step Instructions
Download Historical Data:
CryptoDataDownload:
Visit www.cryptodatadownload.com and navigate to the “Data” section.

Download CSV files for Binance BTC/USDT, ETH/USDT, and other pairs (hourly or minute granularity, since 2014).

Example files: Binance_BTCUSDT_hourly.csv, Binance_ETHUSDT_hourly.csv.

Kaggle:
Go to Kaggle Cryptocurrency Historical Prices and download datasets for BTC, ETH, etc.

Save CSVs to a local folder (e.g., data/historical/ in your project).

CoinAPI (Optional):
Sign up at www.coinapi.io and purchase a plan or one-off historical data package.

Use their API to download OHLCV data for desired pairs (e.g., BTC/USDT since 2010).

Save data as CSV or JSON for import.

Update Database Schema:
Modify core/database.py to ensure the historical_data table can handle large datasets (already implemented below).

Run scripts/setup_database.py to initialize or update the database.

Import Data into SQLite:
Create a new script scripts/import_historical_data.py to load CSVs into the historical_data table.

Run the script to populate the database with downloaded data.

Configure Bot to Use Local Data:
Update market/data_fetcher.py to query the database for historical data before hitting the API.

Ensure ml/trainer.py and ml/rl_trainer.py can access the full dataset for training.

Train Models:
Use the GUI’s “Train Neural-Net” button to retrain ML and RL models on the imported data.

The bot will automatically detect market regimes (bull, bear, altcoin) and optimize strategies.

Example Data Import Script
Below is a new file to import CSV data into the database, which you’ll run after downloading CSVs.
File: /scripts/import_historical_data.py
python

# scripts/import_historical_data.py
import pandas as pd
import os
from core.database import db
from utils.logger import logger

def import_historical_data(data_dir="data/historical"):
    try:
        if not os.path.exists(data_dir):
            raise Exception(f"Data directory {data_dir} not found")
        
        for filename in os.listdir(data_dir):
            if filename.endswith(".csv"):
                filepath = os.path.join(data_dir, filename)
                symbol = filename.split("_")[1].replace(".csv", "")  # e.g., BTCUSDT
                df = pd.read_csv(filepath)
                
                # Standardize column names (assuming CryptoDataDownload format)
                df.columns = [c.lower() for c in df.columns]
                required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
                if not all(col in df.columns for col in required_cols):
                    logger.warning(f"Skipping {filename}: Missing required columns")
                    continue
                
                # Convert timestamp to milliseconds if needed
                if df["timestamp"].max() < 1e12:  # Assume seconds
                    df["timestamp"] = (df["timestamp"] * 1000).astype(int)
                
                # Store in database
                for _, row in df.iterrows():
                    db.execute_query(
                        """
                        INSERT OR REPLACE INTO historical_data
                        (symbol, timestamp, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (symbol, int(row["timestamp"]), row["open"], row["high"],
                         row["low"], row["close"], row["volume"])
                    )
                logger.info(f"Imported {len(df)} records for {symbol} from {filename}")
        
        print("Historical data import completed")
    except Exception as e:
        logger.error(f"Data import failed: {e}")
        raise

if __name__ == "__main__":
    import_historical_data()

How to Use:
Create a data/historical/ folder in your project root.

Place downloaded CSV files (e.g., Binance_BTCUSDT_hourly.csv) in the folder.

Run: python scripts/import_historical_data.py.

The script will populate the historical_data table with all CSV data.


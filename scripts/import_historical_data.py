# scripts/import_historical_data.py
"""
Arasaka Historical Data Importer - Jack 20 years of crypto data into the Matrix
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db
from utils.logger import logger

class HistoricalDataImporter:
    def __init__(self, data_dir="data/historical"):
        self.data_dir = data_dir
        self.supported_formats = ['.csv', '.txt']
        
    def validate_csv_format(self, df):
        """Validate that CSV has required columns"""
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        
        # Check if all required columns exist (case-insensitive)
        df_columns_lower = [col.lower() for col in df.columns]
        for col in required_columns:
            if col not in df_columns_lower:
                raise ValueError(f"Missing required column: {col}")
        
        # Standardize column names
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in required_columns:
                column_mapping[col] = col_lower
        
        df = df.rename(columns=column_mapping)
        return df[required_columns]
    
    def convert_timestamp(self, df):
        """Convert various timestamp formats to milliseconds"""
        timestamp_col = df['timestamp'].iloc[0]
        
        # Check if it's already in milliseconds
        if isinstance(timestamp_col, (int, float)) and timestamp_col > 1e12:
            return df
        
        # Try different timestamp formats
        try:
            # Unix timestamp in seconds
            if isinstance(timestamp_col, (int, float)) and timestamp_col < 1e10:
                df['timestamp'] = df['timestamp'] * 1000
            # String date format
            elif isinstance(timestamp_col, str):
                df['timestamp'] = pd.to_datetime(df['timestamp']).astype(np.int64) // 10**6
            # Already datetime
            elif pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = df['timestamp'].astype(np.int64) // 10**6
        except Exception as e:
            logger.error(f"Timestamp conversion flatlined: {e}")
            raise
        
        return df
    
    def extract_symbol_from_filename(self, filename):
        """Extract trading pair symbol from filename"""
        # Common patterns: Binance_BTCUSDT_hourly.csv, BTCUSDT_1h.csv, etc.
        filename_upper = filename.upper()
        
        # Look for common crypto pairs
        pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT']
        for pair in pairs:
            if pair in filename_upper:
                return f"binance:{pair}"
        
        # Try to extract from pattern Exchange_PAIR_timeframe.csv
        parts = filename.split('_')
        if len(parts) >= 2:
            potential_pair = parts[1].replace('.csv', '').replace('.txt', '')
            if 'USDT' in potential_pair.upper():
                return f"binance:{potential_pair.upper()}"
        
        # Default fallback
        return f"binance:{filename.split('.')[0].upper()}"
    
    def import_file(self, filepath):
        """Import a single CSV file into the database"""
        try:
            filename = os.path.basename(filepath)
            logger.info(f"Importing {filename} into the Neural-Net...")
            
            # Read CSV with various encodings
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
            except:
                df = pd.read_csv(filepath, encoding='latin-1')
            
            # Validate and clean data
            df = self.validate_csv_format(df)
            df = self.convert_timestamp(df)
            
            # Remove invalid rows
            df = df.dropna()
            df = df[df['close'] > 0]  # Remove zero prices
            df = df[df['volume'] >= 0]  # Remove negative volumes
            
            # Extract symbol
            symbol = self.extract_symbol_from_filename(filename)
            
            # Prepare data for insertion
            rows = []
            for _, row in df.iterrows():
                rows.append((
                    symbol,
                    int(row['timestamp']),
                    float(row['open']),
                    float(row['high']),
                    float(row['low']),
                    float(row['close']),
                    float(row['volume'])
                ))
            
            # Batch insert with progress
            batch_size = 1000
            total_rows = len(rows)
            
            for i in range(0, total_rows, batch_size):
                batch = rows[i:i+batch_size]
                db.executemany(
                    """
                    INSERT OR REPLACE INTO historical_data
                    (symbol, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    batch
                )
                
                progress = min((i + batch_size) / total_rows * 100, 100)
                logger.info(f"Progress: {progress:.1f}% - {i + len(batch)}/{total_rows} rows")
            
            logger.info(f"✓ Imported {total_rows} records for {symbol} - Data jacked into the Matrix!")
            return total_rows
            
        except Exception as e:
            logger.error(f"Import failed for {filepath}: {e}")
            raise
    
    def import_all_data(self):
        """Import all CSV files from the data directory"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.warning(f"Created data directory: {self.data_dir}")
            logger.info("Download historical data CSVs and place them in this directory")
            return
        
        files = [f for f in os.listdir(self.data_dir) 
                if any(f.endswith(ext) for ext in self.supported_formats)]
        
        if not files:
            logger.warning(f"No CSV files found in {self.data_dir}")
            logger.info("Download data from CryptoDataDownload or other sources")
            return
        
        logger.info(f"Found {len(files)} files to import")
        total_imported = 0
        
        for file in files:
            filepath = os.path.join(self.data_dir, file)
            try:
                rows = self.import_file(filepath)
                total_imported += rows
            except Exception as e:
                logger.error(f"Skipping {file}: {e}")
                continue
        
        logger.info(f"✓ Total import complete: {total_imported} rows jacked into the Neural-Net!")
        
        # Verify import
        symbols = db.fetch_all("SELECT DISTINCT symbol FROM historical_data")
        for symbol in symbols:
            count = db.fetch_one(
                "SELECT COUNT(*) FROM historical_data WHERE symbol = ?", 
                (symbol[0],)
            )[0]
            logger.info(f"  {symbol[0]}: {count} records")

def main():
    """Main entry point for historical data import"""
    logger.info("=== Arasaka Historical Data Import System ===")
    logger.info("Preparing to jack crypto data into the Neural-Net Trading Matrix...")
    
    importer = HistoricalDataImporter()
    
    # Check if custom data directory is provided
    if len(sys.argv) > 1:
        importer.data_dir = sys.argv[1]
    
    importer.import_all_data()
    
    logger.info("=== Import Complete - Ready to stack Eddies! ===")

if __name__ == "__main__":
    main()

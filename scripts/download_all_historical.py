#!/usr/bin/env python3
"""Download historical data from all exchanges"""
import asyncio
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.exchange_manager import exchange_manager
from market.multi_exchange_fetcher import multi_fetcher
from utils.logger import logger

async def download_exchange_history(exchange_name, pairs, days=365):
    """Download historical data for one exchange"""
    try:
        logger.info(f"Downloading {days} days of data for {exchange_name}")
        
        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        for pair in pairs:
            try:
                data = await multi_fetcher.fetch_ohlcv(
                    pair, "1h", limit=1000, since=since, exchange=exchange_name
                )
                logger.info(f"Downloaded {len(data)} candles for {pair}")
                
                # Save to file
                filename = f"data/historical/{exchange_name}/{pair.replace('/', '_')}_hourly.csv"
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                
                with open(filename, 'w') as f:
                    f.write("timestamp,open,high,low,close,volume\n")
                    for candle in data:
                        f.write(f"{candle[0]},{candle[1]},{candle[2]},{candle[3]},{candle[4]},{candle[5]}\n")
                        
            except Exception as e:
                logger.error(f"Failed to download {pair}: {e}")
                
    except Exception as e:
        logger.error(f"Download failed for {exchange_name}: {e}")

async def main():
    # Initialize
    await multi_fetcher.initialize()
    
    # Download data for each exchange
    exchange_pairs = {
        "coinbase": ["BTC/USD", "ETH/USD", "SOL/USD"],
        "kraken": ["BTC/USD", "ETH/USD", "SOL/USD"],
        "bitstamp": ["BTC/USD", "ETH/USD", "LTC/USD"],
        "bybit": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        "bitvavo": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
    }
    
    tasks = []
    for exchange, pairs in exchange_pairs.items():
        if exchange in multi_fetcher.exchanges:
            tasks.append(download_exchange_history(exchange, pairs))
    
    await asyncio.gather(*tasks)
    
    # Close connections
    await multi_fetcher.close_all()

if __name__ == "__main__":
    asyncio.run(main())

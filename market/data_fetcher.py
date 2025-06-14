# market/data_fetcher.py
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from config.settings import settings
from utils.logger import logger

class DataFetcher:
    def __init__(self):
        self.exchange = ccxt.binance({
            "apiKey": settings.BINANCE_API_KEY,
            "secret": settings.BINANCE_API_SECRET,
            "enableRateLimit": True
        })
        if settings.TESTNET:
            self.exchange.set_sandbox_mode(True)

    async def fetch_ohlcv(self, symbol, timeframe, limit=100):
        try:
            await self.exchange.load_markets()
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            logger.info(f"Fetched {limit} OHLCV records for {symbol}")
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return self.simulate_ohlcv(limit)

    def simulate_ohlcv(self, limit):
        timestamps = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq="1h").astype(int) // 10**6
        close = np.random.normal(60000, 1000, limit).cumsum()
        data = [
            [ts, c * 0.99, c * 1.01, c * 0.98, c, 100]
            for ts, c in zip(timestamps, close)
        ]
        logger.warning("Returning simulated OHLCV data")
        return data

    async def close(self):
        await self.exchange.close()

fetcher = DataFetcher()

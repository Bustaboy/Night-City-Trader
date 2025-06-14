# market/data_fetcher.py
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from config.settings import settings
from core.database import db
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
        self.preload_historical_data()

    async def preload_historical_data(self):
        try:
            await self.exchange.load_markets()
            pairs = list(self.exchange.markets.keys())
            for symbol in pairs[:10]:  # Limit to 10 for demo; remove for full preload
                data = await self.fetch_historical_data(symbol, settings.TRADING["timeframe"], settings.ML["historical_data_years"])
                db.store_historical_data(symbol, data)
                logger.info(f"Preloaded historical data for {symbol}")
        except Exception as e:
            logger.error(f"Preloading historical data failed: {e}")

    async def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None):
        try:
            await self.exchange.load_markets()
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            db.store_historical_data(symbol, ohlcv)
            logger.info(f"Fetched {len(ohlcv)} OHLCV records for {symbol}")
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return self.simulate_ohlcv(limit)

    async def fetch_historical_data(self, symbol, timeframe, years=20):
        try:
            await self.exchange.load_markets()
            since = int(pd.Timestamp.now() - pd.Timedelta(days=365*years)).timestamp() * 1000
            all_data = []
            while since < int(pd.Timestamp.now().timestamp() * 1000):
                data = await self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not data:
                    break
                all_data.extend(data)
                since = data[-1][0] + 1
            logger.info(f"Fetched {len(all_data)} historical OHLCV records for {symbol}")
            return all_data
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return self.simulate_ohlcv(1000)

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

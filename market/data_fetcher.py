# market/data_fetcher.py
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from config.settings import settings
from core.database import db
from utils.logger import logger

class DataFetcher:
    def __init__(self):
        self.exchanges = {}
        for ex in settings.TRADING["exchanges"]:
            exchange_class = getattr(ccxt, ex)
            self.exchanges[ex] = exchange_class({
                "apiKey": settings.BINANCE_API_KEY if ex == "binance" else "",
                "secret": settings.BINANCE_API_SECRET if ex == "binance" else "",
                "enableRateLimit": True
            })
            if settings.TESTNET:
                self.exchanges[ex].set_sandbox_mode(True)
        self.preload_historical_data()

    async def preload_historical_data(self):
        try:
            for ex_name, exchange in self.exchanges.items():
                await exchange.load_markets()
                pairs = [p for p in exchange.markets.keys() if p.endswith("/USDT")]
                for symbol in pairs[:10]:  # Limit for demo
                    data = await self.fetch_historical_data(ex_name, symbol, settings.TRADING["timeframe"], settings.ML["historical_data_years"])
                    db.store_historical_data(f"{ex_name}:{symbol}", data)
                    logger.info(f"Preloaded data for {ex_name}:{symbol}")
        except Exception as e:
            logger.error(f"Preloading failed: {e}")

    async def fetch_ohlcv(self, symbol, timeframe, limit=100, since=None, exchange="binance"):
        try:
            ex = self.exchanges[exchange]
            await ex.load_markets()
            ohlcv = await ex.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            db.store_historical_data(f"{exchange}:{symbol}", ohlcv)
            logger.info(f"Fetched {len(ohlcv)} OHLCV for {exchange}:{symbol}")
            return ohlcv
        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            # Try database
            data = db.fetch_all(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?
                """,
                (f"{exchange}:{symbol}", limit)
            )
            if data:
                return [[d[0], d[1], d[2], d[3], d[4], d[5]] for d in data]
            return self.simulate_ohlcv(limit)

    async def fetch_historical_data(self, exchange, symbol, timeframe, years=20):
        try:
            ex = self.exchanges[exchange]
            await ex.load_markets()
            since = int(pd.Timestamp.now() - pd.Timedelta(days=365*years)).timestamp() * 1000
            all_data = []
            while since < int(pd.Timestamp.now().timestamp() * 1000):
                data = await ex.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not data:
                    break
                all_data.extend(data)
                since = data[-1][0] + 1
            logger.info(f"Fetched {len(all_data)} records for {exchange}:{symbol}")
            return all_data
        except Exception as e:
            logger.error(f"Historical fetch failed: {e}")
            return self.simulate_ohlcv(1000)

    async def fetch_order_book(self, symbol, exchange="binance"):
        try:
            ex = self.exchanges[exchange]
            await ex.load_markets()
            book = await ex.fetch_order_book(symbol, limit=10)
            logger.info(f"Fetched order book for {exchange}:{symbol}")
            return book
        except Exception as e:
            logger.error(f"Order book fetch failed: {e}")
            return {"bids": [], "asks": []}

    def simulate_ohlcv(self, limit):
        timestamps = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq="1h").astype(int) // 10**6
        close = np.random.normal(60000, 1000, limit).cumsum()
        data = [[ts, c * 0.99, c * 1.01, c * 0.98, c, 100] for ts, c in zip(timestamps, close)]
        logger.warning("Returning simulated OHLCV")
        return data

    def set_sandbox_mode(self, enabled):
        for ex in self.exchanges.values():
            ex.set_sandbox_mode(enabled)

    async def close(self):
        for ex in self.exchanges.values():
            await ex.close()

fetcher = DataFetcher()

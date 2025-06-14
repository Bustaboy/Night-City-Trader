# market/pair_selector.py
import ccxt.async_support as ccxt
import pandas as pd
from config.settings import settings
from ml.trainer import trainer
from utils.logger import logger

class PairSelector:
    def __init__(self):
        self.exchange = ccxt.binance({
            "apiKey": settings.BINANCE_API_KEY,
            "secret": settings.BINANCE_API_SECRET,
            "enableRateLimit": True
        })
        if settings.TESTNET:
            self.exchange.set_sandbox_mode(True)
        self.pairs = settings.TRADING.get("pairs", ["BTC/USDT", "ETH/USDT", "BNB/USDT"])

    async def select_best_pair(self, timeframe, limit=100):
        try:
            await self.exchange.load_markets()
            best_pair = None
            highest_score = -1
            for pair in self.pairs:
                data = await self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
                if data:
                    prediction = trainer.predict(data[-1])
                    score = 1 if prediction == 1 else 0  # Simple scoring; could be enhanced
                    logger.info(f"Evaluated pair {pair}: Prediction={prediction}, Score={score}")
                    if score > highest_score:
                        highest_score = score
                        best_pair = pair
            if best_pair:
                logger.info(f"Selected best pair: {best_pair} with score {highest_score}")
                return best_pair
            logger.warning("No suitable pair found")
            return settings.TRADING["symbol"]  # Fallback to default
        except Exception as e:
            logger.error(f"Pair selection failed: {e}")
            return settings.TRADING["symbol"]

    async def close(self):
        await self.exchange.close()

pair_selector = PairSelector()

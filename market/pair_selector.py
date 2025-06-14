# market/pair_selector.py
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from config.settings import settings
from ml.trainer import trainer
from ml.rl_trainer import rl_trainer
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

    async def select_best_pair(self, timeframe, limit=100):
        try:
            await self.exchange.load_markets()
            pairs = [p for p in self.exchange.markets.keys() if p.endswith("/USDT")]
            scores = []
            for pair in pairs:
                try:
                    data = await self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
                    ticker = await self.exchange.fetch_ticker(pair)
                    volume = ticker["quoteVolume"]
                    spread = (ticker["ask"] - ticker["bid"]) / ticker["bid"]
                    volatility = np.std([d[4] for d in data]) / np.mean([d[4] for d in data])
                    if (volume < settings.TRADING["pair_selection"]["min_volume"] or
                        volatility < settings.TRADING["pair_selection"]["min_volatility"] or
                        spread > settings.TRADING["pair_selection"]["max_spread"]):
                        continue
                    prediction = trainer.predict(data[-1])
                    rl_score = rl_trainer.predict(data[-1])
                    score = (prediction + rl_score) * volume * volatility / (spread + 1e-6)
                    scores.append((pair, score))
                    logger.info(f"Evaluated pair {pair}: Score={score}")
                except:
                    continue
            if scores:
                best_pair = max(scores, key=lambda x: x[1])[0]
                logger.info(f"Selected best pair: {best_pair}")
                return best_pair
            logger.warning("No suitable pair found")
            return settings.TRADING["symbol"]
        except Exception as e:
            logger.error(f"Pair selection failed: {e}")
            return settings.TRADING["symbol"]

    async def detect_arbitrage(self):
        try:
            await self.exchange.load_markets()
            opportunities = []
            pairs = [p for p in self.exchange.markets.keys() if p.endswith("/USDT")]
            for i, pair1 in enumerate(pairs):
                for pair2 in pairs[i+1:]:
                    for pair3 in pairs:
                        if pair1.split("/")[0] == pair3.split("/")[0] and pair2.split("/")[0] == pair3.split("/")[1]:
                            ticker1 = await self.exchange.fetch_ticker(pair1)
                            ticker2 = await self.exchange.fetch_ticker(pair2)
                            ticker3 = await self.exchange.fetch_ticker(pair3)
                            profit = (1 / ticker1["ask"]) * ticker2["bid"] * ticker3["bid"] - 1
                            if profit > 0.01:  # 1% profit after fees
                                opportunities.append({
                                    "path": [pair1, pair2, pair3],
                                    "profit": profit
                                })
            return opportunities
        except Exception as e:
            logger.error(f"Arbitrage detection failed: {e}")
            return []

    async def close(self):
        await self.exchange.close()

pair_selector = PairSelector()

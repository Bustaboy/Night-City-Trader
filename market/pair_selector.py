# market/pair_selector.py
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from config.settings import settings
from ml.trainer import trainer
from ml.rl_trainer import rl_trainer
from utils.logger import logger
from core.database import db

class PairSelector:
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

    async def select_best_pair(self, timeframe, limit=100):
        try:
            best_pair = None
            best_score = -1
            for ex_name, ex in self.exchanges.items():
                await ex.load_markets()
                pairs = [p for p in ex.markets.keys() if p.endswith("/USDT")]
                for pair in pairs:
                    try:
                        data = await fetcher.fetch_ohlcv(pair, timeframe, limit=limit, exchange=ex_name)
                        ticker = await ex.fetch_ticker(pair)
                        book = await fetcher.fetch_order_book(pair, exchange=ex_name)
                        volume = ticker["quoteVolume"]
                        prev_volume = await ex.fetch_ticker(pair, params={"timeframe": timeframe, "limit": 2})["quoteVolume"]
                        volume_spike = (volume / prev_volume - 1) if prev_volume > 0 else 0
                        spread = (ticker["ask"] - ticker["bid"]) / ticker["bid"]
                        volatility = np.std([d[4] for d in data]) / np.mean([d[4] for d in data])
                        liquidity = sum(b[1] for b in book["bids"][:5]) + sum(a[1] for a in book["asks"][:5])
                        if (volume < settings.TRADING["pair_selection"]["min_volume"] or
                            volatility < settings.TRADING["pair_selection"]["min_volatility"] or
                            spread > settings.TRADING["pair_selection"]["max_spread"] or
                            liquidity < settings.TRADING["pair_selection"]["min_liquidity"]):
                            continue
                        prediction = trainer.predict(data[-1])
                        rl_score = rl_trainer.predict(data[-1])
                        score = (prediction + rl_score) * volume * volatility * liquidity * (1 + volume_spike) / (spread + 1e-6)
                        logger.info(f"Evaluated {ex_name}:{pair}: Score={score}, VolumeSpike={volume_spike}")
                        if score > best_score:
                            best_score = score
                            best_pair = f"{ex_name}:{pair}"
                    except:
                        continue
            if best_pair:
                logger.info(f"Selected best pair: {best_pair}")
                return best_pair
            logger.warning("No suitable pair found")
            return f"binance:{settings.TRADING['symbol']}"
        except Exception as e:
            logger.error(f"Pair selection flatlined: {e}")
            return f"binance:{settings.TRADING['symbol']}"

    async def auto_rotate_pairs(self):
        try:
            await self.exchange.load_markets()
            pairs = [p for p in self.exchange.markets.keys() if p.endswith("/USDT")]
            profitable_pairs = {}
            trades = db.fetch_all("SELECT symbol, SUM((price * amount) - fee) as profit FROM trades GROUP BY symbol")
            for trade in trades:
                profit = trade[1] or 0
                if profit > 0.01 * db.get_portfolio_value():  # >1% profit
                    profitable_pairs[trade[0]] = profit
                elif profit < -0.01 * db.get_portfolio_value():  # <-1% loss
                    if trade[0] in profitable_pairs:
                        del profitable_pairs[trade[0]]
            for pair in pairs:
                if pair not in profitable_pairs:
                    data = await fetcher.fetch_ohlcv(pair, "1h", limit=100)
                    profit = sum((d[4] - d[1]) * 0.001 for d in data) / 100  # Rough profit estimate
                    if profit > 0.01 * db.get_portfolio_value():
                        profitable_pairs[pair] = profit
            top_pairs = list(profitable_pairs.keys())[:10]  # Top 10 profitable pairs
            logger.info(f"Auto-rotated pairs: {top_pairs}")
            return top_pairs
        except Exception as e:
            logger.error(f"Pair rotation flatlined: {e}")
            return [settings.TRADING["symbol"]]

    async def detect_arbitrage(self):
        try:
            opportunities = []
            for pair in [p for p in self.exchanges["binance"].markets.keys() if p.endswith("/USDT")]:
                try:
                    prices = {}
                    for ex_name, ex in self.exchanges.items():
                        await ex.load_markets()
                        if pair in ex.markets:
                            ticker = await ex.fetch_ticker(pair)
                            prices[ex_name] = {"bid": ticker["bid"], "ask": ticker["ask"]}
                    for ex1 in prices:
                        for ex2 in prices:
                            if ex1 != ex2:
                                profit = (prices[ex2]["bid"] / prices[ex1]["ask"] - 1) - 2 * settings.TRADING["fees"]["taker"]
                                if profit > 0.01:
                                    opportunities.append({
                                        "pair": pair,
                                        "buy_exchange": ex1,
                                        "sell_exchange": ex2,
                                        "profit": profit
                                    })
                    binance = self.exchanges["binance"]
                    await binance.load_markets()
                    pairs = [p for p in binance.markets.keys() if p.endswith("/USDT")]
                    for i, pair1 in enumerate(pairs):
                        for pair2 in pairs[i+1:]:
                            for pair3 in pairs:
                                if pair1.split("/")[0] == pair3.split("/")[0] and pair2.split("/")[0] == pair3.split("/")[1]:
                                    ticker1 = await binance.fetch_ticker(pair1)
                                    ticker2 = await binance.fetch_ticker(pair2)
                                    ticker3 = await binance.fetch_ticker(pair3)
                                    profit = (1 / ticker1["ask"]) * ticker2["bid"] * ticker3["bid"] - 1
                                    if profit > 0.01:
                                        opportunities.append({
                                            "path": [pair1, pair2, pair3],
                                            "profit": profit,
                                            "exchange": "binance"
                                        })
                except:
                    continue
            logger.info(f"Arbitrage scan: {len(opportunities)} opportunities")
            return opportunities
        except Exception as e:
            logger.error(f"Arbitrage detection flatlined: {e}")
            return []

    def set_sandbox_mode(self, enabled):
        for ex in self.exchanges.values():
            ex.set_sandbox_mode(enabled)

    async def close(self):
        for ex in self.exchanges.values():
            await ex.close()

pair_selector = PairSelector()

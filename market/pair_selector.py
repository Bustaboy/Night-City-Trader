# market/pair_selector.py
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
from config.settings import settings
from ml.trainer import trainer
from ml.rl_trainer import rl_trainer
from utils.logger import logger
from core.database import db
from market.data_fetcher import DataFetcher as fetcher

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
                pairs = [f"{ex_name}:{p}" for p in ex.markets.keys() if p.endswith("/USDT")]
                for pair in pairs:
                    try:
                        data = await fetcher.fetch_ohlcv(pair.split(":")[1], timeframe, limit=limit, exchange=ex_name)
                        ticker = await ex.fetch_ticker(pair.split(":")[1])
                        book = await fetcher.fetch_order_book(pair.split(":")[1], exchange=ex_name)
                        volume = ticker["quoteVolume"]
                        prev_volume = await ex.fetch_ticker(pair.split(":")[1], params={"timeframe": timeframe, "limit": 2})["quoteVolume"]
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
                        logger.info(f"Evaluated {pair}: Score={score}, VolumeSpike={volume_spike}")
                        if score > best_score:
                            best_score = score
                            best_pair = pair
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
            profitable_pairs = {}
            for ex_name, ex in self.exchanges.items():
                await ex.load_markets()
                pairs = [f"{ex_name}:{p}" for p in ex.markets.keys() if p.endswith("/USDT")]
                trades = db.fetch_all("SELECT symbol, SUM((price * amount) - fee) as profit FROM trades WHERE symbol LIKE ? GROUP BY symbol", (f"{ex_name}:%",))
                if not trades:  # Handle empty table
                    continue
                for trade in trades:
                    profit = trade[1] or 0
                    symbol = trade[0]
                    if profit > 0.01 * db.get_portfolio_value():  # >1% profit
                        profitable_pairs[symbol] = profit
                    elif profit < -0.01 * db.get_portfolio_value():  # <-1% loss
                        if symbol in profitable_pairs:
                            del profitable_pairs[symbol]
                for pair in pairs:
                    if pair not in profitable_pairs:
                        data = await fetcher.fetch_ohlcv(pair.split(":")[1], "1h", limit=100, exchange=ex_name)
                        rl_pred = rl_trainer.predict(data[-1]) if data else 0
                        profit_est = rl_pred * np.mean([d[4] for d in data]) if data else 0
                        if profit_est > 0.01 * db.get_portfolio_value():
                            profitable_pairs[pair] = profit_est
            top_pairs = list(profitable_pairs.keys())[:10]  # Top 10
            return top_pairs if top_pairs else [f"binance:{settings.TRADING['symbol']}"]
        except Exception as e:
            logger.error(f"Pair rotation flatlined: {e}")
            return [f"binance:{settings.TRADING['symbol']}"]

    async def detect_arbitrage(self):
        try:
            opportunities = []
            for ex_name, ex in self.exchanges.items():
                await ex.load_markets()
                pairs = [p for p in ex.markets.keys() if p.endswith("/USDT")]
                for pair in pairs:
                    try:
                        prices = {}
                        for other_ex_name, other_ex in self.exchanges.items():
                            if pair in other_ex.markets:
                                ticker = await other_ex.fetch_ticker(pair)
                                prices[other_ex_name] = {"bid": ticker["bid"], "ask": ticker["ask"]}
                        for buy_ex in prices:
                            for sell_ex in prices:
                                if buy_ex != sell_ex:
                                    profit = (prices[sell_ex]["bid"] / prices[buy_ex]["ask"] - 1) - 2 * settings.TRADING["fees"]["taker"]
                                    if profit > 0.01:
                                        opportunities.append({
                                            "pair": pair,
                                            "buy_exchange": buy_ex,
                                            "sell_exchange": sell_ex,
                                            "profit": profit
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

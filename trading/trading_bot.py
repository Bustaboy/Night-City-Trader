# trading/trading_bot.py
import ccxt.async_support as ccxt
from config.settings import settings
from core.database import db
from ml.trainer import MLTrainer
from ml.rl_trainer import rl_trainer
from market.data_fetcher import fetcher
import asyncio
import uuid
from datetime import datetime
from utils.logger import logger
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np

class TradingBot:
    def __init__(self):
        self.exchange = ccxt.binance({
            "apiKey": settings.BINANCE_API_KEY,
            "secret": settings.BINANCE_API_SECRET,
            "enableRateLimit": True
        })
        if settings.TESTNET:
            self.exchange.set_sandbox_mode(True)
        self.trainer = MLTrainer()
        self.rl_trainer = rl_trainer

    async def execute_trade(self, symbol, side, amount):
        try:
            await self.exchange.load_markets()
            data = await fetcher.fetch_ohlcv(symbol, settings.TRADING["timeframe"], limit=100)
            prediction = self.trainer.predict(data[-1])
            rl_action = self.rl_trainer.predict(data[-1])
            if (side == "buy" and prediction == 1 and rl_action >= 0.5) or (side == "sell" and prediction == 0 and rl_action <= 0.5):
                order = await self.exchange.create_market_order(symbol, side, amount)
                trade_id = str(uuid.uuid4())
                fee = order.get("fee", {}).get("cost", amount * order["price"] * settings.TRADING["fees"]["taker"])
                db.execute_query(
                    "INSERT INTO trades (id, symbol, side, amount, price, fee, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (trade_id, symbol, side, amount, order["price"], fee, datetime.now().isoformat())
                )
                position_id = str(uuid.uuid4())
                db.execute_query(
                    "INSERT INTO positions (id, symbol, side, amount, entry_price, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (position_id, symbol, side, amount, order["price"], datetime.now().isoformat())
                )
                logger.info(f"Trade executed in the Matrix: {trade_id}, {symbol}, {side}, SL={settings.TRADING['risk']['moderate']['stop_loss']}, TP={settings.TRADING['risk']['moderate']['take_profit']}")
                return {"id": trade_id, "order": order}
            else:
                logger.warning(f"Trade rejected by Neural-Net: {symbol}, {side}")
                raise Exception("Trade not executed: Neural-Net does not support this action")
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            raise

    async def detect_market_regime(self):
        try:
            data = await fetcher.fetch_ohlcv(settings.TRADING["symbol"], "1d", limit=252)
            df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            returns = df["close"].pct_change().dropna()
            volatility = returns.rolling(20).std()
            features = np.column_stack([returns[-100:], volatility[-100:]])
            kmeans = KMeans(n_clusters=3, random_state=42).fit(features)
            regime = kmeans.labels_[-1]
            regime_map = {0: "bull", 1: "bear", 2: "altcoin"}
            return regime_map.get(regime, "bull")
        except Exception as e:
            logger.error(f"Market regime detection failed: {e}")
            return "bull"

    async def backtest_strategy(self, symbol, timeframe, start_date, end_date, strategy):
        try:
            data = db.fetch_all(
                """
                SELECT * FROM historical_data
                WHERE symbol = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
                """,
                (symbol, int(pd.to_datetime(start_date).timestamp() * 1000), int(pd.to_datetime(end_date).timestamp() * 1000))
            )
            df = pd.DataFrame(data, columns=["symbol", "timestamp", "open", "high", "low", "close", "volume"])
            if strategy == "breakout":
                df["atr"] = df["high"].rolling(14).max() - df["low"].rolling(14).min()
                df["signal"] = (df["close"] > df["close"].shift(1) + 2 * df["atr"]).astype(int)
            else:  # mean_reversion
                df["rsi"] = 100 - (100 / (1 + df["close"].diff().where(lambda x: x > 0, 0).rolling(14).mean() / 
                                        df["close"].diff().where(lambda x: x < 0, 0).rolling(14).mean()))
                df["signal"] = ((df["rsi"] < 30).astype(int) - (df["rsi"] > 70).astype(int))
            returns = df["signal"].shift(1) * df["close"].pct_change()
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            return {"sharpe_ratio": sharpe, "total_return": returns.sum()}
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return {"sharpe_ratio": 0, "total_return": 0}

    async def close(self):
        await self.exchange.close()

bot = TradingBot()

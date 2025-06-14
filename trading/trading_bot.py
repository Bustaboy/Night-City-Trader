# trading/trading_bot.py
import ccxt.async_support as ccxt
from config.settings import settings
from core.database import db
from ml.trainer import MLTrainer
from market.data_fetcher import fetcher
import asyncio
import uuid
from datetime import datetime
from utils.logger import logger

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

    async def execute_trade(self, symbol, side, amount):
        try:
            await self.exchange.load_markets()
            data = await fetcher.fetch_ohlcv(symbol, settings.TRADING["timeframe"], limit=100)
            prediction = self.trainer.predict(data[-1])
            if (side == "buy" and prediction == 1) or (side == "sell" and prediction == 0):
                order = await self.exchange.create_market_order(symbol, side, amount)
                trade_id = str(uuid.uuid4())
                db.execute_query(
                    "INSERT INTO trades (id, symbol, side, amount, price, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (trade_id, symbol, side, amount, order["price"], datetime.now().isoformat())
                )
                # Update positions
                position_id = str(uuid.uuid4())
                db.execute_query(
                    "INSERT INTO positions (id, symbol, side, amount, entry_price, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (position_id, symbol, side, amount, order["price"], datetime.now().isoformat())
                )
                logger.info(f"Trade executed: {trade_id}, {symbol}, {side}")
                return {"id": trade_id, "order": order}
            else:
                logger.warning(f"Trade rejected by ML model: {symbol}, {side}")
                raise Exception("Trade not executed: ML model does not support this action")
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            raise

    async def close(self):
        await self.exchange.close()

bot = TradingBot()

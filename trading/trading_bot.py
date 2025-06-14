# trading/trading_bot.py
import ccxt.async_support as ccxt
from config.settings import settings
from core.database import db
from ml.trainer import MLTrainer
from ml.rl_trainer import RLTrainer
from market.data_fetcher import DataFetcher
from trading.strategies import TradingStrategies
from trading.risk_manager import RiskManager
import asyncio
import uuid
from datetime import datetime, timedelta
from utils.logger import logger
from sklearn.cluster import KMeans
import pandas as np

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
        self.rl_trainer = RLTrainer()
        self.strategies = TradingStrategies()
        self.risk_manager = RiskManager()
        self.fetcher = DataFetcher()

    async def execute_trade(self, symbol, side, amount, leverage=1.0):
        try:
            ex_name = symbol.split(":")[0] if ":" in symbol else "binance"
            pair = symbol.split(":")[1] if ":" in symbol else symbol
            if ex_name != "binance":
                raise Exception("Only Binance trades supported for now")
            await self.exchange.load_markets()

            # Fetch data for multi-timeframe analysis
            timeframes = ["1h", "4h", "1d"]
            signals = []
            for tf in timeframes:
                data = await self.fetcher.fetch_ohlcv(pair, tf, limit=100, exchange=ex_name)
                signal = self.strategies.get_signal(pair, data, timeframe=tf)
                signals.append(signal)
            combined_signal = np.mean(signals)
            ml_prediction = self.trainer.predict(data[-1])
            rl_action = self.rl_trainer.predict(data[-1])
            rl_confidence = np.max(self.rl_trainer.model.predict(np.array(data[-1][1:]).reshape(1, -1), verbose=0))

            # Adjust leverage and position size with portfolio value
            market_regime = await self.detect_market_regime()
            leverage = self.risk_manager.adjust_leverage(symbol, rl_confidence, market_regime)
            adjusted_amount = self.risk_manager.adjust_position_size(symbol, amount)

            # Check seasonality
            seasonality = db.fetch_one(
                "SELECT mean_return FROM seasonality_patterns WHERE symbol = ? AND period = ?",
                (symbol, f"weekday_{datetime.now().weekday()}")
            )
            seasonality_weight = seasonality[0] if seasonality else 0

            # Validate trade
            if (side == "buy" and combined_signal > 0.5 and ml_prediction == 1 and rl_action >= 0.5 and seasonality_weight >= 0) or \
               (side == "sell" and combined_signal < -0.5 and ml_prediction == 0 and rl_action <= 0.5 and seasonality_weight <= 0):
                # Smart order routing
                book = await self.fetcher.fetch_order_book(pair, exchange=ex_name)
                total_amount = adjusted_amount
                executed_amount = 0
                orders = []
                fee_rate = settings.TRADING["fees"]["maker"] if self.can_use_maker_order(book, side) else settings.TRADING["fees"]["taker"]
                
                while executed_amount < total_amount:
                    price = book["asks"][0][0] if side == "buy" else book["bids"][0][0]
                    available = book["asks"][0][1] if side == "buy" else book["bids"][0][1]
                    order_amount = min(total_amount - executed_amount, available)
                    if leverage > 1.0:
                        order = await self.exchange.create_market_order(pair, side, order_amount, params={"leverage": leverage})
                    else:
                        order = await self.exchange.create_market_order(pair, side, order_amount)
                    executed_amount += order_amount
                    orders.append(order)
                    book = await self.fetcher.fetch_order_book(pair, exchange=ex_name)
                
                trade_id = str(uuid.uuid4())
                avg_price = np.mean([o["price"] for o in orders])
                fee = sum(o["cost"] * fee_rate for o in orders)
                profit = (avg_price - float(self.amount_entry.get())) * float(self.amount_entry.get()) - fee if side == "buy" else (float(self.amount_entry.get()) - avg_price) * float(self.amount_entry.get()) - fee
                
                # Adaptive SL/TP based on ATR
                atr = self.calculate_atr(data)
                sl_price = avg_price * (1 - 1.5 * atr / avg_price) if side == "buy" else avg_price * (1 + 1.5 * atr / avg_price)
                tp_price = avg_price * (1 + 3.0 * atr / avg_price) if side == "buy" else avg_price * (1 - 3.0 * atr / avg_price)
                oco_params = {
                    "stopPrice": sl_price,
                    "stopLimitPrice": sl_price,
                    "stopLimitTimeInForce": "GTC",
                    "price": tp_price
                }
                await self.exchange.create_order(pair, "oco", side, amount, None, oco_params)

                # Store trade and update portfolio
                db.execute_query(
                    """
                    INSERT INTO trades (id, symbol, side, amount, price, fee, leverage, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (trade_id, symbol, side, amount, avg_price, fee, leverage, datetime.now().isoformat())
                )
                position_id = str(uuid.uuid4())
                db.execute_query(
                    """
                    INSERT INTO positions (id, symbol, side, amount, entry_price, stop_loss, take_profit, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (position_id, symbol, side, amount, avg_price, sl_price, tp_price, datetime.now().isoformat())
                )
                if profit > 0:
                    self.risk_manager.reserve_creds(trade_id, profit)
                new_portfolio_value = db.get_portfolio_value() + profit - fee
                db.update_portfolio_value(new_portfolio_value)

                # Auto-hedge
                hedge_symbol, hedge_amount = self.risk_manager.calculate_hedge(symbol, amount)
                if hedge_symbol:
                    hedge_side = "sell" if side == "buy" else "buy"
                    await self.execute_trade(hedge_symbol, hedge_side, hedge_amount, leverage=1.0)

                logger.info(f"Trade executed: {trade_id}, {symbol}, {side}, {amount} Eddies, Leverage={leverage}")
                return {"id": trade_id, "orders": orders}
            else:
                logger.warning(f"Trade rejected by Neural-Net: {symbol}, {side}")
                raise Exception("Trade not executed: Neural-Net validation failed")
        except Exception as e:
            logger.error(f"Trade execution flatlined: {e}")
            raise

    async def convert_idle_funds(self, target="USDT"):
        try:
            last_trade = db.fetch_one("SELECT timestamp FROM trades ORDER BY timestamp DESC LIMIT 1")
            if not last_trade or (datetime.now() - datetime.fromisoformat(last_trade[0])) > timedelta(hours=24):
                positions = db.fetch_all("SELECT symbol, amount, entry_price FROM positions WHERE side = 'buy'")
                idle_funds = 0
                for pos in positions:
                    current_price = db.fetch_one("SELECT close FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (pos[0],))[0]
                    idle_funds += pos[1] * (current_price - pos[2])
                if idle_funds > 0:
                    order = await self.exchange.create_market_order(f"{pos[0]}/{target}", "sell", idle_funds / current_price)
                    db.execute_query(
                        """
                        INSERT INTO positions (id, symbol, side, amount, entry_price, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (str(uuid.uuid4()), f"{pos[0]}/{target}", "hold", idle_funds, current_price, datetime.now().isoformat())
                    )
                    logger.info(f"Converted {idle_funds} Eddies to {target} during idle time")
        except Exception as e:
            logger.error(f"Idle conversion flatlined: {e}")

    def calculate_atr(self, data):
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        return true_range.rolling(14).mean().iloc[-1]

    def can_use_maker_order(self, book, side):
        spread = book["asks"][0][0] - book["bids"][0][0]
        return spread > 0.001

    async def detect_market_regime(self):
        try:
            data = await self.fetcher.fetch_ohlcv(settings.TRADING["symbol"], "1d", limit=252)
            df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            returns = df["close"].pct_change().dropna()
            volatility = returns.rolling(20).std()
            features = np.column_stack([returns[-100:], volatility[-100:]])
            kmeans = KMeans(n_clusters=3, random_state=42).fit(features)
            regime = kmeans.labels_[-1]
            regime_map = {0: "bull", 1: "bear", 2: "altcoin"}
            logger.info(f"Market regime: {regime_map.get(regime, 'bull')}")
            return regime_map.get(regime, "bull")
        except Exception as e:
            logger.error(f"Regime detection flatlined: {e}")
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
            signals = self.strategies.get_signal(symbol, df, timeframe, strategy)
            df["signal"] = signals
            returns = df["signal"].shift(1) * df["close"].pct_change()
            equity_curve = (1 + returns).cumprod()
            sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
            logger.info(f"Backtest for {symbol} using {strategy}: Sharpe={sharpe}")
            return {
                "sharpe_ratio": sharpe,
                "total_return": returns.sum(),
                "equity_curve": equity_curve.tolist()
            }
        except Exception as e:
            logger.error(f"Backtest flatlined: {e}")
            return {"sharpe_ratio": 0, "total_return": 0, "equity_curve": []}

    def set_sandbox_mode(self, enabled):
        self.exchange.set_sandbox_mode(enabled)

    async def close(self):
        await self.exchange.close()

bot = TradingBot()

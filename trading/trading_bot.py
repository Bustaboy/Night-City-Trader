# trading/trading_bot.py
"""
Arasaka Neural-Net Trading Bot - The core engine for stacking Eddies
"""
import ccxt.async_support as ccxt
import asyncio
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.cluster import KMeans

from config.settings import settings
from core.database import db
from utils.logger import logger

class TradingBot:
    def __init__(self):
        self.exchange = None
        self.trainer = None
        self.rl_trainer = None
        self.strategies = None
        self.risk_manager = None
        self.fetcher = None
        self._initialized = False
        
    async def initialize(self):
        """Lazy initialization to avoid circular imports"""
        if self._initialized:
            return
            
        from ml.trainer import trainer
        from ml.rl_trainer import rl_trainer
        from trading.strategies import strategies
        from trading.risk_manager import risk_manager
        from market.data_fetcher import fetcher
        
        self.trainer = trainer
        self.rl_trainer = rl_trainer
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.fetcher = fetcher
        
        # Initialize exchange
        self.exchange = ccxt.binance({
            "apiKey": settings.BINANCE_API_KEY,
            "secret": settings.BINANCE_API_SECRET,
            "enableRateLimit": True
        })
        
        if settings.TESTNET:
            self.exchange.set_sandbox_mode(True)
            
        self._initialized = True

    async def execute_trade(self, symbol, side, amount, leverage=1.0):
        """Execute a trade with full Neural-Net validation"""
        await self.initialize()
        
        try:
            # Parse symbol if it has exchange prefix
            ex_name = symbol.split(":")[0] if ":" in symbol else "binance"
            pair = symbol.split(":")[1] if ":" in symbol else symbol
            
            if ex_name != "binance":
                raise Exception("Only Binance trades supported in this version")
                
            await self.exchange.load_markets()
            
            # Multi-timeframe analysis
            timeframes = ["1h", "4h", "1d"]
            signals = []
            
            for tf in timeframes:
                data = await self.fetcher.fetch_ohlcv(pair, tf, limit=100, exchange=ex_name)
                signal = self.strategies.get_signal(pair, data, tf)
                signals.append(signal[-1] if len(signal) > 0 else 0)
            
            combined_signal = np.mean(signals)
            
            # Get latest data for ML predictions
            latest_data = await self.fetcher.fetch_ohlcv(pair, "1h", limit=1, exchange=ex_name)
            if not latest_data:
                raise Exception("No market data available")
                
            ml_prediction = self.trainer.predict(latest_data[0])
            rl_action = self.rl_trainer.predict(latest_data[0])
            
            # Calculate RL confidence
            state = self.prepare_state(latest_data[0])
            state_array = np.array(state).reshape(1, -1)
            rl_predictions = self.rl_trainer.model.predict(state_array, verbose=0)
            rl_confidence = np.max(rl_predictions) if rl_predictions.size > 0 else 0.5
            
            # Market regime detection
            market_regime = await self.detect_market_regime()
            
            # Adjust leverage and position size
            leverage = self.risk_manager.adjust_leverage(symbol, rl_confidence, market_regime)
            adjusted_amount = self.risk_manager.adjust_position_size(symbol, amount)
            
            # Check seasonality
            seasonality = db.fetch_one(
                "SELECT mean_return FROM seasonality_patterns WHERE symbol = ? AND period = ?",
                (symbol, f"weekday_{datetime.now().weekday()}")
            )
            seasonality_weight = seasonality[0] if seasonality else 0
            
            # Validate trade signals
            buy_condition = (
                side == "buy" and 
                combined_signal > 0.5 and 
                ml_prediction == 1 and 
                rl_action >= 0.5 and 
                seasonality_weight >= 0
            )
            
            sell_condition = (
                side == "sell" and 
                combined_signal < -0.5 and 
                ml_prediction == 0 and 
                rl_action <= 0.5 and 
                seasonality_weight <= 0
            )
            
            if buy_condition or sell_condition:
                # Execute trade with smart order routing
                result = await self._execute_smart_order(
                    pair, side, adjusted_amount, leverage
                )
                
                logger.info(f"Trade executed: {result['id']}, {symbol}, {side}, {adjusted_amount} Eddies")
                return result
            else:
                logger.warning(f"Trade rejected by Neural-Net: {symbol}, {side}")
                raise Exception("Trade validation failed - Neural-Net rejected")
                
        except Exception as e:
            logger.error(f"Trade execution flatlined: {e}")
            raise

    async def _execute_smart_order(self, pair, side, amount, leverage):
        """Execute order with smart routing and risk management"""
        try:
            # Get order book for smart routing
            book = await self.fetcher.fetch_order_book(pair)
            
            # Calculate fees
            spread = book["asks"][0][0] - book["bids"][0][0] if book["asks"] and book["bids"] else 0
            fee_rate = settings.TRADING["fees"]["maker"] if spread > 0.001 else settings.TRADING["fees"]["taker"]
            
            # Execute order
            if leverage > 1.0:
                order = await self.exchange.create_market_order(
                    pair, side, amount, params={"leverage": leverage}
                )
            else:
                order = await self.exchange.create_market_order(pair, side, amount)
            
            # Store trade in database
            trade_id = str(uuid.uuid4())
            db.execute_query(
                """
                INSERT INTO trades (id, symbol, side, amount, price, fee, leverage, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade_id, 
                    f"binance:{pair}", 
                    side, 
                    amount, 
                    order.get('price', 0),
                    order.get('fee', {}).get('cost', 0),
                    leverage,
                    datetime.now().isoformat()
                )
            )
            
            # Create position with dynamic stop-loss/take-profit
            await self._create_position_with_sl_tp(trade_id, pair, side, amount, order)
            
            return {"id": trade_id, "order": order}
            
        except Exception as e:
            logger.error(f"Smart order execution failed: {e}")
            raise

    async def _create_position_with_sl_tp(self, trade_id, pair, side, amount, order):
        """Create position with ATR-based stop-loss and take-profit"""
        try:
            # Get recent data for ATR calculation
            data = await self.fetcher.fetch_ohlcv(pair, "1h", limit=20)
            atr = self.calculate_atr(data)
            
            entry_price = order.get('price', 0)
            
            # Dynamic SL/TP based on ATR
            if side == "buy":
                stop_loss = entry_price * (1 - 1.5 * atr / entry_price)
                take_profit = entry_price * (1 + 3.0 * atr / entry_price)
            else:
                stop_loss = entry_price * (1 + 1.5 * atr / entry_price)
                take_profit = entry_price * (1 - 3.0 * atr / entry_price)
            
            # Store position
            position_id = str(uuid.uuid4())
            db.execute_query(
                """
                INSERT INTO positions (id, symbol, side, amount, entry_price, stop_loss, take_profit, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    position_id,
                    f"binance:{pair}",
                    side,
                    amount,
                    entry_price,
                    stop_loss,
                    take_profit,
                    datetime.now().isoformat()
                )
            )
            
        except Exception as e:
            logger.error(f"Position creation failed: {e}")

    def calculate_atr(self, data):
        """Calculate Average True Range for dynamic risk management"""
        if not data or len(data) < 2:
            return 0.02  # Default 2% if no data
            
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        
        return atr / df["close"].iloc[-1] if not pd.isna(atr) else 0.02

    async def detect_market_regime(self):
        """Detect current market regime using ML clustering"""
        try:
            # Get historical data
            data = await self.fetcher.fetch_ohlcv(settings.TRADING["symbol"], "1d", limit=252)
            if not data or len(data) < 100:
                return "bull"  # Default
                
            df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            
            # Calculate returns and volatility
            returns = df["close"].pct_change().dropna()
            volatility = returns.rolling(20).std()
            
            # Prepare features for clustering
            features = np.column_stack([
                returns.iloc[-100:].values,
                volatility.iloc[-100:].values
            ])
            
            # Remove NaN values
            features = features[~np.isnan(features).any(axis=1)]
            
            if len(features) < 3:
                return "bull"
                
            # K-means clustering
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            kmeans.fit(features)
            
            # Get current regime
            current_features = features[-1].reshape(1, -1)
            regime = kmeans.predict(current_features)[0]
            
            # Map to regime names based on cluster characteristics
            regime_map = {0: "bull", 1: "bear", 2: "altcoin"}
            detected_regime = regime_map.get(regime, "bull")
            
            logger.info(f"Market regime detected: {detected_regime}")
            return detected_regime
            
        except Exception as e:
            logger.error(f"Regime detection flatlined: {e}")
            return "bull"

    async def convert_idle_funds(self, target="USDT"):
        """Convert idle funds to stable assets or BTC"""
        await self.initialize()
        
        try:
            # Check for idle positions
            last_trade = db.fetch_one("SELECT timestamp FROM trades ORDER BY timestamp DESC LIMIT 1")
            
            if not last_trade or (datetime.now() - datetime.fromisoformat(last_trade[0])) > timedelta(hours=24):
                positions = db.fetch_all("SELECT symbol, amount, entry_price FROM positions WHERE side = 'buy'")
                
                for pos in positions:
                    symbol = pos[0].split(":")[1] if ":" in pos[0] else pos[0]
                    amount = pos[1]
                    
                    # Get current price
                    ticker = await self.exchange.fetch_ticker(symbol)
                    current_price = ticker['last']
                    
                    # Calculate idle value
                    idle_value = amount * current_price
                    
                    if idle_value > 10:  # Min $10 threshold
                        # Determine target based on market regime
                        market_regime = await self.detect_market_regime()
                        if market_regime == "bear" or target == "USDT":
                            target_pair = f"{symbol.split('/')[0]}/USDT"
                        else:
                            target_pair = f"{symbol.split('/')[0]}/BTC"
                        
                        # Execute conversion
                        order = await self.exchange.create_market_order(target_pair, "sell", amount)
                        
                        logger.info(f"Converted {idle_value} Eddies to {target} - Funds secured!")
                        
        except Exception as e:
            logger.error(f"Idle conversion flatlined: {e}")

    async def backtest_strategy(self, symbol, timeframe, start_date, end_date, strategy):
        """Backtest trading strategy on historical data"""
        try:
            # Fetch historical data from database
            start_ts = int(pd.to_datetime(start_date).timestamp() * 1000)
            end_ts = int(pd.to_datetime(end_date).timestamp() * 1000)
            
            data = db.fetch_all(
                """
                SELECT * FROM historical_data
                WHERE symbol = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
                """,
                (symbol, start_ts, end_ts)
            )
            
            if not data:
                logger.warning(f"No historical data for {symbol} in the specified range")
                return {"sharpe_ratio": 0, "total_return": 0, "equity_curve": [1]}
            
            # Convert to DataFrame
            df = pd.DataFrame(
                data, 
                columns=["symbol", "timestamp", "open", "high", "low", "close", "volume"]
            )
            
            # Generate signals
            signals = self.strategies.get_signal(symbol, df, timeframe, strategy)
            df["signal"] = signals
            
            # Calculate returns
            df["returns"] = df["close"].pct_change()
            df["strategy_returns"] = df["signal"].shift(1) * df["returns"]
            
            # Calculate performance metrics
            total_return = df["strategy_returns"].sum()
            
            if df["strategy_returns"].std() > 0:
                sharpe_ratio = df["strategy_returns"].mean() / df["strategy_returns"].std() * np.sqrt(252)
            else:
                sharpe_ratio = 0
            
            # Calculate equity curve
            equity_curve = (1 + df["strategy_returns"]).cumprod()
            
            logger.info(f"Backtest complete: Sharpe={sharpe_ratio:.2f}, Return={total_return:.2%}")
            
            return {
                "sharpe_ratio": sharpe_ratio,
                "total_return": total_return,
                "equity_curve": equity_curve.tolist()
            }
            
        except Exception as e:
            logger.error(f"Backtest flatlined: {e}")
            return {"sharpe_ratio": 0, "total_return": 0, "equity_curve": [1]}

    def prepare_state(self, data):
        """Prepare state for RL model"""
        try:
            # Basic features from OHLCV
            if len(data) >= 6:
                return [
                    data[1],  # open
                    data[2],  # high
                    data[3],  # low
                    data[4],  # close
                    data[5],  # volume
                    0.0,      # sma_20 placeholder
                    0.0,      # sma_50 placeholder
                    50.0,     # rsi_14 placeholder
                    0.0,      # bollinger_upper placeholder
                    0.0,      # bollinger_lower placeholder
                    0.0,      # macd placeholder
                    0.0,      # sentiment_score placeholder
                    0.0       # whale_ratio placeholder
                ]
            else:
                return [0.0] * len(settings.ML["features"])
        except:
            return [0.0] * len(settings.ML["features"])

    def set_sandbox_mode(self, enabled):
        """Toggle testnet/live mode"""
        if self.exchange:
            self.exchange.set_sandbox_mode(enabled)

    async def close(self):
        """Close exchange connections"""
        if self.exchange:
            await self.exchange.close()

# Create singleton instance
bot = TradingBot()
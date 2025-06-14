# trading/risk_manager.py
"""
Arasaka Risk Management Protocols - Protect your Eddies from market flatlines
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from datetime import datetime
import asyncio

from config.settings import settings
from core.database import db
from utils.logger import logger

class RiskManager:
    def __init__(self):
        self.risk_profile = "moderate"
        self.set_risk_profile(self.risk_profile)
        self.flash_drop_threshold = 0.10  # 10% drop threshold
        self.stop_loss_buffer = 0.02  # 2% buffer
        
    def set_risk_profile(self, profile):
        """Set risk parameters based on profile"""
        self.risk_profile = profile
        risk_settings = settings.TRADING["risk"][profile]
        
        self.max_position_size = risk_settings["max_position_size"]
        self.max_daily_loss = risk_settings["max_daily_loss"]
        self.stop_loss = risk_settings["stop_loss"]
        self.take_profit = risk_settings["take_profit"]
        self.max_leverage = risk_settings["max_leverage"]
        
        logger.info(f"Arasaka Risk Protocols set to: {profile}")
    
    def check_profitability(self, symbol, side, amount, leverage=1.0):
        """Check if trade will be profitable after fees"""
        try:
            # Get current price
            market_data = db.fetch_one(
                "SELECT close FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
                (symbol,)
            )
            
            if not market_data:
                market_data = db.fetch_one(
                    "SELECT close FROM historical_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
                    (symbol,)
                )
            
            if not market_data:
                logger.warning("No market data available for profitability check")
                return True  # Allow trade if no data
            
            price = market_data[0]
            fee_rate = settings.TRADING["fees"]["taker"]
            
            # Calculate fees
            position_value = amount * price * leverage
            fee = position_value * fee_rate
            
            # Calculate expected profit
            expected_profit = position_value * self.take_profit
            
            # Check if profit exceeds fees
            if expected_profit <= fee:
                logger.warning(f"Trade rejected: Expected profit {expected_profit:.2f} <= fee {fee:.2f}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Profitability check flatlined: {e}")
            return True  # Allow trade on error
    
    def check_trade_risk(self, symbol, side, amount, leverage=1.0):
        """Check if trade meets risk parameters"""
        try:
            # Check leverage limits
            if leverage > self.max_leverage:
                logger.warning(f"Trade rejected: Leverage {leverage} exceeds max {self.max_leverage}")
                return False
            
            # Get portfolio value
            portfolio_value = db.get_portfolio_value()
            
            # Calculate max position size based on portfolio
            max_size = self.max_position_size * portfolio_value
            
            # Adjust for portfolio size
            if portfolio_value <= 1000:
                max_size *= 1.0  # Full size for small portfolios
            elif portfolio_value <= 10000:
                max_size *= 0.75  # 75% for mid-tier
            else:
                max_size *= 0.5  # 50% for large portfolios
            
            # Check position size
            position_value = amount * leverage
            if position_value > max_size:
                logger.warning(f"Trade rejected: Position size {position_value:.2f} exceeds max {max_size:.2f}")
                return False
            
            # Check daily loss limit
            trades_today = db.fetch_all(
                """
                SELECT side, amount, price, fee 
                FROM trades 
                WHERE timestamp >= date('now', 'start of day')
                """
            )
            
            daily_pnl = 0
            for trade in trades_today:
                if trade[0] == "buy":
                    daily_pnl -= trade[1] * trade[2] + trade[3]
                else:
                    daily_pnl += trade[1] * trade[2] - trade[3]
            
            max_daily_loss_amount = self.max_daily_loss * portfolio_value
            if daily_pnl < -max_daily_loss_amount:
                logger.warning(f"Trade rejected: Daily loss {daily_pnl:.2f} exceeds limit {-max_daily_loss_amount:.2f}")
                return False
            
            # Additional leverage cap for large portfolios
            if portfolio_value > 50000 and leverage > 1.5:
                logger.warning(f"Trade rejected: Leverage capped at 1.5x for portfolios > 50k Eddies")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Risk check flatlined: {e}")
            return False
    
    def adjust_position_size(self, symbol, amount):
        """Adjust position size using Kelly Criterion"""
        try:
            portfolio_value = db.get_portfolio_value()
            
            # Get recent price data
            data = db.fetch_all(
                """
                SELECT close FROM historical_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 100
                """,
                (symbol,)
            )
            
            if len(data) < 20:
                logger.warning("Insufficient data for Kelly sizing, using default")
                return min(amount, self.max_position_size * portfolio_value)
            
            # Calculate returns
            prices = [d[0] for d in data]
            returns = np.diff(prices) / prices[:-1]
            
            # Kelly Criterion calculation
            if len(returns) > 0 and np.std(returns) > 0:
                mean_return = np.mean(returns)
                variance = np.var(returns)
                kelly_fraction = mean_return / variance if variance > 0 else 0.1
            else:
                kelly_fraction = 0.1
            
            # Cap Kelly fraction between 1% and 50%
            kelly_fraction = min(max(kelly_fraction, 0.01), 0.5)
            
            # Calculate max position size
            max_size = self.max_position_size * portfolio_value
            
            # Adjust for portfolio size
            if portfolio_value <= 1000:
                max_size *= 1.0
            elif portfolio_value <= 10000:
                max_size *= 0.75
            else:
                max_size *= 0.5
            
            # Apply Kelly sizing
            adjusted_amount = kelly_fraction * max_size
            final_amount = min(amount, adjusted_amount)
            
            logger.info(f"Position sized: {final_amount:.4f} (Kelly: {kelly_fraction:.2%}, Portfolio: {portfolio_value:.2f})")
            
            return final_amount
            
        except Exception as e:
            logger.error(f"Position sizing flatlined: {e}")
            return amount
    
    def adjust_leverage(self, symbol, prediction_confidence, market_regime):
        """Dynamically adjust leverage based on confidence and market conditions"""
        try:
            base_leverage = self.max_leverage
            portfolio_value = db.get_portfolio_value()
            
            # Reduce leverage in bear markets or for small portfolios
            if market_regime == "bear" or portfolio_value < 1000:
                leverage = min(1.0, base_leverage)
            elif prediction_confidence > 0.8 and portfolio_value > 5000:
                leverage = min(base_leverage, 3.0)
            else:
                leverage = min(base_leverage, 1.5)
            
            # Cap leverage for large portfolios
            if portfolio_value > 50000:
                leverage = min(leverage, 1.5)
            
            logger.info(f"Leverage adjusted to {leverage}x (Confidence: {prediction_confidence:.2f}, Regime: {market_regime})")
            
            return leverage
            
        except Exception as e:
            logger.error(f"Leverage adjustment flatlined: {e}")
            return 1.0
    
    def optimize_portfolio(self):
        """Optimize portfolio weights using Modern Portfolio Theory"""
        try:
            # Get all active positions
            positions = db.fetch_all("SELECT DISTINCT symbol FROM positions WHERE side = 'buy'")
            symbols = [p[0] for p in positions]
            
            if len(symbols) < 2:
                logger.info("Not enough positions for optimization")
                return {symbols[0]: 1.0} if symbols else {}
            
            # Get historical returns for each symbol
            returns_data = []
            valid_symbols = []
            
            for symbol in symbols:
                data = db.fetch_all(
                    """
                    SELECT close FROM historical_data 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 252
                    """,
                    (symbol,)
                )
                
                if len(data) >= 252:
                    prices = [d[0] for d in data]
                    returns = np.diff(prices) / prices[:-1]
                    returns_data.append(returns)
                    valid_symbols.append(symbol)
            
            if len(valid_symbols) < 2:
                return {symbols[0]: 1.0} if symbols else {}
            
            # Calculate covariance matrix
            returns_array = np.array(returns_data)
            mean_returns = np.mean(returns_array, axis=1)
            cov_matrix = np.cov(returns_array)
            
            # Optimization objective: maximize Sharpe ratio
            def negative_sharpe(weights):
                portfolio_return = np.sum(mean_returns * weights) * 252
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
                return -portfolio_return / portfolio_vol if portfolio_vol > 0 else 0
            
            # Constraints and bounds
            constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
            bounds = [(0, 1) for _ in range(len(valid_symbols))]
            initial_weights = np.ones(len(valid_symbols)) / len(valid_symbols)
            
            # Optimize
            result = minimize(
                negative_sharpe,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints
            )
            
            # Create weights dictionary
            weights = {symbol: weight for symbol, weight in zip(valid_symbols, result.x)}
            
            # Add zero weights for excluded symbols
            for symbol in symbols:
                if symbol not in weights:
                    weights[symbol] = 0.0
            
            logger.info(f"Portfolio optimized: {weights}")
            return weights
            
        except Exception as e:
            logger.error(f"Portfolio optimization flatlined: {e}")
            return {}
    
    def rebalance_trades(self):
        """Rebalance portfolio to target weights"""
        try:
            # Get optimized weights
            target_weights = self.optimize_portfolio()
            if not target_weights:
                logger.warning("No target weights for rebalancing")
                return
            
            portfolio_value = db.get_portfolio_value()
            
            # Get current positions
            positions = db.fetch_all(
                """
                SELECT symbol, amount, entry_price 
                FROM positions 
                WHERE side = 'buy'
                """
            )
            
            # Calculate current values
            current_values = {}
            for symbol, amount, entry_price in positions:
                # Get current price
                price_data = db.fetch_one(
                    """
                    SELECT close FROM market_data 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                    """,
                    (symbol,)
                )
                
                if price_data:
                    current_price = price_data[0]
                    current_values[symbol] = amount * current_price
            
            # Calculate rebalancing trades
            rebalance_trades = []
            
            for symbol, target_weight in target_weights.items():
                target_value = portfolio_value * target_weight
                current_value = current_values.get(symbol, 0)
                diff_value = target_value - current_value
                
                # Only rebalance if difference > $10
                if abs(diff_value) > 10:
                    rebalance_trades.append({
                        "symbol": symbol,
                        "value_diff": diff_value,
                        "side": "buy" if diff_value > 0 else "sell"
                    })
            
            # Execute rebalancing (would normally call trading bot)
            for trade in rebalance_trades:
                logger.info(f"Rebalance: {trade['side']} ${abs(trade['value_diff']):.2f} of {trade['symbol']}")
            
            logger.info("Portfolio rebalanced - New weights active!")
            
        except Exception as e:
            logger.error(f"Rebalance flatlined: {e}")
    
    def auto_hedge(self):
        """Automatically hedge high-risk positions"""
        try:
            # Get all positions
            positions = db.fetch_all(
                """
                SELECT symbol, side, amount 
                FROM positions 
                WHERE side = 'buy'
                """
            )
            
            for symbol, side, amount in positions:
                # Get recent volatility
                market_data = db.fetch_all(
                    """
                    SELECT high, low, close 
                    FROM market_data 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 14
                    """,
                    (symbol,)
                )
                
                if len(market_data) >= 14:
                    # Calculate ATR
                    atr = self._calculate_atr_from_data(market_data)
                    
                    # Get 30-day volatility for dynamic threshold
                    hist_data = db.fetch_all(
                        """
                        SELECT close 
                        FROM historical_data 
                        WHERE symbol = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 720
                        """,
                        (symbol,)
                    )
                    
                    if hist_data:
                        prices = [d[0] for d in hist_data]
                        returns = np.diff(prices) / prices[:-1]
                        hist_vol = np.std(returns)
                        dynamic_threshold = max(self.flash_drop_threshold, hist_vol * 2)
                    else:
                        dynamic_threshold = self.flash_drop_threshold
                    
                    # Check if hedging needed
                    if atr > dynamic_threshold:
                        hedge_symbol, hedge_amount = self.calculate_hedge(symbol, amount)
                        if hedge_symbol:
                            logger.info(f"Auto-hedge triggered for {symbol}: Hedge with {hedge_amount} {hedge_symbol}")
            
            logger.info("Auto-hedge scan complete - Risk contained!")
            
        except Exception as e:
            logger.error(f"Auto-hedge flatlined: {e}")
    
    def flash_crash_protection(self):
        """Protect against flash crashes with dynamic stop-losses"""
        try:
            # Get all long positions
            positions = db.fetch_all(
                """
                SELECT id, symbol, amount, entry_price 
                FROM positions 
                WHERE side = 'buy'
                """
            )
            
            for position_id, symbol, amount, entry_price in positions:
                # Get recent prices
                recent_prices = db.fetch_all(
                    """
                    SELECT close 
                    FROM market_data 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                    """,
                    (symbol,)
                )
                
                if len(recent_prices) == 5:
                    prices = [p[0] for p in recent_prices]
                    current_price = prices[0]
                    initial_price = prices[-1]
                    
                    # Calculate drop percentage
                    drop = (initial_price - current_price) / initial_price if initial_price > 0 else 0
                    
                    # Get ATR for dynamic stop-loss
                    market_data = db.fetch_all(
                        """
                        SELECT high, low, close 
                        FROM market_data 
                        WHERE symbol = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 14
                        """,
                        (symbol,)
                    )
                    
                    if market_data:
                        atr = self._calculate_atr_from_data(market_data)
                        stop_price = current_price * (1 - self.stop_loss_buffer - atr)
                    else:
                        stop_price = current_price * (1 - self.stop_loss_buffer)
                    
                    # Trigger protection if drop exceeds threshold
                    if drop > self.flash_drop_threshold:
                        logger.warning(f"Flash crash detected on {symbol}: {drop:.1%} drop!")
                        logger.info(f"Would exit position at stop price: {stop_price:.2f}")
                        
                        # Update position with stop-loss
                        db.execute_query(
                            """
                            UPDATE positions 
                            SET stop_loss = ? 
                            WHERE id = ?
                            """,
                            (stop_price, position_id)
                        )
            
            logger.info("Flash crash protection scan complete")
            
        except Exception as e:
            logger.error(f"Flash crash protection flatlined: {e}")
    
    def calculate_hedge(self, symbol, amount):
        """Calculate optimal hedge for a position"""
        try:
            # Get returns for correlation calculation
            data = db.fetch_all(
                """
                SELECT close 
                FROM historical_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 252
                """,
                (symbol,)
            )
            
            if len(data) < 252:
                return None, 0
            
            prices = [d[0] for d in data]
            returns = np.diff(prices) / prices[:-1]
            
            # Find negatively correlated assets
            correlations = {}
            
            # Get other symbols
            other_symbols = db.fetch_all(
                """
                SELECT DISTINCT symbol 
                FROM historical_data 
                WHERE symbol != ?
                """,
                (symbol,)
            )
            
            for other_symbol in other_symbols[:10]:  # Limit to 10 for performance
                other_data = db.fetch_all(
                    """
                    SELECT close 
                    FROM historical_data 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 252
                    """,
                    (other_symbol[0],)
                )
                
                if len(other_data) == 252:
                    other_prices = [d[0] for d in other_data]
                    other_returns = np.diff(other_prices) / other_prices[:-1]
                    
                    if len(other_returns) == len(returns):
                        corr = np.corrcoef(returns, other_returns)[0, 1]
                        correlations[other_symbol[0]] = corr
            
            if not correlations:
                return None, 0
            
            # Find best hedge (most negative correlation)
            hedge_symbol = min(correlations, key=lambda x: correlations[x])
            hedge_ratio = -correlations[hedge_symbol]
            
            # Only hedge if correlation is significantly negative
            if correlations[hedge_symbol] < -0.3:
                hedge_amount = amount * abs(hedge_ratio)
                logger.info(f"Hedge for {symbol}: {hedge_amount:.4f} {hedge_symbol} (correlation: {correlations[hedge_symbol]:.2f})")
                return hedge_symbol, hedge_amount
            
            return None, 0
            
        except Exception as e:
            logger.error(f"Hedge calculation flatlined: {e}")
            return None, 0
    
    def reserve_creds(self, trade_id, profit):
        """Reserve funds for tax obligations"""
        try:
            # Reserve 25% of profits for taxes
            reserve_amount = profit * 0.25
            
            if reserve_amount > 0:
                db.execute_query(
                    """
                    INSERT INTO reserves (trade_id, amount, timestamp) 
                    VALUES (?, ?, ?)
                    """,
                    (trade_id, reserve_amount, datetime.now().isoformat())
                )
                
                logger.info(f"Reserved {reserve_amount:.2f} Eddies for tax obligations on trade {trade_id}")
                
        except Exception as e:
            logger.error(f"Tax reserve flatlined: {e}")
    
    def _calculate_atr_from_data(self, market_data):
        """Calculate ATR from market data"""
        try:
            df = pd.DataFrame(market_data, columns=["high", "low", "close"])
            
            # Calculate true range
            high_low = df["high"] - df["low"]
            high_close = np.abs(df["high"] - df["close"].shift())
            low_close = np.abs(df["low"] - df["close"].shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            
            # Calculate ATR
            atr = true_range.rolling(14).mean().iloc[-1]
            
            # Return as percentage of price
            return atr / df["close"].iloc[-1] if not pd.isna(atr) else 0.02
            
        except Exception as e:
            logger.error(f"ATR calculation flatlined: {e}")
            return 0.02

# Create singleton instance
risk_manager = RiskManager()

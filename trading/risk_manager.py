# trading/risk_manager.py
from config.settings import settings
from core.database import db
from utils.logger import logger
import numpy as np
from scipy.optimize import minimize
from datetime import datetime

class RiskManager:
    def __init__(self):
        self.risk_profile = "moderate"
        self.set_risk_profile(self.risk_profile)

    def set_risk_profile(self, profile):
        self.risk_profile = profile
        self.max_position_size = settings.TRADING["risk"][profile]["max_position_size"]
        self.max_daily_loss = settings.TRADING["risk"][profile]["max_daily_loss"]
        self.stop_loss = settings.TRADING["risk"][profile]["stop_loss"]
        self.take_profit = settings.TRADING["risk"][profile]["take_profit"]
        self.max_leverage = settings.TRADING["risk"][profile]["max_leverage"]
        logger.info(f"Arasaka Risk Protocols locked: {profile}")

    def check_profitability(self, symbol, side, amount, leverage=1.0):
        try:
            market_data = db.fetch_one(
                "SELECT close FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
                (symbol,)
            )
            if not market_data:
                logger.warning("No market data in the Net")
                return False
            price = market_data[0]
            fee_rate = settings.TRADING["fees"]["taker"]
            fee = amount * price * fee_rate * leverage
            expected_profit = amount * price * self.take_profit * leverage
            if expected_profit <= fee:
                logger.warning(f"Trade rejected: Profit {expected_profit} <= fee {fee}")
                return False
            return True
        except Exception as e:
            logger.error(f"Profitability check flatlined: {e}")
            return False

    def check_trade_risk(self, symbol, side, amount, leverage=1.0):
        try:
            if leverage > self.max_leverage:
                logger.warning(f"Trade rejected: Leverage {leverage} exceeds {self.max_leverage}")
                return False
            portfolio_value = db.get_portfolio_value()
            if amount * leverage > self.max_position_size * portfolio_value:
                logger.warning(f"Trade rejected: Position size exceeds {self.max_position_size * portfolio_value}")
                return False
            trades_today = db.fetch_all(
                "SELECT amount, price FROM trades WHERE timestamp >= date('now', 'start of day')"
            )
            daily_pnl = sum(t[0] * t[1] * (-1 if side == "sell" else 1) for t in trades_today)
            if daily_pnl < -self.max_daily_loss * portfolio_value:
                logger.warning(f"Trade rejected: Daily loss exceeds {self.max_daily_loss * portfolio_value}")
                return False
            return True
        except Exception as e:
            logger.error(f"Risk check flatlined: {e}")
            return False

    def adjust_position_size(self, symbol, amount):
        try:
            portfolio_value = db.get_portfolio_value()
            data = db.fetch_all(
                "SELECT close FROM historical_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 20",
                (symbol,)
            )
            returns = np.diff([d[0] for d in data]) / [d[0] for d in data][:-1]
            volatility = np.std(returns)
            kelly_fraction = (np.mean(returns) / volatility**2) if volatility > 0 else 0.1
            kelly_fraction = min(max(kelly_fraction, 0.01), 0.5)
            max_size = self.max_position_size * portfolio_value
            adjusted = kelly_fraction * max_size
            logger.info(f"Adjusted size for {symbol}: {adjusted} Eddies based on {portfolio_value} portfolio")
            return min(amount, adjusted)
        except Exception as e:
            logger.error(f"Position sizing flatlined: {e}")
            return amount

    def adjust_leverage(self, symbol, prediction_confidence, market_regime):
        try:
            base_leverage = self.max_leverage
            portfolio_value = db.get_portfolio_value()
            if market_regime == "bear" or portfolio_value < 1000:
                leverage = min(1.0, base_leverage)
            elif prediction_confidence > 0.8 and portfolio_value > 5000:
                leverage = min(base_leverage, 3.0)
            else:
                leverage = min(base_leverage, 1.5)
            logger.info(f"Adjusted leverage for {symbol}: {leverage}x based on {portfolio_value} Eddies")
            return leverage
        except Exception as e:
            logger.error(f"Leverage adjustment flatlined: {e}")
            return 1.0

    def optimize_portfolio(self):
        try:
            symbols = db.fetch_all("SELECT DISTINCT symbol FROM positions")
            symbols = [s[0] for s in symbols]
            if not symbols:
                return {}
            returns = []
            for symbol in symbols:
                data = db.fetch_all(
                    "SELECT close FROM historical_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 252",
                    (symbol,)
                )
                if len(data) < 252:
                    continue
                ret = np.diff([d[0] for d in data]) / [d[0] for d in data][:-1]
                returns.append(ret)
            returns = np.array(returns)
            cov_matrix = np.cov(returns)
            def objective(weights):
                port_return = np.sum(returns.mean(axis=1) * weights) * 252
                port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
                return -port_return / port_vol
            constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
            bounds = [(0, 1) for _ in range(len(symbols))]
            result = minimize(objective, np.ones(len(symbols)) / len(symbols), bounds=bounds, constraints=constraints)
            weights = {s: w for s, w in zip(symbols, result.x)}
            logger.info(f"Portfolio optimized: {weights}")
            return weights

    def calculate_hedge(self, symbol, amount):
        try:
            data = db.fetch_all(
                "SELECT close FROM historical_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 252",
                (symbol,)
            )
            returns = np.diff([d[0] for d in data]) / [d[0] for d in data][:-1]
            correlations = {}
            for other_symbol in db.fetch_all("SELECT DISTINCT symbol FROM historical_data"):
                other_symbol = other_symbol[0]
                if other_symbol == symbol:
                    continue
                other_data = db.fetch_all(
                    "SELECT close FROM historical_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 252",
                    (other_symbol,)
                )
                if len(other_data) < 252:
                    continue
                other_returns = np.diff([d[0] for d in other_data]) / [d[0] for d in other_data][:-1]
                corr = np.corrcoef(returns, other_returns)[0, 1]
                correlations[other_symbol] = corr
            if correlations:
                hedge_symbol = max(correlations, key=lambda x: abs(correlations[x]))
                hedge_ratio = -correlations[hedge_symbol]
                hedge_amount = amount * abs(hedge_ratio)
                logger.info(f"Hedge for {symbol}: {hedge_amount} {hedge_symbol}")
                return hedge_symbol, hedge_amount
            return None, 0
        except Exception as e:
            logger.error(f"Hedge calculation flatlined: {e}")
            return None, 0

    def reserve_creds(self, trade_id, profit):
        try:
            reserve_amount = profit * 0.25  # 25% reserve for tax man
            db.execute_query(
                "INSERT INTO reserves (trade_id, amount, timestamp) VALUES (?, ?, ?)",
                (trade_id, reserve_amount, datetime.now().isoformat())
            )
            logger.info(f"Reserved {reserve_amount} Eddies for tax creds on trade {trade_id}")
        except Exception as e:
            logger.error(f"Cred reserve flatlined: {e}")

risk_manager = RiskManager()

# trading/risk_manager.py
from config.settings import settings
from core.database import db
from utils.logger import logger

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
        logger.info(f"Risk profile set to: {profile}")

    def check_profitability(self, symbol, side, amount):
        try:
            # Fetch current price
            market_data = db.fetch_one(
                "SELECT close FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
                (symbol,)
            )
            if not market_data:
                logger.warning("No market data available for profitability check")
                return False
            price = market_data[0]
            fee_rate = settings.TRADING["fees"]["taker"]
            fee = amount * price * fee_rate
            expected_profit = amount * price * self.take_profit
            if expected_profit <= fee:
                logger.warning(f"Trade rejected: Expected profit {expected_profit} <= fee {fee}")
                return False
            return True
        except Exception as e:
            logger.error(f"Profitability check failed: {e}")
            return False

    def check_trade_risk(self, symbol, side, amount):
        try:
            # Check position size
            total_position = db.fetch_one(
                "SELECT SUM(amount) FROM positions WHERE symbol = ?", (symbol,)
            )[0] or 0
            portfolio_value = 100  # Placeholder; should integrate real portfolio value
            if amount > self.max_position_size * portfolio_value:
                logger.warning(f"Trade rejected: Position size exceeds {self.max_position_size}")
                return False

            # Check daily loss
            trades_today = db.fetch_all(
                "SELECT amount, price FROM trades WHERE timestamp >= date('now', 'start of day')"
            )
            daily_pnl = sum(t[0] * t[1] * (-1 if side == "sell" else 1) for t in trades_today)
            if daily_pnl < -self.max_daily_loss * portfolio_value:
                logger.warning(f"Trade rejected: Daily loss exceeds {self.max_daily_loss}")
                return False

            return True
        except Exception as e:
            logger.error(f"Risk check failed: {e}")
            return False

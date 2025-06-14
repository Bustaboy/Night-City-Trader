# trading/risk_manager.py
from config.settings import settings
from core.database import db
from utils.logger import logger

class RiskManager:
    def __init__(self):
        self.max_position_size = settings.TRADING["risk"]["max_position_size"]
        self.max_daily_loss = settings.TRADING["risk"]["max_daily_loss"]

    def check_trade_risk(self, symbol, side, amount):
        try:
            # Check position size
            total_position = db.fetch_one(
                "SELECT SUM(amount) FROM positions WHERE symbol = ?", (symbol,)
            )[0] or 0
            if amount > self.max_position_size * 100:  # Assuming portfolio value ~$100
                logger.warning(f"Trade rejected: Position size exceeds {self.max_position_size}")
                return False

            # Check daily loss
            trades_today = db.fetch_all(
                "SELECT amount, price FROM trades WHERE timestamp >= date('now', 'start of day')"
            )
            daily_pnl = sum(t[0] * t[1] * (-1 if side == "sell" else 1) for t in trades_today)
            if daily_pnl < -self.max_daily_loss * 100:
                logger.warning(f"Trade rejected: Daily loss exceeds {self.max_daily_loss}")
                return False
            return True
        except Exception as e:
            logger.error(f"Risk check failed: {e}")
            return False

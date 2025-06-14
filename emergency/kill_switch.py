# emergency/kill_switch.py
from trading.trading_bot import bot
from utils.logger import logger

class KillSwitch:
    def activate(self):
        try:
            asyncio.run(bot.close())
            logger.critical("Kill switch activated: All trading stopped")
        except Exception as e:
            logger.error(f"Kill switch failed: {e}")
            raise

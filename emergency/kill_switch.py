# emergency/kill_switch.py
from trading.trading_bot import bot
from market.data_fetcher import fetcher
from market.pair_selector import pair_selector
from utils.logger import logger

class KillSwitch:
    async def activate(self):
        try:
            await bot.close()
            await fetcher.close()
            await pair_selector.close()
            logger.critical("Kill switch activated: All trading stopped")
        except Exception as e:
            logger.error(f"Kill switch failed: {e}")
            raise

kill_switch = KillSwitch()

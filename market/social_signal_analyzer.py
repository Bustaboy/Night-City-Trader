# market/social_signal_analyzer.py
import requests
from config.settings import settings
from utils.logger import logger

class SocialSignalAnalyzer:
    def __init__(self):
        self.api_key = settings.SOCIAL["tradingview_api_key"]
        self.base_url = "https://api.tradingview.com/v1/signals"

    async def get_signal(self, symbol):
        try:
            response = requests.get(
                f"{self.base_url}?symbol={symbol}&api_key={self.api_key}"
            )
            response.raise_for_status()
            signal = response.json().get("signal", "neutral")
            score = 1 if signal == "buy" else -1 if signal == "sell" else 0
            logger.info(f"Social signal for {symbol}: {score}")
            return score
        except Exception as e:
            logger.error(f"Social signal failed for {symbol}: {e}")
            return 0

social_analyzer = SocialSignalAnalyzer()

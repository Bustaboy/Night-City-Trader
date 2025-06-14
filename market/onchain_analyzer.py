# market/onchain_analyzer.py
import requests
from config.settings import settings
from utils.logger import logger

class OnChainAnalyzer:
    def __init__(self):
        self.api_key = settings.ONCHAIN["glassnode_api_key"]
        self.base_url = "https://api.glassnode.com/v1/metrics"

    async def get_metrics(self, symbol):
        try:
            asset = symbol.split("/")[0]
            response = requests.get(
                f"{self.base_url}/transactions/transfers_volume_to_exchanges_sum?a={asset}&api_key={self.api_key}"
            )
            response.raise_for_status()
            data = response.json()
            whale_ratio = sum(d["v"] for d in data[-10:]) / 10  # Average whale deposits
            score = 1 if whale_ratio < 100 else -1 if whale_ratio > 1000 else 0
            logger.info(f"On-chain score for {symbol}: {score}")
            return score
        except Exception as e:
            logger.error(f"On-chain analysis failed for {symbol}: {e}")
            return 0

onchain_analyzer = OnChainAnalyzer()

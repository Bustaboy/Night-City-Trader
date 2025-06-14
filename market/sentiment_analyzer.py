# market/sentiment_analyzer.py
import requests
from config.settings import settings
from utils.logger import logger

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = settings.SENTIMENT["api_key"]
        self.base_url = "https://api.cryptopanic.com/v1/posts"

    async def get_sentiment(self, symbol):
        try:
            response = requests.get(
                f"{self.base_url}?auth_token={self.api_key}&filter=important&currencies={symbol.split('/')[0]}"
            )
            response.raise_for_status()
            posts = response.json()["results"]
            sentiment_score = sum(1 if p["votes"]["bullish"] > p["votes"]["bearish"] else -1 for p in posts) / max(len(posts), 1)
            logger.info(f"Sentiment score for {symbol}: {sentiment_score}")
            return sentiment_score
        except Exception as e:
            logger.error(f"Sentiment analysis failed for {symbol}: {e}")
            return 0.0

sentiment_analyzer = SentimentAnalyzer()

# market/sentiment_analyzer.py
from config.settings import settings
from utils.logger import logger
import requests
import tweepy
import re

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = settings.SENTIMENT["api_key"]
        self.sources = settings.SENTIMENT["sources"]
        self.auth = tweepy.OAuthHandler(settings.X_API_KEY, settings.X_API_SECRET)
        self.auth.set_access_token(settings.X_ACCESS_TOKEN, settings.X_ACCESS_TOKEN_SECRET)
        self.api = tweepy.API(self.auth)

    async def analyze_sentiment(self, symbol):
        try:
            sentiment_score = 0
            if "x" in self.sources:
                query = f"${symbol} -filter:retweets"
                tweets = self.api.search_tweets(q=query, lang="en", count=100)
                for tweet in tweets:
                    text = tweet.text.lower()
                    if re.search(r"\b(bull|moon|to the moon|pump)\b", text):
                        sentiment_score += 0.1
                    elif re.search(r"\b(bear|dump|crash)\b", text):
                        sentiment_score -= 0.1
            if "cryptopanic" in self.sources and self.api_key:
                response = requests.get(f"https://cryptopanic.com/api/v1/posts/?auth_token={self.api_key}&currencies={symbol}")
                response.raise_for_status()
                data = response.json()
                for post in data["results"]:
                    if post["sentiment"] == "bullish":
                        sentiment_score += 0.2
                    elif post["sentiment"] == "bearish":
                        sentiment_score -= 0.2
            sentiment_score = max(min(sentiment_score, 1.0), -1.0)  # Normalize
            logger.info(f"Sentiment for {symbol}: {sentiment_score}")
            return {"score": sentiment_score}
        except Exception as e:
            logger.error(f"Sentiment analysis flatlined: {e}")
            return {"score": 0.0}

    async def auto_exploit_trends(self):
        try:
            symbols = db.fetch_all("SELECT DISTINCT symbol FROM trades")
            for symbol in [s[0] for s in symbols]:
                sentiment = await self.analyze_sentiment(symbol)
                if sentiment["score"] > 0.7:
                    asyncio.run(bot.execute_trade(symbol, "buy", 0.001))  # Default amount
                elif sentiment["score"] < -0.7:
                    asyncio.run(bot.execute_trade(symbol, "sell", 0.001))
            logger.info("Auto-exploited social trends - Eddies stacked!")
        except Exception as e:
            logger.error(f"Trend exploitation flatlined: {e}")

sentiment_analyzer = SentimentAnalyzer()

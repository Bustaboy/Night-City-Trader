# market/sentiment_analyzer.py
from core.database import db
import tweepy
import re
from config.settings import settings
from utils.logger import logger
import requests

class SentimentAnalyzer:
    def __init__(self):
        self.api_key = settings.SENTIMENT["api_key"]
        self.sources = settings.SENTIMENT["sources"]
        self.client = tweepy.Client(
            consumer_key=settings.X_API_KEY,
            consumer_secret=settings.X_API_SECRET,
            access_token=settings.X_ACCESS_TOKEN,
            access_token_secret=settings.X_ACCESS_TOKEN_SECRET
        )
        self.x_weight = 0.6
        self.cryptopanic_weight = 0.4

    async def analyze_sentiment(self, symbol):
        try:
            total_score = 0
            count = 0
            if "x" in self.sources:
                query = f"${symbol} -filter:retweets"
                tweets = self.client.search_recent_tweets(query=query, max_results=100, tweet_fields=["created_at"])
                for tweet in tweets.data or []:
                    text = tweet.text.lower()
                    score = 0
                    bull_keywords = r"\b(bull|moon|to the moon|pump)\b"
                    bear_keywords = r"\b(bear|dump|crash)\b"
                    bull_count = len(re.findall(bull_keywords, text))
                    bear_count = len(re.findall(bear_keywords, text))
                    score += bull_count * 0.1 - bear_count * 0.1
                    total_score += score
                    count += 1
            if "cryptopanic" in self.sources and self.api_key:
                response = requests.get(f"https://cryptopanic.com/api/v1/posts/?auth_token={self.api_key}&currencies={symbol}")
                response.raise_for_status()
                data = response.json()
                for post in data["results"]:
                    if post["sentiment"] == "bullish":
                        total_score += 0.2
                    elif post["sentiment"] == "bearish":
                        total_score -= 0.2
                    count += 1
            sentiment_score = total_score / count if count > 0 else 0
            sentiment_score = max(min(sentiment_score, 1.0), -1.0)  # Normalize
            logger.info(f"Sentiment for {symbol}: {sentiment_score}")
            return {"score": sentiment_score}
        except tweepy.TooManyRequests as e:
            logger.warning(f"X API rate limit hit: {e}")
            return {"score": 0.0}
        except Exception as e:
            logger.error(f"Sentiment analysis flatlined: {e}")
            return {"score": 0.0}

    async def auto_exploit_trends(self):
        try:
            symbols = db.fetch_all("SELECT DISTINCT symbol FROM trades")
            for symbol in [s[0] for s in symbols]:
                sentiment = await self.analyze_sentiment(symbol)
                if sentiment["score"] > 0.7:
                    asyncio.run(bot.execute_trade(symbol, "buy", 0.001))
                elif sentiment["score"] < -0.7:
                    asyncio.run(bot.execute_trade(symbol, "sell", 0.001))
            logger.info("Auto-exploited social trends - Eddies stacked!")
        except Exception as e:
            logger.error(f"Trend exploitation flatlined: {e}")

sentiment_analyzer = SentimentAnalyzer()

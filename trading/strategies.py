# trading/strategies.py
import pandas as pd
import numpy as np
from config.settings import settings
from utils.logger import logger

class TradingStrategies:
    def __init__(self):
        self.config = settings.TRADING["strategies"]

    def calculate_indicators(self, df):
        df["atr"] = (df["high"].rolling(14).max() - df["low"].rolling(14).min())
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["std_20"] = df["close"].rolling(window=20).std()
        df["bollinger_upper"] = df["sma_20"] + 2 * df["std_20"]
        df["bollinger_lower"] = df["sma_20"] - 2 * df["std_20"]
        return df

    def get_signal(self, symbol, data, timeframe, strategy="breakout"):
        try:
            if isinstance(data, list):
                df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            else:
                df = data.copy()
            df = self.calculate_indicators(df)
            
            if strategy == "breakout":
                threshold = self.config["breakout"]["breakout_threshold"]
                df["signal"] = np.where(
                    df["close"] > df["close"].shift(1) + threshold * df["atr"].shift(1), 1,
                    np.where(df["close"] < df["close"].shift(1) - threshold * df["atr"].shift(1), -1, 0)
                )
            elif strategy == "mean_reversion":
                df["signal"] = np.where(
                    df["rsi"] < self.config["mean_reversion"]["rsi_lower"], 1,
                    np.where(df["rsi"] > self.config["mean_reversion"]["rsi_upper"], -1, 0)
                )
            else:
                df["signal"] = 0
            
            logger.info(f"Generated {strategy} signals for {symbol} on {timeframe}")
            return df["signal"].values
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return np.zeros(len(df))

strategies = TradingStrategies()

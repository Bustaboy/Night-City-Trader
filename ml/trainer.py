# ml/trainer.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from config.settings import settings
from market.data_fetcher import DataFetcher
import joblib
from utils.logger import logger

class MLTrainer:
    def __init__(self):
        self.model_path = settings.ML["model_path"]
        self.features = settings.ML["features"]
        self.scaler = StandardScaler()
        self.fetcher = DataFetcher()

    def calculate_indicators(self, df):
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["rsi_14"] = 100 - (100 / (1 + rs))
        # Bollinger Bands
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["std_20"] = df["close"].rolling(window=20).std()
        df["bollinger_upper"] = df["sma_20"] + 2 * df["std_20"]
        df["bollinger_lower"] = df["sma_20"] - 2 * df["std_20"]
        # MACD
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        return df

    def prepare_data(self, data):
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = self.calculate_indicators(df)
        df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
        df = df.dropna()
        X = df[self.features]
        y = df["target"]
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled, y

    async def train(self, symbol=None):
        try:
            symbol = symbol or settings.TRADING["symbol"]
            data = await self.fetcher.fetch_historical_data(symbol, settings.TRADING["timeframe"], settings.ML["historical_data_years"])
            X, y = self.prepare_data(data)
            model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1)
            model.fit(X, y)
            joblib.dump(model, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            return model
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise

    def predict(self, data):
        try:
            model = joblib.load(self.model_path)
            df = pd.DataFrame([data], columns=["timestamp", "open", "high", "low", "close", "volume"])
            df = self.calculate_indicators(df)
            X = df[self.features]
            X_scaled = self.scaler.transform(X)
            prediction = model.predict(X_scaled)[0]
            logger.info(f"Prediction made: {prediction}")
            return prediction
        except FileNotFoundError:
            logger.error("Model not found; please train first")
            raise Exception("Model not found")

trainer = MLTrainer()

# ml/trainer.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from config.settings import settings
from market.data_fetcher import fetcher
import joblib
from utils.logger import logger

class MLTrainer:
    def __init__(self):
        self.model_path = settings.ML["model_path"]
        self.features = settings.ML["features"]
        self.scaler = StandardScaler()
        self.fetcher = fetcher

    def calculate_indicators(self, df):
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["rsi_14"] = 100 - (100 / (1 + rs))
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["std_20"] = df["close"].rolling(window=20).std()
        df["bollinger_upper"] = df["sma_20"] + 2 * df["std_20"]
        df["bollinger_lower"] = df["sma_20"] - 2 * df["std_20"]
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["sentiment_score"] = 0.0  # Placeholder, updated by sentiment_analyzer
        df["whale_ratio"] = 0.0  # Placeholder, updated by onchain_analyzer
        return df

    def analyze_seasonality(self, symbol):
        try:
            data = db.fetch_all(
                "SELECT timestamp, close FROM historical_data WHERE symbol = ?",
                (symbol,)
            )
            df = pd.DataFrame(data, columns=["timestamp", "close"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["month"] = df["timestamp"].dt.month
            df["weekday"] = df["timestamp"].dt.weekday
            for period in ["month", "weekday"]:
                grouped = df.groupby(period)["close"].pct_change().dropna()
                mean_return = grouped.mean()
                volatility = grouped.std()
                for idx in mean_return.index:
                    db.store_seasonality_pattern(symbol, f"{period}_{idx}", mean_return[idx], volatility[idx])
            logger.info(f"Seasonality analyzed for {symbol}")
        except Exception as e:
            logger.error(f"Seasonality analysis failed: {e}")

    def prepare_data(self, data):
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = self.calculate_indicators(df)
        df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
        df = df.dropna()
        X = df[self.features]
        y = df["target"]
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled, y

    async def train(self, data):
        try:
            symbol = data[0][0].split(":")[1] if ":" in data[0][0] else settings.TRADING["symbol"]
            self.analyze_seasonality(symbol)
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
            logger.info(f"Prediction: {prediction}")
            return prediction
        except FileNotFoundError:
            logger.error("Model not found")
            raise Exception("Model not found")

trainer = MLTrainer()

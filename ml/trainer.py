# ml/trainer.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from config.settings import settings
from market.data_fetcher import DataFetcher
import joblib

class MLTrainer:
    def __init__(self):
        self.model_path = settings.ML["model_path"]
        self.features = settings.ML["features"]
        self.scaler = StandardScaler()

    def calculate_indicators(self, df):
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["rsi_14"] = 100 - (100 / (1 + rs))
        return df

    def prepare_data(self, data):
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = self.calculate_indicators(df)
        df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)  # 1 for buy, 0 for sell
        df = df.dropna()
        X = df[self.features]
        y = df["target"]
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled, y

    def train(self, data):
        X, y = self.prepare_data(data)
        model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1)
        model.fit(X, y)
        joblib.dump(model, self.model_path)
        return model

    def predict(self, data):
        model = joblib.load(self.model_path)
        df = pd.DataFrame([data], columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = self.calculate_indicators(df)
        X = df[self.features]
        X_scaled = self.scaler.transform(X)
        return model.predict(X_scaled)[0]  # 1 for buy, 0 for sell

trainer = MLTrainer()

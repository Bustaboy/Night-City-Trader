# ml/trainer.py
"""
Arasaka ML Training Core - XGBoost-powered predictions for maximum Eddies
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import xgboost as xgb
import joblib
import os

from config.settings import settings
from core.database import db
from utils.logger import logger

class MLTrainer:
    def __init__(self):
        self.model_path = settings.ML["model_path"]
        self.features = settings.ML["features"]
        self.scaler = StandardScaler()
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load existing model if available"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info("ML model loaded from disk")
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            self.model = None
    
    def calculate_indicators(self, df):
        """Calculate technical indicators for ML features"""
        try:
            # Simple Moving Averages
            df["sma_20"] = df["close"].rolling(window=20, min_periods=1).mean()
            df["sma_50"] = df["close"].rolling(window=50, min_periods=1).mean()
            
            # RSI
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14, min_periods=1).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14, min_periods=1).mean()
            rs = gain / (loss + 1e-10)  # Avoid division by zero
            df["rsi_14"] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df["std_20"] = df["close"].rolling(window=20, min_periods=1).std()
            df["bollinger_upper"] = df["sma_20"] + 2 * df["std_20"]
            df["bollinger_lower"] = df["sma_20"] - 2 * df["std_20"]
            
            # MACD
            ema12 = df["close"].ewm(span=12, adjust=False, min_periods=1).mean()
            ema26 = df["close"].ewm(span=26, adjust=False, min_periods=1).mean()
            df["macd"] = ema12 - ema26
            
            # Placeholder features (would be updated by other analyzers)
            df["sentiment_score"] = 0.0
            df["whale_ratio"] = 0.0
            
            # Fill any remaining NaN values
            df = df.fillna(method='ffill').fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"Indicator calculation flatlined: {e}")
            # Return df with zero features if calculation fails
            for feature in self.features:
                if feature not in df.columns:
                    df[feature] = 0.0
            return df
    
    def analyze_seasonality(self, symbol):
        """Analyze seasonal patterns in the data"""
        try:
            # Fetch historical data
            data = db.fetch_all(
                """
                SELECT timestamp, close 
                FROM historical_data 
                WHERE symbol = ?
                ORDER BY timestamp
                """,
                (symbol,)
            )
            
            if len(data) < 100:
                logger.warning(f"Insufficient data for seasonality analysis of {symbol}")
                return
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=["timestamp", "close"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["returns"] = df["close"].pct_change()
            
            # Extract time features
            df["month"] = df["timestamp"].dt.month
            df["weekday"] = df["timestamp"].dt.weekday
            df["hour"] = df["timestamp"].dt.hour
            
            # Calculate seasonal patterns
            for period in ["month", "weekday"]:
                grouped = df.groupby(period)["returns"]
                mean_returns = grouped.mean()
                volatility = grouped.std()
                
                # Store patterns in database
                for idx in mean_returns.index:
                    db.store_seasonality_pattern(
                        symbol,
                        f"{period}_{idx}",
                        mean_returns[idx],
                        volatility[idx]
                    )
            
            logger.info(f"Seasonality patterns analyzed for {symbol}")
            
        except Exception as e:
            logger.error(f"Seasonality analysis flatlined: {e}")
    
    def prepare_data(self, data):
        """Prepare data for training"""
        try:
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(
                    data, 
                    columns=["timestamp", "open", "high", "low", "close", "volume"]
                )
            else:
                df = data.copy()
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Create target variable (1 if price goes up, 0 if down)
            df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
            
            # Remove last row (no target)
            df = df[:-1]
            
            # Remove any rows with NaN
            df = df.dropna()
            
            if len(df) < 100:
                raise ValueError("Insufficient data for training")
            
            # Extract features and target
            X = df[self.features].values
            y = df["target"].values
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            return X_scaled, y
            
        except Exception as e:
            logger.error(f"Data preparation flatlined: {e}")
            raise
    
    async def train(self, data):
        """Train the XGBoost model"""
        try:
            logger.info("Starting ML model training...")
            
            # Prepare data
            X, y = self.prepare_data(data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                early_stopping_rounds=10,
                verbose=False
            )
            
            # Evaluate model
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            logger.info(f"Model training complete - Train: {train_score:.3f}, Test: {test_score:.3f}")
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            
            # Save scaler
            scaler_path = self.model_path.replace('.pkl', '_scaler.pkl')
            joblib.dump(self.scaler, scaler_path)
            
            logger.info(f"Model saved to {self.model_path}")
            
            # Analyze seasonality for the symbol
            if len(data) > 0 and isinstance(data[0], (list, tuple)) and len(data[0]) > 0:
                symbol = "binance:BTC/USDT"  # Default symbol
                self.analyze_seasonality(symbol)
            
            return self.model
            
        except Exception as e:
            logger.error(f"Model training flatlined: {e}")
            raise
    
    def predict(self, data):
        """Make prediction on new data"""
        try:
            if self.model is None:
                raise ValueError("No model available - train first!")
            
            # Prepare single data point
            if isinstance(data, (list, tuple)):
                df = pd.DataFrame(
                    [data],
                    columns=["timestamp", "open", "high", "low", "close", "volume"]
                )
            else:
                df = pd.DataFrame([data])
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Extract features
            X = df[self.features].values
            
            # Load scaler if needed
            scaler_path = self.model_path.replace('.pkl', '_scaler.pkl')
            if os.path.exists(scaler_path) and not hasattr(self.scaler, 'mean_'):
                self.scaler = joblib.load(scaler_path)
            
            # Scale features
            if hasattr(self.scaler, 'mean_'):
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X  # Use unscaled if scaler not fitted
            
            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            probability = self.model.predict_proba(X_scaled)[0]
            
            logger.info(f"ML Prediction: {prediction} (confidence: {max(probability):.3f})")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction flatlined: {e}")
            # Return neutral prediction on error
            return 0

# Create singleton instance
trainer = MLTrainer()

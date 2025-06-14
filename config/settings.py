# config/settings.py
"""
Arasaka Configuration Core - All settings for the Neural-Net Trading Matrix
"""
from dotenv import load_dotenv
import os
import yaml

# Load environment variables
load_dotenv()

class Settings:
    """Central configuration management for the Trading Matrix"""
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local_trading.db")
    
    # API Settings
    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Exchange Settings
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    TESTNET = os.getenv("TESTNET", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # External API Keys
    X_API_KEY = os.getenv("X_API_KEY", "")
    X_API_SECRET = os.getenv("X_API_SECRET", "")
    X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
    X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "")
    
    def __init__(self):
        """Load configuration from YAML file"""
        self.load_config()
    
    def load_config(self):
        """Load trading configuration from config.yaml"""
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        # Default configuration if file doesn't exist
        default_config = {
            "trading": {
                "exchanges": ["binance"],
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "amount": 0.001,
                "testnet": True,
                "fees": {
                    "taker": 0.001,
                    "maker": 0.0005
                },
                "risk": {
                    "default": {
                        "max_leverage": 3.0
                    },
                    "conservative": {
                        "max_position_size": 0.005,
                        "max_daily_loss": 0.02,
                        "stop_loss": 0.02,
                        "take_profit": 0.05,
                        "max_leverage": 1.0
                    },
                    "moderate": {
                        "max_position_size": 0.01,
                        "max_daily_loss": 0.05,
                        "stop_loss": 0.05,
                        "take_profit": 0.10,
                        "max_leverage": 2.0
                    },
                    "aggressive": {
                        "max_position_size": 0.02,
                        "max_daily_loss": 0.10,
                        "stop_loss": 0.10,
                        "take_profit": 0.15,
                        "max_leverage": 3.0
                    }
                },
                "strategies": {
                    "breakout": {
                        "atr_period": 14,
                        "breakout_threshold": 2.0
                    },
                    "mean_reversion": {
                        "rsi_upper": 70,
                        "rsi_lower": 30
                    }
                },
                "pair_selection": {
                    "min_volume": 1000000,
                    "min_volatility": 0.02,
                    "max_spread": 0.001,
                    "min_liquidity": 100000,
                    "volume_spike_threshold": 0.5
                }
            },
            "ml": {
                "model_path": "ml/model.pkl",
                "features": [
                    "sma_20",
                    "sma_50", 
                    "rsi_14",
                    "bollinger_upper",
                    "bollinger_lower",
                    "macd",
                    "sentiment_score",
                    "whale_ratio"
                ],
                "train_interval": 86400,
                "batch_size": 1000,
                "historical_data_years": 15
            },
            "rl": {
                "model_path": "ml/rl_model.h5",
                "episodes": 100,
                "gamma": 0.95,
                "epsilon": 1.0,
                "epsilon_decay": 0.995,
                "learning_rate": 0.001,
                "batch_size": 64
            },
            "sentiment": {
                "api_key": os.getenv("CRYPTOPANIC_API_KEY", ""),
                "sources": ["cryptopanic", "x"]
            },
            "social": {
                "tradingview_api_key": os.getenv("TRADINGVIEW_API_KEY", "")
            },
            "onchain": {
                "glassnode_api_key": os.getenv("GLASSNODE_API_KEY", "")
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        # Merge with defaults
                        self._merge_config(default_config, loaded_config)
                        config = loaded_config
                    else:
                        config = default_config
            else:
                config = default_config
                # Save default config
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, "w") as f:
                    yaml.dump(default_config, f, default_flow_style=False)
        except Exception as e:
            print(f"Config load error: {e}, using defaults")
            config = default_config
        
        # Set attributes
        self.TRADING = config.get("trading", default_config["trading"])
        self.ML = config.get("ml", default_config["ml"])
        self.RL = config.get("rl", default_config["rl"])
        self.SENTIMENT = config.get("sentiment", default_config["sentiment"])
        self.SOCIAL = config.get("social", default_config["social"])
        self.ONCHAIN = config.get("onchain", default_config["onchain"])
    
    def _merge_config(self, default, loaded):
        """Recursively merge loaded config with defaults"""
        for key, value in default.items():
            if key not in loaded:
                loaded[key] = value
            elif isinstance(value, dict) and isinstance(loaded[key], dict):
                self._merge_config(value, loaded[key])

# Create global settings instance
settings = Settings()

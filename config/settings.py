# config/settings.py
from dotenv import load_dotenv
import os
import yaml

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local_trading.db")
    API_HOST = os.getenv("API_HOST", "127.0.0.1")
    API_PORT = int(os.getenv("API_PORT", 8000))
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
    TESTNET = os.getenv("TESTNET", "true").lower() == "true"

    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    TRADING = config["trading"]
    ML = config["ml"]

settings = Settings()

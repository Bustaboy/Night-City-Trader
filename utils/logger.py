# utils/logger.py
"""
Arasaka Logging System - Tracks all Neural-Net operations
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging format
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# Create main logger
logger = logging.getLogger("ArasakaMatrix")
logger.setLevel(logging.INFO)

# File handler with rotation
file_handler = RotatingFileHandler(
    "logs/trading.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(log_format, date_format))
logger.addHandler(file_handler)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format, date_format))
logger.addHandler(console_handler)

# Create specialized loggers
trade_logger = logging.getLogger("ArasakaMatrix.Trades")
risk_logger = logging.getLogger("ArasakaMatrix.Risk")
ml_logger = logging.getLogger("ArasakaMatrix.ML")

# Suppress verbose libraries
logging.getLogger("ccxt").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("tensorflow").setLevel(logging.WARNING)

# Log startup
logger.info("=" * 60)
logger.info("Arasaka Neural-Net Trading Matrix initializing...")
logger.info(f"Log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 60)

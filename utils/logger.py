# utils/logger.py
import logging
from config.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="trading.log"
)
logger = logging.getLogger(__name__)

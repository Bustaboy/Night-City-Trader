# utils/alert_manager.py
from utils.logger import logger

class AlertManager:
    def create_alert(self, message):
        logger.info(f"Alert: {message}")
        # Could extend to show GUI popups or write to a file
        return {"status": "alert_created"}

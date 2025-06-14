# utils/alert_manager.py
from utils.logger import logger
import tkinter as tk
from tkinter import messagebox

class AlertManager:
    def create_alert(self, message):
        logger.info(f"Alert: {message}")
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showwarning("Trading Bot Alert", message)
        root.destroy()
        return {"status": "alert_created"}

alert_manager = AlertManager()

# utils/tax_reporter.py
from core.database import db
from utils.logger import logger
import csv
from datetime import datetime

class TaxReporter:
    def __init__(self):
        self.tax_rates = {
            "US": 0.30,  # 30% capital gains
            "Germany": 0.25,  # 25% average
            "UK": 0.20,  # 20% basic rate
            "Portugal": 0.00,  # No crypto tax pre-2023
            "France": 0.30,  # 30% flat rate
            "Japan": 0.20,  # 20% income tax
            "Default": 0.30  # Fallback
        }

    def generate_report(self, country):
        try:
            tax_rate = self.tax_rates.get(country, self.tax_rates["Default"])
            trades = db.fetch_all("SELECT * FROM trades WHERE timestamp LIKE ?", (f"%{datetime.now().year}%",))
            total_profit = 0
            for trade in trades:
                buy_price = db.fetch_one("SELECT price FROM trades WHERE id = ? AND side = 'buy'", (trade["id"],))[0] if trade["side"] == "sell" else 0
                sell_price = trade["price"] if trade["side"] == "sell" else 0
                profit = (sell_price - buy_price) * trade["amount"] - trade["fee"]
                total_profit += profit
            tax_owed = total_profit * tax_rate
            net_after_tax = total_profit - tax_owed
            filename = f"tax_report_{country}_{datetime.now().year}.csv"
            with open(filename, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Year", "Profit (Eddies)", "Tax Owed (Eddies)", "Net After Tax (Eddies)"])
                writer.writerow([datetime.now().year, round(total_profit, 2), round(tax_owed, 2), round(net_after_tax, 2)])
            logger.info(f"Tax report jacked for {country}: {total_profit} Eddies")
            return filename
        except Exception as e:
            logger.error(f"Tax report flatlined: {e}")
            return None

tax_reporter = TaxReporter()

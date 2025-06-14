# utils/tax_reporter.py
from core.database import db
from utils.logger import logger
import csv
from datetime import datetime
import os

class TaxReporter:
    def __init__(self):
        self.tax_rates_file = "config/tax_rates.csv"
        self.load_tax_rates()

    def load_tax_rates(self):
        try:
            if os.path.exists(self.tax_rates_file):
                with open(self.tax_rates_file, "r") as f:
                    reader = csv.DictReader(f)
                    self.rates = {row["country"]: float(row["rate"]) for row in reader}
            else:
                self.rates = {}  # Empty if file missing
                logger.warning("Tax rates file not found, using DB or default")
            # Load from DB as fallback
            db_rates = db.fetch_all("SELECT country, rate FROM tax_rates")
            for row in db_rates:
                self.rates[row[0]] = float(row[1])
        except Exception as e:
            logger.error(f"Tax rates load flatlined: {e}")
            self.rates = {"Default": 0.30}  # Fallback

    def update_tax_rates(self, rates_data):
        try:
            with open(self.tax_rates_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["country", "rate"])
                for country, rate in rates_data.items():
                    writer.writerow([country, rate])
                    db.execute_query("INSERT OR REPLACE INTO tax_rates (country, rate) VALUES (?, ?)", (country, rate))
            self.load_tax_rates()
            logger.info("Tax rates updated and jacked into the Net")
        except Exception as e:
            logger.error(f"Tax rates update flatlined: {e}")

    def generate_report(self, country):
        try:
            tax_rate = self.rates.get(country, self.rates.get("Default", 0.30))
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

# utils/tax_reporter.py
"""
Arasaka Tax Reporter - Keeps the tax man happy while you stack Eddies
"""
import csv
import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup

from core.database import db
from utils.logger import logger

class TaxReporter:
    def __init__(self):
        self.tax_rates_file = "config/tax_rates.csv"
        self.rates = {}
        self.load_tax_rates()
    
    def load_tax_rates(self):
        """Load tax rates from file or database"""
        try:
            # Load from CSV file
            if os.path.exists(self.tax_rates_file):
                with open(self.tax_rates_file, "r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if "country" in row and "rate" in row:
                            self.rates[row["country"]] = float(row["rate"])
            
            # Load from database (overrides CSV)
            db_rates = db.fetch_all("SELECT country, rate FROM tax_rates")
            for country, rate in db_rates:
                self.rates[country] = float(rate)
            
            # Default rates if nothing loaded
            if not self.rates:
                self.rates = {
                    "US": 0.30,
                    "Germany": 0.25,
                    "UK": 0.20,
                    "Portugal": 0.00,
                    "France": 0.30,
                    "Japan": 0.20,
                    "Canada": 0.50,
                    "Australia": 0.45,
                    "Default": 0.30
                }
            
            logger.info(f"Loaded tax rates for {len(self.rates)} countries")
            
        except Exception as e:
            logger.error(f"Tax rates load failed: {e}")
            self.rates = {"Default": 0.30}
    
    def update_tax_rates(self):
        """Update tax rates from online sources"""
        try:
            # Try to fetch from a public API or scrape
            # This is a simplified example - in production, use a reliable tax API
            
            updated_rates = {}
            
            # Example: Try to fetch from a hypothetical API
            try:
                response = requests.get(
                    "https://api.example.com/tax-rates/crypto",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    for country, rate in data.items():
                        updated_rates[country] = float(rate)
            except:
                # Fallback to web scraping or manual updates
                logger.info("API unavailable, using default rates")
            
            # If we got updates, save them
            if updated_rates:
                # Save to CSV
                with open(self.tax_rates_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["country", "rate"])
                    for country, rate in updated_rates.items():
                        writer.writerow([country, rate])
                        
                        # Save to database
                        db.execute_query(
                            "INSERT OR REPLACE INTO tax_rates (country, rate) VALUES (?, ?)",
                            (country, rate)
                        )
                
                self.rates = updated_rates
                logger.info(f"Updated tax rates for {len(updated_rates)} countries")
            else:
                # Create default CSV if it doesn't exist
                if not os.path.exists(self.tax_rates_file):
                    with open(self.tax_rates_file, "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(["country", "rate"])
                        for country, rate in self.rates.items():
                            writer.writerow([country, rate])
                
                logger.info("Using existing tax rates")
            
        except Exception as e:
            logger.error(f"Tax rate update failed: {e}")
    
    def generate_report(self, country):
        """Generate tax report for a specific country"""
        try:
            # Get tax rate
            tax_rate = self.rates.get(country, self.rates.get("Default", 0.30))
            
            # Get current year
            current_year = datetime.now().year
            
            # Fetch all trades for the year
            trades = db.fetch_all(
                """
                SELECT id, symbol, side, amount, price, fee, timestamp
                FROM trades
                WHERE strftime('%Y', timestamp) = ?
                ORDER BY timestamp
                """,
                (str(current_year),)
            )
            
            if not trades:
                logger.warning(f"No trades found for {current_year}")
                return None
            
            # Calculate gains/losses
            positions = {}  # Track positions for FIFO calculation
            total_profit = 0
            total_fees = 0
            trade_details = []
            
            for trade_id, symbol, side, amount, price, fee, timestamp in trades:
                total_fees += fee or 0
                
                if side == "buy":
                    # Add to position
                    if symbol not in positions:
                        positions[symbol] = []
                    positions[symbol].append({
                        "amount": amount,
                        "price": price,
                        "timestamp": timestamp
                    })
                    
                elif side == "sell":
                    # Calculate profit using FIFO
                    if symbol in positions and positions[symbol]:
                        remaining = amount
                        sale_revenue = amount * price
                        cost_basis = 0
                        
                        while remaining > 0 and positions[symbol]:
                            position = positions[symbol][0]
                            
                            if position["amount"] <= remaining:
                                # Use entire position
                                cost_basis += position["amount"] * position["price"]
                                remaining -= position["amount"]
                                positions[symbol].pop(0)
                            else:
                                # Use part of position
                                cost_basis += remaining * position["price"]
                                position["amount"] -= remaining
                                remaining = 0
                        
                        profit = sale_revenue - cost_basis - fee
                        total_profit += profit
                        
                        trade_details.append({
                            "date": timestamp,
                            "symbol": symbol,
                            "amount": amount,
                            "sale_price": price,
                            "cost_basis": cost_basis / amount if amount > 0 else 0,
                            "profit": profit
                        })
            
            # Calculate tax
            tax_owed = max(0, total_profit * tax_rate)
            net_after_tax = total_profit - tax_owed
            
            # Generate report file
            report_filename = f"tax_report_{country}_{current_year}.csv"
            
            with open(report_filename, "w", newline="") as f:
                writer = csv.writer(f)
                
                # Summary section
                writer.writerow(["TAX REPORT SUMMARY"])
                writer.writerow(["Country", country])
                writer.writerow(["Year", current_year])
                writer.writerow(["Tax Rate", f"{tax_rate:.1%}"])
                writer.writerow([])
                writer.writerow(["Total Trades", len(trades)])
                writer.writerow(["Total Profit/Loss", f"{total_profit:.2f}"])
                writer.writerow(["Total Fees", f"{total_fees:.2f}"])
                writer.writerow(["Tax Owed", f"{tax_owed:.2f}"])
                writer.writerow(["Net After Tax", f"{net_after_tax:.2f}"])
                writer.writerow([])
                
                # Trade details
                writer.writerow(["TRADE DETAILS"])
                writer.writerow(["Date", "Symbol", "Amount", "Sale Price", "Cost Basis", "Profit/Loss"])
                
                for detail in trade_details:
                    writer.writerow([
                        detail["date"],
                        detail["symbol"],
                        f"{detail['amount']:.8f}",
                        f"{detail['sale_price']:.2f}",
                        f"{detail['cost_basis']:.2f}",
                        f"{detail['profit']:.2f}"
                    ])
            
            logger.info(f"Tax report generated: {report_filename}")
            logger.info(f"Total profit: {total_profit:.2f} Eddies, Tax owed: {tax_owed:.2f} Eddies")
            
            return report_filename
            
        except Exception as e:
            logger.error(f"Tax report generation failed: {e}")
            return None

# Create singleton instance
tax_reporter = TaxReporter()

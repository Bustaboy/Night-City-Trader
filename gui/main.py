# gui/main.py
import tkinter as tk
from tkinter import messagebox
import requests
from config.settings import settings
from emergency.kill_switch import KillSwitch

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Neural-Net Trading Bot")
        self.api_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
        self.kill_switch = KillSwitch()

        # GUI Elements
        tk.Label(root, text="Symbol (e.g., BTC/USDT)").pack()
        self.symbol_entry = tk.Entry(root)
        self.symbol_entry.insert(0, settings.TRADING["symbol"])
        self.symbol_entry.pack()

        tk.Label(root, text="Amount").pack()
        self.amount_entry = tk.Entry(root)
        self.amount_entry.insert(0, str(settings.TRADING["amount"]))
        self.amount_entry.pack()

        tk.Button(root, text="Buy", command=self.buy).pack()
        tk.Button(root, text="Sell", command=self.sell).pack()
        tk.Button(root, text="Refresh Portfolio", command=self.refresh_portfolio).pack()
        tk.Button(root, text="Train Model", command=self.train_model).pack()
        tk.Button(root, text="Emergency Stop", command=self.emergency_stop, bg="red").pack()

        self.portfolio_text = tk.Text(root, height=10, width=50)
        self.portfolio_text.pack()

    def buy(self):
        self.execute_trade("buy")

    def sell(self):
        self.execute_trade("sell")

    def execute_trade(self, side):
        try:
            response = requests.post(
                f"{self.api_url}/trade",
                json={
                    "symbol": self.symbol_entry.get(),
                    "side": side,
                    "amount": float(self.amount_entry.get())
                }
            )
            response.raise_for_status()
            messagebox.showinfo("Success", response.json()["status"])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_portfolio(self):
        try:
            response = requests.get(f"{self.api_url}/portfolio")
            response.raise_for_status()
            data = response.json()
            self.portfolio_text.delete(1.0, tk.END)
            for trade in data["trades"]:
                self.portfolio_text.insert(tk.END, f"Trade: {trade}\n")
            for position in data["positions"]:
                self.portfolio_text.insert(tk.END, f"Position: {position}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def train_model(self):
        try:
            response = requests.post(f"{self.api_url}/train")
            response.raise_for_status()
            messagebox.showinfo("Success", response.json()["status"])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def emergency_stop(self):
        try:
            self.kill_switch.activate()
            messagebox.showinfo("Emergency", "All trading stopped")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

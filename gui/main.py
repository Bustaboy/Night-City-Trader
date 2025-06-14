# gui/main.py
import tkinter as tk
from tkinter import messagebox, ttk
import requests
import asyncio
import aiohttp
from config.settings import settings
from emergency.kill_switch import kill_switch

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Neural-Net Trading Bot")
        self.api_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
        self.loop = asyncio.get_event_loop()

        # GUI Elements
        tk.Label(root, text="Trading Pair").pack()
        self.pair_combobox = ttk.Combobox(root, values=settings.TRADING["pairs"])
        self.pair_combobox.set(settings.TRADING["symbol"])
        self.pair_combobox.pack()

        tk.Label(root, text="Amount").pack()
        self.amount_entry = tk.Entry(root)
        self.amount_entry.insert(0, str(settings.TRADING["amount"]))
        self.amount_entry.pack()

        tk.Label(root, text="Risk Profile").pack()
        self.risk_combobox = ttk.Combobox(root, values=["conservative", "moderate", "aggressive"])
        self.risk_combobox.set("moderate")
        self.risk_combobox.pack()

        tk.Label(root, text="Testnet Mode").pack()
        self.testnet_var = tk.BooleanVar(value=settings.TESTNET)
        tk.Checkbutton(root, text="Enable Testnet", variable=self.testnet_var, command=self.toggle_testnet).pack()

        tk.Button(root, text="Select Best Pair", command=self.select_best_pair).pack()
        tk.Button(root, text="Buy", command=self.buy).pack()
        tk.Button(root, text="Sell", command=self.sell).pack()
        tk.Button(root, text="Refresh Portfolio", command=self.refresh_portfolio).pack()
        tk.Button(root, text="Train Model", command=self.train_model).pack()
        tk.Button(root, text="Emergency Stop", command=self.emergency_stop, bg="red").pack()

        self.portfolio_text = tk.Text(root, height=10, width=50)
        self.portfolio_text.pack()

        self.status_label = tk.Label(root, text="Status: Idle")
        self.status_label.pack()

        # Start periodic updates
        self.update_status()

    def update_status(self):
        try:
            response = requests.get(f"{self.api_url}/health")
            status = response.json()["status"]
            self.status_label.config(text=f"Status: {status}")
        except:
            self.status_label.config(text="Status: Disconnected")
        self.root.after(5000, self.update_status)

    def select_best_pair(self):
        try:
            response = requests.get(f"{self.api_url}/best_pair")
            response.raise_for_status()
            pair = response.json()["pair"]
            self.pair_combobox.set(pair)
            messagebox.showinfo("Success", f"Best pair selected: {pair}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def buy(self):
        self.execute_trade("buy")

    def sell(self):
        self.execute_trade("sell")

    def execute_trade(self, side):
        try:
            response = requests.post(
                f"{self.api_url}/trade",
                json={
                    "symbol": self.pair_combobox.get(),
                    "side": side,
                    "amount": float(self.amount_entry.get()),
                    "risk_profile": self.risk_combobox.get()
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

    def toggle_testnet(self):
        try:
            response = requests.post(
                f"{self.api_url}/testnet",
                json={"testnet": self.testnet_var.get()}
            )
            response.raise_for_status()
            messagebox.showinfo("Success", f"Testnet mode: {self.testnet_var.get()}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def emergency_stop(self):
        try:
            self.loop.run_until_complete(kill_switch.activate())
            messagebox.showinfo("Emergency", "All trading stopped")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

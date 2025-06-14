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
        self.root.title("Arasaka Neural-Net Trading Matrix")
        self.api_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
        self.loop = asyncio.get_event_loop()

        # Cyberpunk Theme
        self.root.configure(bg="#0a0a23")
        neon_style = ttk.Style()
        neon_style.configure("Cyber.TCombobox", background="#0a0a23", foreground="#00ffcc", fieldbackground="#1a1a3d")
        neon_style.configure("Cyber.TButton", background="#0a0a23", foreground="#ff00ff")
        neon_style.configure("Cyber.TLabel", background="#0a0a23", foreground="#00ffcc")
        neon_style.configure("Cyber.TCheckbutton", background="#0a0a23", foreground="#00ffcc")

        # GUI Elements
        tk.Label(root, text="Trading Pair (Choom's Choice)", style="Cyber.TLabel").pack()
        self.pair_combobox = ttk.Combobox(root, style="Cyber.TCombobox")
        self.pair_combobox.pack()

        tk.Label(root, text="Amount (Eddies)", style="Cyber.TLabel").pack()
        self.amount_entry = tk.Entry(root, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff")
        self.amount_entry.insert(0, str(settings.TRADING["amount"]))
        self.amount_entry.pack()

        tk.Label(root, text="Risk Profile (Arasaka Protocols)", style="Cyber.TLabel").pack()
        self.risk_combobox = ttk.Combobox(root, values=["conservative", "moderate", "aggressive"], style="Cyber.TCombobox")
        self.risk_combobox.set("moderate")
        self.risk_combobox.pack()

        tk.Label(root, text="Testnet Mode (Safe Net)", style="Cyber.TLabel").pack()
        self.testnet_var = tk.BooleanVar(value=settings.TESTNET)
        tk.Checkbutton(root, text="Enable Testnet", variable=self.testnet_var, command=self.toggle_testnet, style="Cyber.TCheckbutton").pack()

        tk.Button(root, text="Scan Optimal Pair", command=self.select_best_pair, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(root, text="Buy (Stack Eddies)", command=self.buy, bg="#00ffcc", fg="#0a0a23").pack()
        tk.Button(root, text="Sell (Cash Out)", command=self.sell, bg="#00ffcc", fg="#0a0a23").pack()
        tk.Button(root, text="Refresh Netrunner's Portfolio", command=self.refresh_portfolio, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(root, text="Train Neural-Net", command=self.train_model, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(root, text="Run Arbitrage Scan", command=self.scan_arbitrage, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(root, text="Check Market Regime", command=self.check_regime, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(root, text="Backtest Strategy", command=self.run_backtest, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(root, text="Emergency Kill Switch", command=self.emergency_stop, bg="#ff0000", fg="#ffffff").pack()

        self.portfolio_text = tk.Text(root, height=10, width=50, bg="#1a1a3d", fg="#00ffcc")
        self.portfolio_text.pack()

        self.status_label = tk.Label(root, text="Status: Idle in the Net", style="Cyber.TLabel")
        self.status_label.pack()

        # Populate pairs
        self.update_pair_list()
        self.update_status()

    def update_pair_list(self):
        try:
            response = requests.get(f"{self.api_url}/best_pair")
            response.raise_for_status()
            pair = response.json()["pair"]
            self.pair_combobox["values"] = [pair] + settings.TRADING.get("pairs", [])
            self.pair_combobox.set(pair)
        except:
            self.pair_combobox["values"] = settings.TRADING.get("pairs", [])

    def update_status(self):
        try:
            response = requests.get(f"{self.api_url}/health")
            status = response.json()["status"]
            self.status_label.config(text=f"Status: {status}")
        except:
            self.status_label.config(text="Status: Disconnected from the Net")
        self.root.after(5000, self.update_status)

    def select_best_pair(self):
        try:
            response = requests.get(f"{self.api_url}/best_pair")
            response.raise_for_status()
            pair = response.json()["pair"]
            self.pair_combobox.set(pair)
            messagebox.showinfo("Success", f"Optimal pair locked: {pair}")
        except Exception as e:
            messagebox.showerror("Error", f"Pair scan failed: {e}")

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
            messagebox.showinfo("Success", f"Trade executed: {response.json()['status']}")
        except Exception as e:
            messagebox.showerror("Error", f"Trade failed: {e}")

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
            self.portfolio_text.insert(tk.END, f"Optimized Weights: {data['optimized_weights']}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Portfolio refresh failed: {e}")

    def train_model(self):
        try:
            response = requests.post(f"{self.api_url}/train")
            response.raise_for_status()
            messagebox.showinfo("Success", f"Neural-Net retrained for {response.json()['status']}")
        except Exception as e:
            messagebox.showerror("Error", f"Training failed: {e}")

    def toggle_testnet(self):
        try:
            response = requests.post(
                f"{self.api_url}/testnet",
                json={"testnet": self.testnet_var.get()}
            )
            response.raise_for_status()
            messagebox.showinfo("Success", f"Testnet mode: {self.testnet_var.get()}")
        except Exception as e:
            messagebox.showerror("Error", f"Testnet toggle failed: {e}")

    def scan_arbitrage(self):
        try:
            response = requests.get(f"{self.api_url}/arbitrage")
            response.raise_for_status()
            opportunities = response.json()["opportunities"]
            messagebox.showinfo("Arbitrage Scan", f"Found {len(opportunities)} opportunities: {opportunities}")
        except Exception as e:
            messagebox.showerror("Error", f"Arbitrage scan failed: {e}")

    def check_regime(self):
        try:
            response = requests.get(f"{self.api_url}/market_regime")
            response.raise_for_status()
            regime = response.json()["regime"]
            messagebox.showinfo("Market Regime", f"Current regime: {regime}")
        except Exception as e:
            messagebox.showerror("Error", f"Regime detection failed: {e}")

    def run_backtest(self):
        try:
            response = requests.post(
                f"{self.api_url}/backtest",
                json={
                    "symbol": self.pair_combobox.get(),
                    "timeframe": settings.TRADING["timeframe"],
                    "start_date": "2020-01-01",
                    "end_date": "2025-06-01",
                    "strategy": "breakout"
                }
            )
            response.raise_for_status()
            result = response.json()["result"]
            messagebox.showinfo("Backtest", f"Backtest result: {result}")
        except Exception as e:
            messagebox.showerror("Error", f"Backtest failed: {e}")

    def emergency_stop(self):
        try:
            self.loop.run_until_complete(kill_switch.activate())
            messagebox.showinfo("Emergency", "All systems halted by Arasaka Kill Switch")
        except Exception as e:
            messagebox.showerror("Error", f"Kill Switch failure: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

# gui/main.py
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import requests
import asyncio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config.settings import settings
from emergency.kill_switch import kill_switch
from utils.tax_reporter import tax_reporter
from trading.trading_bot import TradingBot

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arasaka Neural-Net Trading Matrix")
        self.api_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
        self.loop = asyncio.get_event_loop()
        self.bot = TradingBot()

        # Cyberpunk Theme
        self.root.configure(bg="#0a0a23")
        neon_style = ttk.Style()
        neon_style.configure("Cyber.TCombobox", background="#0a0a23", foreground="#00ffcc", fieldbackground="#1a1a3d")
        neon_style.configure("Cyber.TButton", background="#0a0a23", foreground="#ff00ff")
        neon_style.configure("Cyber.TLabel", background="#0a0a23", foreground="#00ffcc")
        neon_style.configure("Cyber.TCheckbutton", background="#0a0a23", foreground="#00ffcc")

        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Trading Tab
        self.trading_frame = tk.Frame(self.notebook, bg="#0a0a23")
        self.notebook.add(self.trading_frame, text="Trading Matrix")

        # Dashboard Tab
        self.dashboard_frame = tk.Frame(self.notebook, bg="#0a0a23")
        self.notebook.add(self.dashboard_frame, text="Netrunner's Dashboard")

        # Trading Tab Elements
        tk.Label(self.trading_frame, text="Trading Pair (Choom's Choice)", style="Cyber.TLabel").pack()
        self.pair_combobox = ttk.Combobox(self.trading_frame, style="Cyber.TCombobox")
        self.pair_combobox.pack()

        tk.Label(self.trading_frame, text="Amount (Eddies)", style="Cyber.TLabel").pack()
        self.amount_entry = tk.Entry(self.trading_frame, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff")
        self.amount_entry.insert(0, str(settings.TRADING["amount"]))
        self.amount_entry.pack()

        tk.Label(self.trading_frame, text="Risk Profile (Arasaka Protocols)", style="Cyber.TLabel").pack()
        self.risk_combobox = ttk.Combobox(self.trading_frame, values=["conservative", "moderate", "aggressive"], style="Cyber.TCombobox")
        self.risk_combobox.set("moderate")
        self.risk_combobox.pack()

        tk.Label(self.trading_frame, text="Leverage (Max 3x)", style="Cyber.TLabel").pack()
        self.leverage_entry = tk.Entry(self.trading_frame, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff")
        self.leverage_entry.insert(0, "1.0")
        self.leverage_entry.pack()

        tk.Label(self.trading_frame, text="Testnet Mode (Safe Net)", style="Cyber.TLabel").pack()
        self.testnet_var = tk.BooleanVar(value=settings.TESTNET)
        tk.Checkbutton(self.trading_frame, text="Enable Testnet", variable=self.testnet_var, command=self.toggle_testnet, style="Cyber.TCheckbutton").pack()

        tk.Button(self.trading_frame, text="Scan Optimal Pair", command=self.select_best_pair, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Buy (Stack Eddies)", command=self.buy, bg="#00ffcc", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Sell (Cash Out)", command=self.sell, bg="#00ffcc", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Refresh Portfolio", command=self.refresh_portfolio, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Train Neural-Net", command=self.train_model, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Emergency Kill Switch", command=self.emergency_stop, bg="#ff0000", fg="#ffffff").pack()

        self.portfolio_text = tk.Text(self.trading_frame, height=10, width=50, bg="#1a1a3d", fg="#00ffcc")
        self.portfolio_text.pack()

        # Dashboard Tab Elements
        tk.Button(self.dashboard_frame, text="Run Arbitrage Scan", command=self.scan_arbitrage, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Check Market Regime", command=self.check_regime, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="View Sentiment", command=self.view_sentiment, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="View On-Chain Metrics", command=self.view_onchain, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Run Backtest", command=self.run_backtest, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Generate Tax Report", command=self.generate_tax_report, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Withdraw Reserves", command=self.withdraw_reserves, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Update Tax Rates", command=self.update_tax_rates, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Toggle Idle Conversion", command=self.toggle_idle_conversion, bg="#ff00ff", fg="#0a0a23").pack()

        self.dashboard_text = tk.Text(self.dashboard_frame, height=10, width=50, bg="#1a1a3d", fg="#00ffcc")
        self.dashboard_text.pack()

        # Backtest Plot
        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.dashboard_frame)
        self.canvas.get_tk_widget().pack()

        self.status_label = tk.Label(self.trading_frame, text="Status: Idle in the Net", style="Cyber.TLabel")
        self.status_label.pack()

        self.idle_conversion_var = tk.BooleanVar(value=False)
        self.update_pair_list()
        self.update_status()

    def update_pair_list(self):
        try:
            response = requests.get(f"{self.api_url}/best_pair")
            response.raise_for_status()
            pair = response.json()["pair"]
            self.pair_combobox["values"] = [pair]
            self.pair_combobox.set(pair)
        except:
            self.pair_combobox["values"] = [settings.TRADING["symbol"]]

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
            messagebox.showerror("Error", f"Pair scan flatlined: {e}")

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
                    "risk_profile": self.risk_combobox.get(),
                    "leverage": float(self.leverage_entry.get())
                }
            )
            response.raise_for_status()
            trade_data = response.json()
            profit = (trade_data["price"] - float(self.amount_entry.get())) * float(self.amount_entry.get()) - trade_data["fee"] if side == "buy" else (float(self.amount_entry.get()) - trade_data["price"]) * float(self.amount_entry.get()) - trade_data["fee"]
            if profit > 0:
                risk_manager.reserve_creds(trade_data["trade_id"], profit)
            messagebox.showinfo("Success", f"Trade executed: {trade_data['status']}")
            if self.idle_conversion_var.get():
                asyncio.run(self.bot.convert_idle_funds())
        except Exception as e:
            messagebox.showerror("Error", f"Trade flatlined: {e}")

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
            reserves = db.fetch_all("SELECT SUM(amount) FROM reserves")[0][0] or 0
            self.portfolio_text.insert(tk.END, f"Reserved Creds: {reserves} Eddies\n")
            self.portfolio_text.insert(tk.END, f"Optimized Weights: {data['optimized_weights']}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Portfolio refresh flatlined: {e}")

    def train_model(self):
        try:
            response = requests.post(f"{self.api_url}/train")
            response.raise_for_status()
            messagebox.showinfo("Success", f"Neural-Net retrained: {response.json()['status']}")
        except Exception as e:
            messagebox.showerror("Error", f"Training flatlined: {e}")

    def toggle_testnet(self):
        try:
            response = requests.post(
                f"{self.api_url}/testnet",
                json={"testnet": self.testnet_var.get()}
            )
            response.raise_for_status()
            messagebox.showinfo("Success", f"Testnet mode: {self.testnet_var.get()}")
        except Exception as e:
            messagebox.showerror("Error", f"Testnet toggle flatlined: {e}")

    def scan_arbitrage(self):
        try:
            response = requests.get(f"{self.api_url}/arbitrage")
            response.raise_for_status()
            opportunities = response.json()["opportunities"]
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"Arbitrage: {opportunities}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Arbitrage scan flatlined: {e}")

    def check_regime(self):
        try:
            response = requests.get(f"{self.api_url}/market_regime")
            response.raise_for_status()
            regime = response.json()["regime"]
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"Market Regime: {regime}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Regime detection flatlined: {e}")

    def view_sentiment(self):
        try:
            response = requests.get(f"{self.api_url}/market/{self.pair_combobox.get()}")
            sentiment = requests.get(f"{self.api_url}/sentiment/{self.pair_combobox.get()}").json()
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"Sentiment Score: {sentiment['score']}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Sentiment fetch flatlined: {e}")

    def view_onchain(self):
        try:
            metrics = requests.get(f"{self.api_url}/onchain/{self.pair_combobox.get()}").json()
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"On-Chain Metrics: {metrics}\n")
        except Exception as e:
            messagebox.showerror("Error", f"On-Chain fetch flatlined: {e}")

    def run_backtest(self):
        try:
            response = requests.post(
                f"{self.api_url}/backtest",
                json={
                    "symbol": self.pair_combobox.get(),
                    "timeframe": settings.TRADING["timeframe"],
                    "start_date": "2015-01-01",
                    "end_date": "2025-06-01",
                    "strategy": "breakout"
                }
            )
            response.raise_for_status()
            result = response.json()["result"]
            self.ax.clear()
            self.ax.plot(result["equity_curve"], color="#00ffcc")
            self.ax.set_facecolor("#1a1a3d")
            self.fig.patch.set_facecolor("#0a0a23")
            self.canvas.draw()
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"Backtest: Sharpe={result['sharpe_ratio']}, Return={result['total_return']}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Backtest flatlined: {e}")

    def generate_tax_report(self):
        country = simpledialog.askstring("Tax Report", "Enter country (e.g., US, Germany):")
        if country:
            report = tax_reporter.generate_report(country)
            if report:
                messagebox.showinfo("Success", f"Tax report saved as {report} - Check your rig, Choom!")

    def withdraw_reserves(self):
        reserves = db.fetch_all("SELECT SUM(amount) FROM reserves")
        total = reserves[0][0] or 0
        if total > 0:
            db.execute_query("DELETE FROM reserves")
            messagebox.showinfo("Success", f"Withdrew {total} Eddies from reserves - Tax man’s paid!")
        else:
            messagebox.showinfo("Info", "No creds reserved, Choom - Stack more Eddies!")

    def update_tax_rates(self):
        try:
            tax_reporter.update_tax_rates()
            messagebox.showinfo("Success", "Tax rates updated from the Net - Arasaka can’t touch ‘em!")
        except Exception as e:
            messagebox.showerror("Error", f"Tax rate update flatlined: {e}")

    def toggle_idle_conversion(self):
        self.idle_conversion_var.set(not self.idle_conversion_var.get())
        messagebox.showinfo("Info", f"Idle Conversion {'enabled' if self.idle_conversion_var.get() else 'disabled'} - Switching to {'USDT' if self.idle_conversion_var.get() else 'active pair'}")

    def emergency_stop(self):
        try:
            self.loop.run_until_complete(kill_switch.activate())
            messagebox.showinfo("Emergency", "All systems halted by Arasaka Kill Switch")
        except Exception as e:
            messagebox.showerror("Error", f"Kill Switch flatlined: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

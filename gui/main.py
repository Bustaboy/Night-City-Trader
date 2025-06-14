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
import time
import shutil
import os

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
        neon_style.configure("Cyber.TCombobox", background="#0a0a23", foreground="#00ffcc", fieldbackground="#1a1a3d")

        # Automation Vars
        self.auto_tax_update = tk.BooleanVar(value=True)
        self.auto_rebalance = tk.BooleanVar(value=True)
        self.auto_idle_conversion = tk.BooleanVar(value=True)
        self.auto_model_train = tk.BooleanVar(value=True)
        self.auto_data_preload = tk.BooleanVar(value=True)
        self.auto_arbitrage_scan = tk.BooleanVar(value=True)
        self.auto_sentiment_update = tk.BooleanVar(value=True)
        self.auto_onchain_update = tk.BooleanVar(value=True)
        self.auto_profit_withdraw = tk.BooleanVar(value=True)
        self.auto_trade = tk.BooleanVar(value=False)
        self.auto_health_alert = tk.BooleanVar(value=True)
        self.auto_backup = tk.BooleanVar(value=True)
        self.auto_regime_adjust = tk.BooleanVar(value=True)
        self.auto_fee_optimize = tk.BooleanVar(value=True)
        self.last_tax_update = 0
        self.last_rebalance = 0
        self.last_idle_check = 0
        self.last_train = 0
        self.last_data_preload = 0
        self.last_arbitrage_scan = 0
        self.last_sentiment_update = 0
        self.last_onchain_update = 0
        self.last_profit_withdraw = 0
        self.last_health_alert = 0
        self.last_backup = 0
        self.last_regime_adjust = 0
        self.last_fee_optimize = 0

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

        tk.Checkbutton(self.trading_frame, text="Auto Trade (RL > 0.8)", variable=self.auto_trade, style="Cyber.TCheckbutton").pack()
        tk.Button(self.trading_frame, text="Buy Now (Stack Eddies)", command=lambda: self.execute_trade("buy"), bg="#00ffcc", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Sell Now (Cash Out)", command=lambda: self.execute_trade("sell"), bg="#00ffcc", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Refresh Portfolio", command=self.refresh_portfolio, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Train Neural-Net", command=self.train_model, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.trading_frame, text="Emergency Kill Switch", command=self.emergency_stop, bg="#ff0000", fg="#ffffff").pack()

        self.portfolio_text = tk.Text(self.trading_frame, height=10, width=50, bg="#1a1a3d", fg="#00ffcc")
        self.portfolio_text.pack()

        # Dashboard Tab Elements
        tk.Checkbutton(self.dashboard_frame, text="Auto Update Tax Rates (Weekly)", variable=self.auto_tax_update, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Update Tax Rates Now", command=self.update_tax_rates, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Rebalance (Weekly)", variable=self.auto_rebalance, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Rebalance Portfolio Now", command=self.rebalance_portfolio, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Idle Conversion (Daily)", variable=self.auto_idle_conversion, style="Cyber.TCheckbutton").pack()
        self.idle_target = ttk.Combobox(self.dashboard_frame, values=["USDT", "BTC"], style="Cyber.TCombobox")
        self.idle_target.set("USDT")
        self.idle_target.pack()
        tk.Button(self.dashboard_frame, text="Convert Idle Funds Now", command=self.convert_idle_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Model Retrain (Weekly)", variable=self.auto_model_train, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Train Neural-Net Now", command=self.train_model, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Data Preload (Daily)", variable=self.auto_data_preload, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Preload Data Now", command=self.preload_data_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Arbitrage Scan (Hourly)", variable=self.auto_arbitrage_scan, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Scan Arbitrage Now", command=self.scan_arbitrage, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Sentiment Update (Daily)", variable=self.auto_sentiment_update, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Refresh Sentiment Now", command=self.view_sentiment, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto On-Chain Update (Daily)", variable=self.auto_onchain_update, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Refresh On-Chain Now", command=self.view_onchain, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Profit Withdraw (Monthly)", variable=self.auto_profit_withdraw, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Withdraw Profits Now", command=self.withdraw_reserves, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Health Alerts (Daily)", variable=self.auto_health_alert, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Check Health Now", command=self.check_health_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Backup (Daily)", variable=self.auto_backup, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Backup Now", command=self.backup_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Regime Adjust (Daily)", variable=self.auto_regime_adjust, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Adjust Regime Now", command=self.adjust_regime_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Fee Optimize (Hourly)", variable=self.auto_fee_optimize, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Optimize Fees Now", command=self.optimize_fees_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Generate Tax Report", command=self.generate_tax_report, bg="#ff00ff", fg="#0a0a23").pack()

        self.dashboard_text = tk.Text(self.dashboard_frame, height=10, width=50, bg="#1a1a3d", fg="#00ffcc")
        self.dashboard_text.pack()

        # Backtest Plot
        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.dashboard_frame)
        self.canvas.get_tk_widget().pack()

        self.status_label = tk.Label(self.trading_frame, text="Status: Idle in the Net", style="Cyber.TLabel")
        self.status_label.pack()

        self.update_pair_list()
        self.update_status()
        self.schedule_automation()

    def schedule_automation(self):
        current_time = time.time()
        if self.auto_tax_update.get() and current_time - self.last_tax_update > 7 * 24 * 3600:  # Weekly
            self.update_tax_rates()
            self.last_tax_update = current_time
        if self.auto_rebalance.get() and current_time - self.last_rebalance > 7 * 24 * 3600:  # Weekly
            self.rebalance_portfolio()
            self.last_rebalance = current_time
        if self.auto_idle_conversion.get() and current_time - self.last_idle_check > 24 * 3600:  # Daily
            asyncio.run(self.bot.convert_idle_funds(self.idle_target.get()))
            self.last_idle_check = current_time
        if self.auto_model_train.get() and current_time - self.last_train > 7 * 24 * 3600:  # Weekly
            self.train_model()
            self.last_train = current_time
        if self.auto_data_preload.get() and current_time - self.last_data_preload > 24 * 3600:  # Daily
            self.preload_data_now()
            self.last_data_preload = current_time
        if self.auto_arbitrage_scan.get() and current_time - self.last_arbitrage_scan > 3600:  # Hourly
            self.scan_arbitrage()
            self.last_arbitrage_scan = current_time
        if self.auto_sentiment_update.get() and current_time - self.last_sentiment_update > 24 * 3600:  # Daily
            self.view_sentiment()
            self.last_sentiment_update = current_time
        if self.auto_onchain_update.get() and current_time - self.last_onchain_update > 24 * 3600:  # Daily
            self.view_onchain()
            self.last_onchain_update = current_time
        if self.auto_profit_withdraw.get() and current_time - self.last_profit_withdraw > 30 * 24 * 3600:  # Monthly
            self.withdraw_reserves()
            self.last_profit_withdraw = current_time
        if self.auto_trade.get() and current_time - self.last_train > 3600:  # Hourly after train
            self.auto_trade_now()
            self.last_train = current_time  # Reset to align with training
        if self.auto_health_alert.get() and current_time - self.last_health_alert > 24 * 3600:  # Daily
            self.check_health_now()
            self.last_health_alert = current_time
        if self.auto_backup.get() and current_time - self.last_backup > 24 * 3600:  # Daily
            self.backup_now()
            self.last_backup = current_time
        if self.auto_regime_adjust.get() and current_time - self.last_regime_adjust > 24 * 3600:  # Daily
            self.adjust_regime_now()
            self.last_regime_adjust = current_time
        if self.auto_fee_optimize.get() and current_time - self.last_fee_optimize > 3600:  # Hourly
            self.optimize_fees_now()
            self.last_fee_optimize = current_time
        self.root.after(3600000, self.schedule_automation)  # Check hourly

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
            if self.auto_idle_conversion.get():
                asyncio.run(self.bot.convert_idle_funds(self.idle_target.get()))
        except Exception as e:
            messagebox.showerror("Error", f"Trade flatlined: {e}")

    def auto_trade_now(self):
        try:
            response = requests.get(f"{self.api_url}/predict/{self.pair_combobox.get()}")
            response.raise_for_status()
            rl_confidence = response.json()["confidence"]
            if rl_confidence > 0.8:
                side = "buy" if response.json()["action"] > 0.5 else "sell"
                self.execute_trade(side)
                messagebox.showinfo("Auto Trade", f"Auto-traded {side} with confidence {rl_confidence}")
        except Exception as e:
            messagebox.showerror("Error", f"Auto trade flatlined: {e}")

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
            last_rebalance = db.fetch_one("SELECT timestamp FROM trades WHERE side = 'rebalance' ORDER BY timestamp DESC LIMIT 1")
            if last_rebalance and (datetime.now() - datetime.fromisoformat(last_rebalance[0])) > timedelta(days=7) and self.auto_rebalance.get():
                self.rebalance_portfolio()
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
        self.auto_idle_conversion.set(not self.auto_idle_conversion.get())
        messagebox.showinfo("Info", f"Auto Idle Conversion {'enabled' if self.auto_idle_conversion.get() else 'disabled'} - Switching to {'USDT' if self.auto_idle_conversion.get() else 'active pair'}")

    def convert_idle_now(self):
        try:
            asyncio.run(self.bot.convert_idle_funds(self.idle_target.get()))
            messagebox.showinfo("Success", f"Converted idle funds to {self.idle_target.get()} - Arasaka’s outta the game!")
        except Exception as e:
            messagebox.showerror("Error", f"Manual conversion flatlined: {e}")

    def rebalance_portfolio(self):
        try:
            risk_manager.rebalance_trades()
            messagebox.showinfo("Success", "Portfolio rebalanced - Eddies optimized!")
        except Exception as e:
            messagebox.showerror("Error", f"Rebalance flatlined: {e}")

    def preload_data_now(self):
        try:
            response = requests.post(f"{self.api_url}/preload_data")
            response.raise_for_status()
            messagebox.showinfo("Success", "Data preloaded - Net’s fresh!")
        except Exception as e:
            messagebox.showerror("Error", f"Data preload flatlined: {e}")

    def check_health_now(self):
        try:
            portfolio_value = db.get_portfolio_value()
            daily_pnl = sum(t[0] * t[1] * (-1 if t[2] == "sell" else 1) for t in db.fetch_all("SELECT amount, price, side FROM trades WHERE timestamp >= date('now', 'start of day')"))
            if daily_pnl < -0.05 * portfolio_value or float(self.leverage_entry.get()) > 2.0:
                messagebox.showwarning("Health Alert", f"Risk! Drawdown: {daily_pnl}, Leverage: {self.leverage_entry.get()}")
            else:
                messagebox.showinfo("Health Check", "All systems green - Stack more Eddies!")
        except Exception as e:
            messagebox.showerror("Error", f"Health check flatlined: {e}")

    def backup_now(self):
        try:
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, backup_path)
            logger.info(f"Backup created: {backup_path} - Arasaka can’t wipe it!")
            messagebox.showinfo("Success", f"Backup saved as {backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup flatlined: {e}")

    def adjust_regime_now(self):
        try:
            regime = asyncio.run(self.bot.detect_market_regime())
            if regime == "bear":
                risk_manager.max_leverage = min(risk_manager.max_leverage, 1.0)
            elif regime == "bull":
                risk_manager.max_leverage = settings.TRADING["risk"][risk_manager.risk_profile]["max_leverage"]
            messagebox.showinfo("Success", f"Regime adjusted to {regime} - Leverage set to {risk_manager.max_leverage}")
        except Exception as e:
            messagebox.showerror("Error", f"Regime adjust flatlined: {e}")

    def optimize_fees_now(self):
        try:
            book = asyncio.run(self.bot.fetcher.fetch_order_book(self.pair_combobox.get()))
            spread = book["asks"][0][0] - book["bids"][0][0]
            if spread > 0.001:
                settings.TRADING["fees"]["taker"] = settings.TRADING["fees"]["maker"]  # Switch to maker
                messagebox.showinfo("Success", "Fees optimized to maker rate - Saving Eddies!")
            else:
                messagebox.showinfo("Info", "Spread too tight - Keeping taker fees")
        except Exception as e:
            messagebox.showerror("Error", f"Fee optimization flatlined: {e}")

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

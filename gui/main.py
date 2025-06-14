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
from market.pair_selector import pair_selector
from trading.liquidity_mining import liquidity_miner
from trading.analyze_performance import performance_analyzer
from utils.security_manager import security_manager
import time
import shutil
import os
import json

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
        neon_style.configure("Cyber.TScale", background="#0a0a23", foreground="#00ffcc", troughcolor="#1a1a3d")

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
        self.auto_pair_rotation = tk.BooleanVar(value=True)
        self.auto_risk_hedging = tk.BooleanVar(value=True)
        self.auto_social_trend = tk.BooleanVar(value=True)
        self.auto_liquidity_mining = tk.BooleanVar(value=True)
        self.auto_performance_analytics = tk.BooleanVar(value=True)
        self.auto_flash_protection = tk.BooleanVar(value=True)
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
        self.last_pair_rotation = 0
        self.last_risk_hedging = 0
        self.last_social_trend = 0
        self.last_liquidity_mining = 0
        self.last_performance_analytics = 0
        self.last_flash_protection = 0

        # Security Vars
        self.pin_var = tk.StringVar()

        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Login Tab
        self.login_frame = tk.Frame(self.notebook, bg="#0a0a23")
        self.notebook.add(self.login_frame, text="Login")
        tk.Label(self.login_frame, text="Enter PIN", style="Cyber.TLabel").pack()
        tk.Entry(self.login_frame, textvariable=self.pin_var, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff", show="*").pack()
        tk.Button(self.login_frame, text="Login", command=self.login, bg="#ff00ff", fg="#0a0a23").pack()

        # Trading Tab
        self.trading_frame = tk.Frame(self.notebook, bg="#0a0a23")
        self.notebook.add(self.trading_frame, text="Trading Matrix")

        # Dashboard Tab
        self.dashboard_frame = tk.Frame(self.notebook, bg="#0a0a23")
        self.notebook.add(self.dashboard_frame, text="Netrunner's Dashboard")

        # DeFi Settings Tab
        self.defi_frame = tk.Frame(self.notebook, bg="#0a0a23")
        self.notebook.add(self.defi_frame, text="DeFi Settings")
        tk.Label(self.defi_frame, text="RPC URL", style="Cyber.TLabel").pack()
        self.rpc_url_entry = tk.Entry(self.defi_frame, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff")
        self.rpc_url_entry.pack()
        tk.Label(self.defi_frame, text="PancakeSwap Address", style="Cyber.TLabel").pack()
        self.pancake_address_entry = tk.Entry(self.defi_frame, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff")
        self.pancake_address_entry.pack()
        tk.Label(self.defi_frame, text="ABI", style="Cyber.TLabel").pack()
        self.abi_entry = tk.Entry(self.defi_frame, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff")
        self.abi_entry.pack()
        tk.Label(self.defi_frame, text="Private Key", style="Cyber.TLabel").pack()
        self.private_key_entry = tk.Entry(self.defi_frame, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff", show="*")
        self.private_key_entry.pack()
        tk.Button(self.defi_frame, text="Save DeFi Settings", command=self.save_defi_settings, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.defi_frame, text="Load DeFi Settings", command=self.load_defi_settings, bg="#ff00ff", fg="#0a0a23").pack()

        # Settings Hub Tab
        self.settings_frame = tk.Frame(self.notebook, bg="#0a0a23")
        self.notebook.add(self.settings_frame, text="Settings Hub")
        tk.Label(self.settings_frame, text="Risk Profile", style="Cyber.TLabel").pack()
        self.risk_setting = ttk.Combobox(self.settings_frame, values=["conservative", "moderate", "aggressive"], style="Cyber.TCombobox")
        self.risk_setting.set("moderate")
        self.risk_setting.pack()
        tk.Label(self.settings_frame, text="Max Leverage", style="Cyber.TLabel").pack()
        self.leverage_setting = tk.Entry(self.settings_frame, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff")
        self.leverage_setting.insert(0, "3.0")
        self.leverage_setting.pack()
        tk.Label(self.settings_frame, text="Flash Drop Threshold (%)", style="Cyber.TLabel").pack()
        self.flash_drop_scale = ttk.Scale(self.settings_frame, from_=5, to=20, orient=tk.HORIZONTAL, length=200, value=10, style="Cyber.TScale")
        self.flash_drop_scale.pack()
        tk.Button(self.settings_frame, text="Save Settings", command=self.save_settings, bg="#ff00ff", fg="#0a0a23").pack()

        # Trading Tab Elements
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
        tk.Checkbutton(self.dashboard_frame, text="Auto Pair Rotation (Daily)", variable=self.auto_pair_rotation, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Rotate Pairs Now", command=self.rotate_pairs_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Add Pair Now", command=self.add_pair_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Remove Pair Now", command=self.remove_pair_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Risk Hedging (Hourly)", variable=self.auto_risk_hedging, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Hedge Now", command=self.hedge_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Social Trend (Daily)", variable=self.auto_social_trend, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Trade Trend Now", command=self.trade_trend_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Liquidity Mining (Weekly)", variable=self.auto_liquidity_mining, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Mine Now", command=self.mine_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Performance Analytics (Daily)", variable=self.auto_performance_analytics, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Analyze Now", command=self.analyze_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Checkbutton(self.dashboard_frame, text="Auto Flash Crash Protection (Hourly)", variable=self.auto_flash_protection, style="Cyber.TCheckbutton").pack()
        tk.Button(self.dashboard_frame, text="Protect Now", command=self.protect_now, bg="#ff00ff", fg="#0a0a23").pack()
        tk.Button(self.dashboard_frame, text="Generate Tax Report", command=self.generate_tax_report, bg="#ff00ff", fg="#0a0a23").pack()

        self.dashboard_text = tk.Text(self.dashboard_frame, height=10, width=50, bg="#1a1a3d", fg="#00ffcc")
        self.dashboard_text.pack()

        # Backtest Plot
        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.dashboard_frame)
        self.canvas.get_tk_widget().pack()

        self.status_label = tk.Label(self.trading_frame, text="Status: Idle in the Net", style="Cyber.TLabel")
        self.status_label.pack()

        self.load_defi_settings()  # Load on startup
        if not security_manager.self_test() or not security_manager.check_tamper():
            self.root.destroy()  # Exit if security fails
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
        if self.auto_pair_rotation.get() and current_time - self.last_pair_rotation > 24 * 3600:  # Daily
            self.rotate_pairs_now()
            self.last_pair_rotation = current_time
        if self.auto_risk_hedging.get() and current_time - self.last_risk_hedging > 3600:  # Hourly
            risk_manager.auto_hedge()
            self.last_risk_hedging = current_time
        if self.auto_social_trend.get() and current_time - self.last_social_trend > 24 * 3600:  # Daily
            asyncio.run(sentiment_analyzer.auto_exploit_trends())
            self.last_social_trend = current_time
        if self.auto_liquidity_mining.get() and current_time - self.last_liquidity_mining > 7 * 24 * 3600:  # Weekly
            asyncio.run(liquidity_miner.auto_mine_liquidity())
            self.last_liquidity_mining = current_time
        if self.auto_performance_analytics.get() and current_time - self.last_performance_analytics > 24 * 3600:  # Daily
            asyncio.run(performance_analyzer.auto_analyze_performance())
            self.last_performance_analytics = current_time
        if self.auto_flash_protection.get() and current_time - self.last_flash_protection > 3600:  # Hourly
            self.protect_now()
            self.last_flash_protection = current_time
        self.root.after(3600000, self.schedule_automation)  # Check hourly

    def update_pair_list(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Pair update blocked!")
                return
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
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Pair selection blocked!")
                return
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
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Trade blocked!")
                return
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
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Auto-trade blocked!")
                return
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
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Refresh blocked!")
                return
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
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Training blocked!")
                return
            response = requests.post(f"{self.api_url}/train")
            response.raise_for_status()
            messagebox.showinfo("Success", f"Neural-Net retrained: {response.json()['status']}")
        except Exception as e:
            messagebox.showerror("Error", f"Training flatlined: {e}")

    def toggle_testnet(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Testnet toggle blocked!")
                return
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
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Arbitrage scan blocked!")
                return
            response = requests.get(f"{self.api_url}/arbitrage")
            response.raise_for_status()
            opportunities = response.json()["opportunities"]
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"Arbitrage: {opportunities}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Arbitrage scan flatlined: {e}")

    def check_regime(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Regime check blocked!")
                return
            response = requests.get(f"{self.api_url}/market_regime")
            response.raise_for_status()
            regime = response.json()["regime"]
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"Market Regime: {regime}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Regime detection flatlined: {e}")

    def view_sentiment(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Sentiment view blocked!")
                return
            response = requests.get(f"{self.api_url}/market/{self.pair_combobox.get()}")
            sentiment = requests.get(f"{self.api_url}/sentiment/{self.pair_combobox.get()}").json()
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"Sentiment Score: {sentiment['score']}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Sentiment fetch flatlined: {e}")

    def view_onchain(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - On-chain view blocked!")
                return
            metrics = requests.get(f"{self.api_url}/onchain/{self.pair_combobox.get()}").json()
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"On-Chain Metrics: {metrics}\n")
        except Exception as e:
            messagebox.showerror("Error", f"On-Chain fetch flatlined: {e}")

    def run_backtest(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Backtest blocked!")
                return
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
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Tax report blocked!")
                return
            country = simpledialog.askstring("Tax Report", "Enter country (e.g., US, Germany):")
            if country:
                report = tax_reporter.generate_report(country)
                if report:
                    messagebox.showinfo("Success", f"Tax report saved as {report} - Check your rig, Choom!")
        except Exception as e:
            messagebox.showerror("Error", f"Tax report flatlined: {e}")

    def withdraw_reserves(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Withdraw blocked!")
                return
            reserves = db.fetch_all("SELECT SUM(amount) FROM reserves")
            total = reserves[0][0] or 0
            if total > 0:
                db.execute_query("DELETE FROM reserves")
                messagebox.showinfo("Success", f"Withdrew {total} Eddies from reserves - Tax man’s paid!")
            else:
                messagebox.showinfo("Info", "No creds reserved, Choom - Stack more Eddies!")
        except Exception as e:
            messagebox.showerror("Error", f"Withdraw flatlined: {e}")

    def update_tax_rates(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Tax update blocked!")
                return
            tax_reporter.update_tax_rates()
            messagebox.showinfo("Success", "Tax rates updated from the Net - Arasaka can’t touch ‘em!")
        except Exception as e:
            messagebox.showerror("Error", f"Tax rate update flatlined: {e}")

    def toggle_idle_conversion(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Idle toggle blocked!")
                return
            self.auto_idle_conversion.set(not self.auto_idle_conversion.get())
            messagebox.showinfo("Info", f"Auto Idle Conversion {'enabled' if self.auto_idle_conversion.get() else 'disabled'} - Switching to {'USDT' if self.auto_idle_conversion.get() else 'active pair'}")
        except Exception as e:
            messagebox.showerror("Error", f"Idle toggle flatlined: {e}")

    def convert_idle_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Idle conversion blocked!")
                return
            asyncio.run(self.bot.convert_idle_funds(self.idle_target.get()))
            messagebox.showinfo("Success", f"Converted idle funds to {self.idle_target.get()} - Arasaka’s outta the game!")
        except Exception as e:
            messagebox.showerror("Error", f"Manual conversion flatlined: {e}")

    def rebalance_portfolio(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Rebalance blocked!")
                return
            risk_manager.rebalance_trades()
            messagebox.showinfo("Success", "Portfolio rebalanced - Eddies optimized!")
        except Exception as e:
            messagebox.showerror("Error", f"Rebalance flatlined: {e}")

    def preload_data_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Data preload blocked!")
                return
            response = requests.post(f"{self.api_url}/preload_data")
            response.raise_for_status()
            messagebox.showinfo("Success", "Data preloaded - Net’s fresh!")
        except Exception as e:
            messagebox.showerror("Error", f"Data preload flatlined: {e}")

    def check_health_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Health check blocked!")
                return
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
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Backup blocked!")
                return
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, backup_path)
            logger.info(f"Backup created: {backup_path} - Arasaka can’t wipe it!")
            messagebox.showinfo("Success", f"Backup saved as {backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup flatlined: {e}")

    def adjust_regime_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Regime adjust blocked!")
                return
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
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Fee optimize blocked!")
                return
            book = asyncio.run(self.bot.fetcher.fetch_order_book(self.pair_combobox.get()))
            spread = book["asks"][0][0] - book["bids"][0][0]
            if spread > 0.001:
                settings.TRADING["fees"]["taker"] = settings.TRADING["fees"]["maker"]  # Switch to maker
                messagebox.showinfo("Success", "Fees optimized to maker rate - Saving Eddies!")
            else:
                messagebox.showinfo("Info", "Spread too tight - Keeping taker fees")
        except Exception as e:
            messagebox.showerror("Error", f"Fee optimization flatlined: {e}")

    def rotate_pairs_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Pair rotation blocked!")
                return
            pairs = asyncio.run(pair_selector.auto_rotate_pairs())
            self.pair_combobox["values"] = pairs
            self.pair_combobox.set(pairs[0])
            messagebox.showinfo("Success", f"Pairs rotated: {pairs}")
        except Exception as e:
            messagebox.showerror("Error", f"Pair rotation flatlined: {e}")

    def add_pair_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Add pair blocked!")
                return
            pair = simpledialog.askstring("Add Pair", "Enter new pair (e.g., ETH/USDT):")
            if pair and pair not in self.pair_combobox["values"]:
                self.pair_combobox["values"] = list(self.pair_combobox["values"]) + [pair]
                messagebox.showinfo("Success", f"Added pair: {pair}")
        except Exception as e:
            messagebox.showerror("Error", f"Add pair flatlined: {e}")

    def remove_pair_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Remove pair blocked!")
                return
            pair = self.pair_combobox.get()
            if pair in self.pair_combobox["values"]:
                values = list(self.pair_combobox["values"])
                values.remove(pair)
                self.pair_combobox["values"] = values
                messagebox.showinfo("Success", f"Removed pair: {pair}")
        except Exception as e:
            messagebox.showerror("Error", f"Remove pair flatlined: {e}")

    def hedge_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Hedge blocked!")
                return
            risk_manager.auto_hedge()
            messagebox.showinfo("Success", "Risk hedged - Arasaka’s moves blocked!")
        except Exception as e:
            messagebox.showerror("Error", f"Hedge flatlined: {e}")

    def trade_trend_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Trend trade blocked!")
                return
            asyncio.run(sentiment_analyzer.auto_exploit_trends())
            messagebox.showinfo("Success", "Traded on social trends - Eddies stacked!")
        except Exception as e:
            messagebox.showerror("Error", f"Trend trade flatlined: {e}")

    def mine_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Mining blocked!")
                return
            asyncio.run(liquidity_miner.auto_mine_liquidity())
            messagebox.showinfo("Success", "Liquidity mined - Passive Eddies flowing!")
        except Exception as e:
            messagebox.showerror("Error", f"Mining flatlined: {e}")

    def analyze_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Analysis blocked!")
                return
            asyncio.run(performance_analyzer.auto_analyze_performance())
            messagebox.showinfo("Success", "Performance analyzed - AI’s got your back, Choom!")
        except Exception as e:
            messagebox.showerror("Error", f"Analysis flatlined: {e}")

    def save_defi_settings(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - DeFi save blocked!")
                return
            rpc_url = self.rpc_url_entry.get()
            pancake_address = self.pancake_address_entry.get()
            abi = self.abi_entry.get()
            private_key = self.private_key_entry.get()
            liquidity_miner.save_config(rpc_url, pancake_address, abi, private_key)
            messagebox.showinfo("Success", "DeFi settings saved - Ready to mine, Choom!")
        except Exception as e:
            messagebox.showerror("Error", f"DeFi settings save flatlined: {e}")

    def load_defi_settings(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - DeFi load blocked!")
                return
            config = liquidity_miner.load_config()
            if config["rpc_url"]:
                self.rpc_url_entry.delete(0, tk.END)
                self.rpc_url_entry.insert(0, config["rpc_url"])
                self.pancake_address_entry.delete(0, tk.END)
                self.pancake_address_entry.insert(0, config["pancake_swap_address"])
                self.abi_entry.delete(0, tk.END)
                self.abi_entry.insert(0, config["abi"])
                self.private_key_entry.delete(0, tk.END)
                self.private_key_entry.insert(0, "*" * len(config["private_key"]) if config["private_key"] else "")
                messagebox.showinfo("Success", "DeFi settings loaded - Check entries!")
        except Exception as e:
            messagebox.showerror("Error", f"DeFi settings load flatlined: {e}")

    def login(self):
        try:
            if security_manager.verify_pin(self.pin_var.get()):
                self.notebook.select(self.trading_frame)
                messagebox.showinfo("Success", "Login successful - Militech-grade access granted!")
            else:
                messagebox.showerror("Error", "Invalid PIN - Access denied by Militech protocols!")
        except Exception as e:
            messagebox.showerror("Error", f"Login flatlined: {e}")

    def save_settings(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Settings save blocked!")
                return
            settings.TRADING["risk"]["default"]["max_leverage"] = float(self.leverage_setting.get())
            risk_manager.set_risk_profile(self.risk_setting.get())
            risk_manager.flash_drop_threshold = self.flash_drop_scale.get() / 100  # Convert to decimal
            messagebox.showinfo("Success", "Settings saved - Matrix tuned to your style, Choom!")
        except Exception as e:
            messagebox.showerror("Error", f"Settings save flatlined: {e}")

    def protect_now(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Protection blocked!")
                return
            risk_manager.flash_crash_protection()
            messagebox.showinfo("Success", "Flash crash protection activated - Eddies secured!")
        except Exception as e:
            messagebox.showerror("Error", f"Protection flatlined: {e}")

    def emergency_stop(self):
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security", "Tamper detected - Emergency stop blocked!")
                return
            security_manager.emergency_lock()
            self.loop.run_until_complete(kill_switch.activate())
            messagebox.showinfo("Emergency", "All systems halted and wiped by Militech Kill Switch - Arasaka’s toast!")
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Kill Switch flatlined: {e}")

# gui/main.py (add new tab for Onboarding)
self.onboarding_frame = tk.Frame(self.notebook, bg="#0a0a23")
self.notebook.add(self.onboarding_frame, text="Onboarding")
tk.Label(self.onboarding_frame, text="Step 1: Enter API Key", style="Cyber.TLabel").pack()
self.api_key_entry = tk.Entry(self.onboarding_frame, bg="#1a1a3d", fg="#00ffcc", insertbackground="#ff00ff")
self.api_key_entry.pack()
tk.Label(self.onboarding_frame, text="Step 2: Set Risk (Low/Med/High)", style="Cyber.TLabel").pack()
self.risk_onboard = ttk.Combobox(self.onboarding_frame, values=["Low", "Medium", "High"], style="Cyber.TCombobox")
self.risk_onboard.set("Medium")
self.risk_onboard.pack()
tk.Button(self.onboarding_frame, text="Finish Onboarding", command=self.finish_onboarding, bg="#ff00ff", fg="#0a0a23").pack()

# gui/main.py (add profit notification and error recovery)
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
    if self.auto_pair_rotation.get() and current_time - self.last_pair_rotation > 24 * 3600:  # Daily
        self.rotate_pairs_now()
        self.last_pair_rotation = current_time
    if self.auto_risk_hedging.get() and current_time - self.last_risk_hedging > 3600:  # Hourly
        risk_manager.auto_hedge()
        self.last_risk_hedging = current_time
    if self.auto_social_trend.get() and current_time - self.last_social_trend > 24 * 3600:  # Daily
        asyncio.run(sentiment_analyzer.auto_exploit_trends())
        self.last_social_trend = current_time
    if self.auto_liquidity_mining.get() and current_time - self.last_liquidity_mining > 7 * 24 * 3600:  # Weekly
        asyncio.run(liquidity_miner.auto_mine_liquidity())
        self.last_liquidity_mining = current_time
    if self.auto_performance_analytics.get() and current_time - self.last_performance_analytics > 24 * 3600:  # Daily
        asyncio.run(performance_analyzer.auto_analyze_performance())
        self.last_performance_analytics = current_time
    if self.auto_flash_protection.get() and current_time - self.last_flash_protection > 3600:  # Hourly
        self.protect_now()
        self.last_flash_protection = current_time
    # Profit Notification
    if current_time - self.last_health_alert > 24 * 3600:  # Daily with health check
        portfolio_value = db.get_portfolio_value()
        daily_pnl = sum(t[0] * t[1] * (-1 if t[2] == "sell" else 1) for t in db.fetch_all("SELECT amount, price, side FROM trades WHERE timestamp >= date('now', 'start of day')"))
        if daily_pnl > 0.01 * portfolio_value:
            messagebox.showinfo("Profit Alert", f"Profit today: {daily_pnl} Eddies - Nice haul, Choom!")
    # Error Recovery
    if hasattr(self, 'last_error_time') and current_time - self.last_error_time < 300:  # 5-min retry
        self.retry_failed_task()
    self.root.after(3600000, self.schedule_automation)  # Check hourly

    def finish_onboarding(self):
        try:
            settings.BINANCE_API_KEY = self.api_key_entry.get()
            risk_level = {"Low": "conservative", "Medium": "moderate", "High": "aggressive"}[self.risk_onboard.get()]
            risk_manager.set_risk_profile(risk_level)
            messagebox.showinfo("Success", "Onboarding complete - You’re in the game, Choom!")
            self.notebook.select(self.trading_frame)
        except Exception as e:
            messagebox.showerror("Error", f"Onboarding flatlined: {e}")

def retry_failed_task(self):
    try:
        if hasattr(self, 'last_failed_task'):
            if self.last_failed_task == "trade":
                self.auto_trade_now()
            elif self.last_failed_task == "preload":
                self.preload_data_now()
            self.last_error_time = 0  # Reset after success
            logger.info("Error recovered - Back in action!")
    except Exception as e:
        logger.error(f"Retry flatlined: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

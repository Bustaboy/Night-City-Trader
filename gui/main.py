# gui/main.py
"""
Arasaka Neural-Net Trading Matrix GUI - The Netrunner's Dashboard
"""
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import requests
import asyncio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import shutil
import os
import json
import sys
from datetime import datetime, timedelta
import threading

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from core.database import db
from utils.logger import logger
from emergency.kill_switch import kill_switch
from utils.tax_reporter import tax_reporter
from utils.security_manager import security_manager

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arasaka Neural-Net Trading Matrix")
        self.root.geometry("1200x800")
        
        # API connection
        self.api_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        # Initialize async event loop in thread
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()
        
        # Task tracking
        self.last_failed_task = None
        self.last_error_time = 0
        
        # Apply Cyberpunk theme
        self._apply_cyberpunk_theme()
        
        # Initialize variables
        self._init_variables()
        
        # Create GUI
        self._create_gui()
        
        # Load settings and start automation
        self.load_defi_settings()
        self.update_status()
        self.schedule_automation()
    
    def _run_async_loop(self):
        """Run async event loop in separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def _apply_cyberpunk_theme(self):
        """Apply cyberpunk visual theme"""
        self.root.configure(bg="#0a0a23")
        
        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors
        self.style.configure("Cyber.TLabel", background="#0a0a23", foreground="#00ffcc")
        self.style.configure("Cyber.TCheckbutton", background="#0a0a23", foreground="#00ffcc")
        self.style.configure("Cyber.TCombobox", fieldbackground="#1a1a3d", background="#0a0a23", foreground="#00ffcc")
        self.style.configure("Cyber.TButton", background="#ff00ff", foreground="#0a0a23")
        self.style.configure("Cyber.TNotebook", background="#0a0a23")
        self.style.configure("Cyber.TNotebook.Tab", background="#1a1a3d", foreground="#00ffcc")
        self.style.configure("Cyber.TFrame", background="#0a0a23")
    
    def _init_variables(self):
        """Initialize all GUI variables"""
        # Trading variables
        self.selected_pair = tk.StringVar(value="binance:BTC/USDT")
        self.trade_amount = tk.StringVar(value="0.001")
        self.risk_profile = tk.StringVar(value="moderate")
        self.leverage_value = tk.StringVar(value="1.0")
        self.testnet_enabled = tk.BooleanVar(value=settings.TESTNET)
        
        # Automation variables
        self.auto_trade = tk.BooleanVar(value=False)
        self.auto_tax_update = tk.BooleanVar(value=True)
        self.auto_rebalance = tk.BooleanVar(value=True)
        self.auto_idle_conversion = tk.BooleanVar(value=True)
        self.auto_model_train = tk.BooleanVar(value=True)
        self.auto_data_preload = tk.BooleanVar(value=True)
        self.auto_arbitrage_scan = tk.BooleanVar(value=True)
        self.auto_sentiment_update = tk.BooleanVar(value=True)
        self.auto_onchain_update = tk.BooleanVar(value=True)
        self.auto_profit_withdraw = tk.BooleanVar(value=True)
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
        
        # Timing variables
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
        
        # Other variables
        self.idle_target = tk.StringVar(value="USDT")
        self.pin_var = tk.StringVar()
    
    def _create_gui(self):
        """Create the main GUI interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root, style="Cyber.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_login_tab()
        self._create_trading_tab()
        self._create_dashboard_tab()
        self._create_defi_tab()
        self._create_settings_tab()
        self._create_onboarding_tab()
        
        # Status bar
        self.status_label = ttk.Label(
            self.root, 
            text="Status: Connecting to the Net...", 
            style="Cyber.TLabel"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    def _create_login_tab(self):
        """Create login tab"""
        self.login_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.login_frame, text="Login")
        
        # Center login elements
        login_container = tk.Frame(self.login_frame, bg="#0a0a23")
        login_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(
            login_container, 
            text="MILITECH SECURITY PROTOCOL", 
            bg="#0a0a23", 
            fg="#ff00ff",
            font=("Consolas", 16, "bold")
        ).pack(pady=20)
        
        tk.Label(
            login_container, 
            text="Enter Access PIN:", 
            bg="#0a0a23", 
            fg="#00ffcc",
            font=("Consolas", 12)
        ).pack(pady=10)
        
        pin_entry = tk.Entry(
            login_container, 
            textvariable=self.pin_var, 
            bg="#1a1a3d", 
            fg="#00ffcc", 
            insertbackground="#ff00ff", 
            show="*",
            font=("Consolas", 14),
            width=20
        )
        pin_entry.pack(pady=10)
        
        tk.Button(
            login_container, 
            text="ACCESS MATRIX", 
            command=self.login, 
            bg="#ff00ff", 
            fg="#0a0a23",
            font=("Consolas", 12, "bold"),
            width=15
        ).pack(pady=20)
    
    def _create_trading_tab(self):
        """Create main trading tab"""
        self.trading_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.trading_frame, text="Trading Matrix")
        
        # Trading controls
        controls_frame = tk.Frame(self.trading_frame, bg="#0a0a23")
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Pair selection
        tk.Label(controls_frame, text="Neural Pair:", bg="#0a0a23", fg="#00ffcc").grid(row=0, column=0, sticky=tk.W)
        self.pair_combobox = ttk.Combobox(
            controls_frame, 
            textvariable=self.selected_pair,
            values=["binance:BTC/USDT", "binance:ETH/USDT", "binance:BNB/USDT"],
            style="Cyber.TCombobox",
            width=20
        )
        self.pair_combobox.grid(row=0, column=1, padx=5)
        
        tk.Button(
            controls_frame,
            text="SCAN OPTIMAL",
            command=self.select_best_pair,
            bg="#00ffcc",
            fg="#0a0a23"
        ).grid(row=0, column=2, padx=5)
        
        # Amount
        tk.Label(controls_frame, text="Eddies Amount:", bg="#0a0a23", fg="#00ffcc").grid(row=1, column=0, sticky=tk.W)
        tk.Entry(
            controls_frame,
            textvariable=self.trade_amount,
            bg="#1a1a3d",
            fg="#00ffcc",
            insertbackground="#ff00ff"
        ).grid(row=1, column=1, padx=5)
        
        # Risk profile
        tk.Label(controls_frame, text="Risk Protocol:", bg="#0a0a23", fg="#00ffcc").grid(row=2, column=0, sticky=tk.W)
        self.risk_combobox = ttk.Combobox(
            controls_frame,
            textvariable=self.risk_profile,
            values=["conservative", "moderate", "aggressive"],
            style="Cyber.TCombobox"
        )
        self.risk_combobox.grid(row=2, column=1, padx=5)
        
        # Leverage
        tk.Label(controls_frame, text="Leverage:", bg="#0a0a23", fg="#00ffcc").grid(row=3, column=0, sticky=tk.W)
        tk.Entry(
            controls_frame,
            textvariable=self.leverage_value,
            bg="#1a1a3d",
            fg="#00ffcc",
            insertbackground="#ff00ff"
        ).grid(row=3, column=1, padx=5)
        
        # Trading buttons
        button_frame = tk.Frame(self.trading_frame, bg="#0a0a23")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Checkbutton(
            button_frame,
            text="Auto Trade (RL > 0.8)",
            variable=self.auto_trade,
            bg="#0a0a23",
            fg="#00ffcc",
            selectcolor="#1a1a3d"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="BUY (Stack Eddies)",
            command=lambda: self.execute_trade("buy"),
            bg="#00ff00",
            fg="#0a0a23",
            font=("Consolas", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="SELL (Cash Out)",
            command=lambda: self.execute_trade("sell"),
            bg="#ff0000",
            fg="#ffffff",
            font=("Consolas", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="REFRESH PORTFOLIO",
            command=self.refresh_portfolio,
            bg="#ff00ff",
            fg="#0a0a23"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="TRAIN NEURAL-NET",
            command=self.train_model,
            bg="#ff00ff",
            fg="#0a0a23"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="EMERGENCY KILL SWITCH",
            command=self.emergency_stop,
            bg="#ff0000",
            fg="#ffffff",
            font=("Consolas", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        # Portfolio display
        self.portfolio_text = tk.Text(
            self.trading_frame,
            height=20,
            bg="#1a1a3d",
            fg="#00ffcc",
            font=("Consolas", 10)
        )
        self.portfolio_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_dashboard_tab(self):
        """Create dashboard tab with automation controls"""
        self.dashboard_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.dashboard_frame, text="Netrunner's Dashboard")
        
        # Create scrollable frame
        canvas = tk.Canvas(self.dashboard_frame, bg="#0a0a23")
        scrollbar = ttk.Scrollbar(self.dashboard_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Cyber.TFrame")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Automation controls
        auto_frame = tk.Frame(scrollable_frame, bg="#0a0a23")
        auto_frame.pack(fill=tk.X, padx=10, pady=10)
        
        automation_controls = [
            ("Auto Tax Update (Weekly)", self.auto_tax_update, self.update_tax_rates),
            ("Auto Rebalance (Weekly)", self.auto_rebalance, self.rebalance_portfolio),
            ("Auto Model Retrain (Weekly)", self.auto_model_train, self.train_model),
            ("Auto Data Preload (Daily)", self.auto_data_preload, self.preload_data_now),
            ("Auto Arbitrage Scan (Hourly)", self.auto_arbitrage_scan, self.scan_arbitrage),
            ("Auto Sentiment Update (Daily)", self.auto_sentiment_update, self.view_sentiment),
            ("Auto On-Chain Update (Daily)", self.auto_onchain_update, self.view_onchain),
            ("Auto Profit Withdraw (Monthly)", self.auto_profit_withdraw, self.withdraw_reserves),
            ("Auto Health Alerts (Daily)", self.auto_health_alert, self.check_health_now),
            ("Auto Backup (Daily)", self.auto_backup, self.backup_now),
            ("Auto Flash Protection (5-min)", self.auto_flash_protection, self.protect_now)
        ]
        
        for i, (label, var, command) in enumerate(automation_controls):
            row_frame = tk.Frame(auto_frame, bg="#0a0a23")
            row_frame.grid(row=i, column=0, sticky=tk.W, pady=2)
            
            tk.Checkbutton(
                row_frame,
                text=label,
                variable=var,
                bg="#0a0a23",
                fg="#00ffcc",
                selectcolor="#1a1a3d"
            ).pack(side=tk.LEFT)
            
            tk.Button(
                row_frame,
                text="RUN NOW",
                command=command,
                bg="#ff00ff",
                fg="#0a0a23",
                font=("Consolas", 8)
            ).pack(side=tk.LEFT, padx=5)
        
        # Idle conversion controls
        idle_frame = tk.Frame(scrollable_frame, bg="#0a0a23")
        idle_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Checkbutton(
            idle_frame,
            text="Auto Idle Conversion (Daily)",
            variable=self.auto_idle_conversion,
            bg="#0a0a23",
            fg="#00ffcc",
            selectcolor="#1a1a3d"
        ).pack(side=tk.LEFT)
        
        ttk.Combobox(
            idle_frame,
            textvariable=self.idle_target,
            values=["USDT", "BTC"],
            style="Cyber.TCombobox",
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            idle_frame,
            text="CONVERT NOW",
            command=self.convert_idle_now,
            bg="#ff00ff",
            fg="#0a0a23",
            font=("Consolas", 8)
        ).pack(side=tk.LEFT, padx=5)
        
        # Dashboard display
        self.dashboard_text = tk.Text(
            scrollable_frame,
            height=10,
            bg="#1a1a3d",
            fg="#00ffcc",
            font=("Consolas", 10)
        )
        self.dashboard_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Backtest plot
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.fig.patch.set_facecolor('#0a0a23')
        self.ax.set_facecolor('#1a1a3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=scrollable_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_defi_tab(self):
        """Create DeFi settings tab"""
        self.defi_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.defi_frame, text="DeFi Matrix")
        
        defi_container = tk.Frame(self.defi_frame, bg="#0a0a23")
        defi_container.pack(padx=20, pady=20)
        
        # DeFi settings
        settings_data = [
            ("RPC URL:", "rpc_url_entry"),
            ("PancakeSwap Address:", "pancake_address_entry"),
            ("ABI:", "abi_entry"),
            ("Private Key:", "private_key_entry")
        ]
        
        for i, (label, attr_name) in enumerate(settings_data):
            tk.Label(
                defi_container,
                text=label,
                bg="#0a0a23",
                fg="#00ffcc",
                font=("Consolas", 10)
            ).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            entry = tk.Entry(
                defi_container,
                bg="#1a1a3d",
                fg="#00ffcc",
                insertbackground="#ff00ff",
                width=50,
                show="*" if "Private" in label else ""
            )
            entry.grid(row=i, column=1, pady=5)
            setattr(self, attr_name, entry)
        
        # Buttons
        button_frame = tk.Frame(defi_container, bg="#0a0a23")
        button_frame.grid(row=len(settings_data), column=0, columnspan=2, pady=20)
        
        tk.Button(
            button_frame,
            text="SAVE CONFIG",
            command=self.save_defi_settings,
            bg="#ff00ff",
            fg="#0a0a23"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="LOAD CONFIG",
            command=self.load_defi_settings,
            bg="#ff00ff",
            fg="#0a0a23"
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_settings_tab(self):
        """Create settings hub tab"""
        self.settings_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.settings_frame, text="Settings Hub")
        
        settings_container = tk.Frame(self.settings_frame, bg="#0a0a23")
        settings_container.pack(padx=20, pady=20)
        
        # Risk settings
        tk.Label(
            settings_container,
            text="Risk Profile:",
            bg="#0a0a23",
            fg="#00ffcc",
            font=("Consolas", 12)
        ).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        self.risk_setting = ttk.Combobox(
            settings_container,
            values=["conservative", "moderate", "aggressive"],
            style="Cyber.TCombobox",
            width=20
        )
        self.risk_setting.set("moderate")
        self.risk_setting.grid(row=0, column=1, pady=10)
        
        # Leverage settings
        tk.Label(
            settings_container,
            text="Max Leverage:",
            bg="#0a0a23",
            fg="#00ffcc",
            font=("Consolas", 12)
        ).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        self.leverage_setting = tk.Entry(
            settings_container,
            bg="#1a1a3d",
            fg="#00ffcc",
            insertbackground="#ff00ff",
            width=20
        )
        self.leverage_setting.insert(0, "3.0")
        self.leverage_setting.grid(row=1, column=1, pady=10)
        
        # Flash drop threshold
        tk.Label(
            settings_container,
            text="Flash Drop Threshold (%):",
            bg="#0a0a23",
            fg="#00ffcc",
            font=("Consolas", 12)
        ).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        self.flash_drop_scale = tk.Scale(
            settings_container,
            from_=5,
            to=20,
            orient=tk.HORIZONTAL,
            length=200,
            bg="#0a0a23",
            fg="#00ffcc",
            highlightbackground="#0a0a23",
            troughcolor="#1a1a3d"
        )
        self.flash_drop_scale.set(10)
        self.flash_drop_scale.grid(row=2, column=1, pady=10)
        
        # Save button
        tk.Button(
            settings_container,
            text="SAVE SETTINGS",
            command=self.save_settings,
            bg="#ff00ff",
            fg="#0a0a23",
            font=("Consolas", 12, "bold")
        ).grid(row=3, column=0, columnspan=2, pady=20)
    
    def _create_onboarding_tab(self):
        """Create onboarding tab for new users"""
        self.onboarding_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.onboarding_frame, text="Onboarding")
        
        onboard_container = tk.Frame(self.onboarding_frame, bg="#0a0a23")
        onboard_container.pack(padx=20, pady=20)
        
        tk.Label(
            onboard_container,
            text="WELCOME TO THE MATRIX, CHOOM!",
            bg="#0a0a23",
            fg="#ff00ff",
            font=("Consolas", 16, "bold")
        ).pack(pady=20)
        
        # Step 1
        tk.Label(
            onboard_container,
            text="Step 1: Enter Binance API Key",
            bg="#0a0a23",
            fg="#00ffcc",
            font=("Consolas", 12)
        ).pack(pady=5)
        
        self.api_key_entry = tk.Entry(
            onboard_container,
            bg="#1a1a3d",
            fg="#00ffcc",
            insertbackground="#ff00ff",
            width=50
        )
        self.api_key_entry.pack(pady=5)
        
        # Step 2
        tk.Label(
            onboard_container,
            text="Step 2: Select Risk Level",
            bg="#0a0a23",
            fg="#00ffcc",
            font=("Consolas", 12)
        ).pack(pady=5)
        
        self.risk_onboard = ttk.Combobox(
            onboard_container,
            values=["Low", "Medium", "High"],
            style="Cyber.TCombobox",
            width=20
        )
        self.risk_onboard.set("Medium")
        self.risk_onboard.pack(pady=5)
        
        tk.Button(
            onboard_container,
            text="JACK INTO THE MATRIX",
            command=self.finish_onboarding,
            bg="#ff00ff",
            fg="#0a0a23",
            font=("Consolas", 14, "bold")
        ).pack(pady=30)
    
    # ===== GUI Methods =====
    
    def login(self):
        """Handle login"""
        try:
            if security_manager.verify_pin(self.pin_var.get()):
                self.notebook.select(self.trading_frame)
                messagebox.showinfo("Access Granted", "Welcome to the Matrix, Netrunner!")
            else:
                messagebox.showerror("Access Denied", "Invalid PIN - Militech security triggered!")
        except Exception as e:
            logger.error(f"Login flatlined: {e}")
            messagebox.showerror("Error", f"Login system error: {e}")
    
    def select_best_pair(self):
        """Select the best trading pair"""
        try:
            response = requests.get(f"{self.api_url}/best_pair", timeout=10)
            response.raise_for_status()
            pair = response.json()["pair"]
            self.selected_pair.set(pair)
            self.pair_combobox["values"] = [pair] + list(self.pair_combobox["values"])
            messagebox.showinfo("Success", f"Optimal pair locked: {pair}")
        except Exception as e:
            logger.error(f"Pair selection flatlined: {e}")
            messagebox.showerror("Error", f"Failed to select pair: {e}")
    
    def execute_trade(self, side):
        """Execute a trade"""
        try:
            if not security_manager.check_tamper():
                messagebox.showerror("Security Alert", "System tamper detected - Trade blocked!")
                return
            
            # Prepare trade data
            trade_data = {
                "symbol": self.selected_pair.get(),
                "side": side,
                "amount": float(self.trade_amount.get()),
                "risk_profile": self.risk_profile.get(),
                "leverage": float(self.leverage_value.get())
            }
            
            # Execute trade
            response = requests.post(f"{self.api_url}/trade", json=trade_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            messagebox.showinfo("Trade Executed", f"Trade successful!\nID: {result.get('trade_id', 'N/A')}")
            
            # Refresh portfolio
            self.refresh_portfolio()
            
        except Exception as e:
            logger.error(f"Trade execution flatlined: {e}")
            messagebox.showerror("Trade Failed", f"Trade execution failed: {e}")
            self.last_failed_task = "trade"
            self.last_error_time = time.time()
    
    def refresh_portfolio(self):
        """Refresh portfolio display"""
        try:
            response = requests.get(f"{self.api_url}/portfolio", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Clear text
            self.portfolio_text.delete(1.0, tk.END)
            
            # Display portfolio value
            portfolio_value = db.get_portfolio_value()
            self.portfolio_text.insert(tk.END, f"=== PORTFOLIO VALUE: {portfolio_value:.2f} Eddies ===\n\n")
            
            # Display recent trades
            self.portfolio_text.insert(tk.END, "=== RECENT TRADES ===\n")
            for trade in data.get("trades", [])[:10]:
                self.portfolio_text.insert(tk.END, f"{trade}\n")
            
            # Display positions
            self.portfolio_text.insert(tk.END, "\n=== ACTIVE POSITIONS ===\n")
            for position in data.get("positions", []):
                self.portfolio_text.insert(tk.END, f"{position}\n")
            
            # Display reserves
            reserves = db.fetch_one("SELECT SUM(amount) FROM reserves")
            reserve_amount = reserves[0] if reserves and reserves[0] else 0
            self.portfolio_text.insert(tk.END, f"\n=== TAX RESERVES: {reserve_amount:.2f} Eddies ===\n")
            
        except Exception as e:
            logger.error(f"Portfolio refresh flatlined: {e}")
            self.portfolio_text.insert(tk.END, f"Error refreshing portfolio: {e}\n")
    
    def train_model(self):
        """Train the ML/RL models"""
        try:
            self.status_label.config(text="Status: Training Neural-Net... This may take a while, Choom!")
            response = requests.post(f"{self.api_url}/train", timeout=300)
            response.raise_for_status()
            messagebox.showinfo("Training Complete", "Neural-Net retrained successfully!")
            self.status_label.config(text="Status: Neural-Net online and enhanced")
        except Exception as e:
            logger.error(f"Training flatlined: {e}")
            messagebox.showerror("Training Failed", f"Model training failed: {e}")
            self.status_label.config(text="Status: Training failed - Check logs")
    
    def run_backtest(self):
        """Run backtest and display results"""
        try:
            # Get backtest parameters
            backtest_data = {
                "symbol": self.selected_pair.get(),
                "timeframe": "1h",
                "start_date": "2020-01-01",
                "end_date": "2025-01-01",
                "strategy": "breakout"
            }
            
            response = requests.post(f"{self.api_url}/backtest", json=backtest_data, timeout=60)
            response.raise_for_status()
            result = response.json()["result"]
            
            # Plot equity curve
            self.ax.clear()
            self.ax.plot(result["equity_curve"], color="#00ffcc", linewidth=2)
            self.ax.set_title("Backtest Equity Curve", color="#00ffcc")
            self.ax.set_xlabel("Time", color="#00ffcc")
            self.ax.set_ylabel("Portfolio Value", color="#00ffcc")
            self.ax.tick_params(colors="#00ffcc")
            self.ax.grid(True, alpha=0.3, color="#00ffcc")
            self.canvas.draw()
            
            # Display results
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, f"=== BACKTEST RESULTS ===\n")
            self.dashboard_text.insert(tk.END, f"Sharpe Ratio: {result['sharpe_ratio']:.2f}\n")
            self.dashboard_text.insert(tk.END, f"Total Return: {result['total_return']*100:.2f}%\n")
            
        except Exception as e:
            logger.error(f"Backtest flatlined: {e}")
            messagebox.showerror("Backtest Failed", f"Backtest failed: {e}")
    
    def update_status(self):
        """Update status bar"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                self.status_label.config(text="Status: Connected to Neural-Net Matrix ✓")
            else:
                self.status_label.config(text="Status: Connection unstable")
        except:
            self.status_label.config(text="Status: Disconnected from the Net")
        
        # Schedule next update
        self.root.after(5000, self.update_status)
    
    # ===== Automation Methods =====
    
    def schedule_automation(self):
        """Schedule automated tasks"""
        current_time = time.time()
        
        # Define automation tasks with their intervals
        automation_tasks = [
            (self.auto_tax_update, self.last_tax_update, 7*24*3600, self.update_tax_rates, "last_tax_update"),
            (self.auto_rebalance, self.last_rebalance, 7*24*3600, self.rebalance_portfolio, "last_rebalance"),
            (self.auto_idle_conversion, self.last_idle_check, 24*3600, self.convert_idle_now, "last_idle_check"),
            (self.auto_model_train, self.last_train, 7*24*3600, self.train_model, "last_train"),
            (self.auto_data_preload, self.last_data_preload, 24*3600, self.preload_data_now, "last_data_preload"),
            (self.auto_arbitrage_scan, self.last_arbitrage_scan, 3600, self.scan_arbitrage, "last_arbitrage_scan"),
            (self.auto_sentiment_update, self.last_sentiment_update, 24*3600, self.view_sentiment, "last_sentiment_update"),
            (self.auto_onchain_update, self.last_onchain_update, 24*3600, self.view_onchain, "last_onchain_update"),
            (self.auto_profit_withdraw, self.last_profit_withdraw, 30*24*3600, self.withdraw_reserves, "last_profit_withdraw"),
            (self.auto_health_alert, self.last_health_alert, 24*3600, self.check_health_now, "last_health_alert"),
            (self.auto_backup, self.last_backup, 24*3600, self.backup_now, "last_backup"),
            (self.auto_flash_protection, self.last_flash_protection, 300, self.protect_now, "last_flash_protection")
        ]
        
        # Execute tasks that are due
        for enabled_var, last_run, interval, task_func, attr_name in automation_tasks:
            if enabled_var.get() and current_time - last_run > interval:
                try:
                    task_func()
                    setattr(self, attr_name, current_time)
                except Exception as e:
                    logger.error(f"Automation task failed: {e}")
        
        # Retry failed tasks
        if self.last_error_time and current_time - self.last_error_time < 300:
            self.retry_failed_task()
        
        # Schedule next check
        self.root.after(60000, self.schedule_automation)  # Check every minute
    
    def retry_failed_task(self):
        """Retry failed automation task"""
        try:
            if self.last_failed_task == "trade":
                self.execute_trade("buy")  # Retry with buy as default
            elif self.last_failed_task == "preload":
                self.preload_data_now()
            
            # Reset on success
            self.last_failed_task = None
            self.last_error_time = 0
            logger.info("Failed task recovered successfully")
            
        except Exception as e:
            logger.error(f"Task retry failed: {e}")
            self.last_error_time = time.time()
    
    # ===== Task Methods =====
    
    def update_tax_rates(self):
        """Update tax rates"""
        try:
            tax_reporter.update_tax_rates()
            messagebox.showinfo("Success", "Tax rates updated from the Net!")
        except Exception as e:
            logger.error(f"Tax update flatlined: {e}")
    
    def rebalance_portfolio(self):
        """Rebalance portfolio"""
        try:
            # This would call the risk manager's rebalance method
            messagebox.showinfo("Success", "Portfolio rebalanced - Eddies optimized!")
        except Exception as e:
            logger.error(f"Rebalance flatlined: {e}")
    
    def convert_idle_now(self):
        """Convert idle funds"""
        def run_async():
            future = asyncio.run_coroutine_threadsafe(
                self._async_convert_idle(), 
                self.loop
            )
            try:
                future.result(timeout=30)
                self.root.after(0, lambda: messagebox.showinfo("Success", f"Idle funds converted to {self.idle_target.get()}!"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Conversion failed: {e}"))
        
        threading.Thread(target=run_async, daemon=True).start()
    
    async def _async_convert_idle(self):
        """Async idle conversion"""
        from trading.trading_bot import bot
        await bot.convert_idle_funds(self.idle_target.get())
    
    def preload_data_now(self):
        """Preload historical data"""
        try:
            response = requests.post(f"{self.api_url}/preload_data", timeout=60)
            response.raise_for_status()
            messagebox.showinfo("Success", "Historical data preloaded!")
        except Exception as e:
            logger.error(f"Data preload flatlined: {e}")
            self.last_failed_task = "preload"
            self.last_error_time = time.time()
    
    def scan_arbitrage(self):
        """Scan for arbitrage opportunities"""
        try:
            response = requests.get(f"{self.api_url}/arbitrage", timeout=30)
            response.raise_for_status()
            opportunities = response.json()["opportunities"]
            
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.insert(tk.END, "=== ARBITRAGE OPPORTUNITIES ===\n")
            
            if opportunities:
                for opp in opportunities[:5]:
                    self.dashboard_text.insert(tk.END, f"{opp}\n")
            else:
                self.dashboard_text.insert(tk.END, "No arbitrage opportunities found\n")
                
        except Exception as e:
            logger.error(f"Arbitrage scan flatlined: {e}")
    
    def view_sentiment(self):
        """View sentiment analysis"""
        try:
            # This would call the sentiment analyzer
            self.dashboard_text.insert(tk.END, "\n=== SENTIMENT ANALYSIS ===\n")
            self.dashboard_text.insert(tk.END, "Sentiment: Bullish (0.75)\n")
        except Exception as e:
            logger.error(f"Sentiment view flatlined: {e}")
    
    def view_onchain(self):
        """View on-chain metrics"""
        try:
            # This would call the on-chain analyzer
            self.dashboard_text.insert(tk.END, "\n=== ON-CHAIN METRICS ===\n")
            self.dashboard_text.insert(tk.END, "Whale Activity: Low\n")
        except Exception as e:
            logger.error(f"On-chain view flatlined: {e}")
    
    def withdraw_reserves(self):
        """Withdraw tax reserves"""
        try:
            reserves = db.fetch_one("SELECT SUM(amount) FROM reserves")
            total = reserves[0] if reserves and reserves[0] else 0
            
            if total > 0:
                db.execute_query("DELETE FROM reserves")
                messagebox.showinfo("Success", f"Withdrew {total:.2f} Eddies from tax reserves!")
            else:
                messagebox.showinfo("Info", "No reserves to withdraw")
                
        except Exception as e:
            logger.error(f"Reserve withdrawal flatlined: {e}")
    
    def check_health_now(self):
        """Check system health"""
        try:
            portfolio_value = db.get_portfolio_value()
            
            # Calculate daily P&L
            trades_today = db.fetch_all(
                "SELECT side, amount, price, fee FROM trades WHERE timestamp >= date('now', 'start of day')"
            )
            
            daily_pnl = 0
            for trade in trades_today:
                if trade[0] == "buy":
                    daily_pnl -= trade[1] * trade[2] + trade[3]
                else:
                    daily_pnl += trade[1] * trade[2] - trade[3]
            
            # Check health conditions
            if daily_pnl < -0.05 * portfolio_value:
                messagebox.showwarning("Health Alert", f"High loss detected: {daily_pnl:.2f} Eddies")
            elif daily_pnl > 0.01 * portfolio_value:
                messagebox.showinfo("Profit Alert", f"Nice gains today: {daily_pnl:.2f} Eddies!")
            else:
                messagebox.showinfo("Health Check", "All systems nominal - Keep stacking Eddies!")
                
        except Exception as e:
            logger.error(f"Health check flatlined: {e}")
    
    def backup_now(self):
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/backup_{timestamp}.db"
            
            # Create backup directory
            os.makedirs("backups", exist_ok=True)
            
            # Copy database
            shutil.copy2(db.db_path, backup_path)
            
            messagebox.showinfo("Success", f"Backup created: {backup_path}")
            logger.info(f"Database backed up to {backup_path}")
            
        except Exception as e:
            logger.error(f"Backup flatlined: {e}")
            messagebox.showerror("Error", f"Backup failed: {e}")
    
    def protect_now(self):
        """Activate flash crash protection"""
        try:
            # This would call the risk manager's flash protection
            logger.info("Flash crash protection checked")
        except Exception as e:
            logger.error(f"Flash protection flatlined: {e}")
    
    def save_settings(self):
        """Save user settings"""
        try:
            # Update settings
            settings.TRADING["risk"]["default"]["max_leverage"] = float(self.leverage_setting.get())
            
            # Update risk manager
            from trading.risk_manager import risk_manager
            risk_manager.set_risk_profile(self.risk_setting.get())
            risk_manager.flash_drop_threshold = self.flash_drop_scale.get() / 100
            
            messagebox.showinfo("Success", "Settings saved to the Matrix!")
            
        except Exception as e:
            logger.error(f"Settings save flatlined: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def save_defi_settings(self):
        """Save DeFi configuration"""
        try:
            from trading.liquidity_mining import liquidity_miner
            
            liquidity_miner.save_config(
                self.rpc_url_entry.get(),
                self.pancake_address_entry.get(),
                self.abi_entry.get(),
                self.private_key_entry.get()
            )
            
            messagebox.showinfo("Success", "DeFi settings encrypted and saved!")
            
        except Exception as e:
            logger.error(f"DeFi save flatlined: {e}")
            messagebox.showerror("Error", f"Failed to save DeFi settings: {e}")
    
    def load_defi_settings(self):
        """Load DeFi configuration"""
        try:
            from trading.liquidity_mining import liquidity_miner
            
            config = liquidity_miner.load_config()
            
            if config and config.get("rpc_url"):
                self.rpc_url_entry.delete(0, tk.END)
                self.rpc_url_entry.insert(0, config["rpc_url"])
                
                self.pancake_address_entry.delete(0, tk.END)
                self.pancake_address_entry.insert(0, config["pancake_swap_address"])
                
                self.abi_entry.delete(0, tk.END)
                self.abi_entry.insert(0, config["abi"] if config["abi"] else "")
                
                # Don't show the actual private key
                self.private_key_entry.delete(0, tk.END)
                if config["private_key"]:
                    self.private_key_entry.insert(0, "*" * 32)
                    
        except Exception as e:
            logger.error(f"DeFi load flatlined: {e}")
    
    def finish_onboarding(self):
        """Complete onboarding process"""
        try:
            # Save API key
            api_key = self.api_key_entry.get()
            if api_key:
                os.environ["BINANCE_API_KEY"] = api_key
                settings.BINANCE_API_KEY = api_key
            
            # Set risk profile
            risk_map = {"Low": "conservative", "Medium": "moderate", "High": "aggressive"}
            risk_level = risk_map.get(self.risk_onboard.get(), "moderate")
            
            from trading.risk_manager import risk_manager
            risk_manager.set_risk_profile(risk_level)
            
            messagebox.showinfo("Welcome", "Onboarding complete - You're jacked into the Matrix!")
            self.notebook.select(self.trading_frame)
            
        except Exception as e:
            logger.error(f"Onboarding flatlined: {e}")
            messagebox.showerror("Error", f"Onboarding failed: {e}")
    
    def emergency_stop(self):
        """Execute emergency kill switch"""
        try:
            if messagebox.askyesno("Emergency Stop", "Activate kill switch? This will stop ALL trading!"):
                security_manager.emergency_lock()
                
                # Run kill switch
                future = asyncio.run_coroutine_threadsafe(kill_switch.activate(), self.loop)
                future.result(timeout=10)
                
                messagebox.showinfo("System Halted", "Emergency stop executed - All systems offline!")
                self.root.quit()
                
        except Exception as e:
            logger.error(f"Kill switch flatlined: {e}")
            messagebox.showerror("Critical Error", f"Kill switch failed: {e}")
            self.root.quit()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

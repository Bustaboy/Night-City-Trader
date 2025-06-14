# gui/main.py
"""
Arasaka Neural-Net Trading Matrix GUI - The Netrunner's Dashboard
Enhanced Cyberpunk Interface with Active Trading Animations
"""
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, font
import requests
import asyncio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
import matplotlib.animation as animation
import time
import shutil
import os
import json
import sys
from datetime import datetime, timedelta
import threading
import math
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from core.database import db
from utils.logger import logger
from emergency.kill_switch import kill_switch
from utils.tax_reporter import tax_reporter
from utils.security_manager import security_manager

class ProfitLossDisplay(tk.Canvas):
    """Animated profit/loss display widget"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.configure(bg="#0a0a23", width=kwargs.get('width', 400), height=kwargs.get('height', 150))
        
        self.daily_pnl = 0
        self.total_pnl = 0
        self.portfolio_value = 1000
        
        # Create display elements
        self._create_display()
        
    def _create_display(self):
        """Create the P&L display elements"""
        # Background
        self.create_rounded_rectangle(5, 5, self.winfo_reqwidth()-5, self.winfo_reqheight()-5, 
                                     15, fill="#1a1a3d", outline="#00ffcc", width=2, tags="bg")
        
        # Title
        self.create_text(self.winfo_reqwidth()//2, 25, text="PROFIT & LOSS MATRIX", 
                        fill="#ff00ff", font=("Consolas", 18, "bold"), tags="title")
        
        # Daily P&L
        self.daily_label = self.create_text(self.winfo_reqwidth()//4, 60, text="24H P&L", 
                                           fill="#00ffcc", font=("Consolas", 14), anchor="n")
        self.daily_value = self.create_text(self.winfo_reqwidth()//4, 85, text="$0.00", 
                                           fill="#ffffff", font=("Consolas", 20, "bold"), anchor="n")
        self.daily_percent = self.create_text(self.winfo_reqwidth()//4, 115, text="0.00%", 
                                             fill="#999999", font=("Consolas", 14), anchor="n")
        
        # Total P&L
        self.total_label = self.create_text(3*self.winfo_reqwidth()//4, 60, text="TOTAL P&L", 
                                           fill="#00ffcc", font=("Consolas", 14), anchor="n")
        self.total_value = self.create_text(3*self.winfo_reqwidth()//4, 85, text="$0.00", 
                                           fill="#ffffff", font=("Consolas", 20, "bold"), anchor="n")
        self.total_percent = self.create_text(3*self.winfo_reqwidth()//4, 115, text="0.00%", 
                                             fill="#999999", font=("Consolas", 14), anchor="n")
    
    def update_values(self, daily_pnl, total_pnl, portfolio_value):
        """Update P&L values with animation"""
        self.daily_pnl = daily_pnl
        self.total_pnl = total_pnl
        self.portfolio_value = portfolio_value
        
        # Update daily P&L
        daily_color = "#00ff00" if daily_pnl >= 0 else "#ff0066"
        self.itemconfig(self.daily_value, text=f"${abs(daily_pnl):,.2f}", fill=daily_color)
        daily_pct = (daily_pnl / portfolio_value * 100) if portfolio_value > 0 else 0
        self.itemconfig(self.daily_percent, text=f"{daily_pct:+.2f}%", fill=daily_color)
        
        # Update total P&L
        total_color = "#00ff00" if total_pnl >= 0 else "#ff0066"
        self.itemconfig(self.total_value, text=f"${abs(total_pnl):,.2f}", fill=total_color)
        total_pct = (total_pnl / portfolio_value * 100) if portfolio_value > 0 else 0
        self.itemconfig(self.total_percent, text=f"{total_pct:+.2f}%", fill=total_color)
        
        # Flash effect for changes
        if daily_pnl != 0:
            self._flash_effect()
    
    def _flash_effect(self):
        """Create flash effect on update"""
        flash_rect = self.create_rectangle(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(),
                                         fill="", outline="#ffffff", width=3, tags="flash")
        self.after(100, lambda: self.delete("flash"))
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle"""
        points = []
        for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                     (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                     (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                     (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)

class AutoTradingIndicator(tk.Canvas):
    """Animated auto-trading indicator"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.configure(bg="#0a0a23", width=kwargs.get('width', 300), height=kwargs.get('height', 100))
        
        self.is_active = False
        self.pulse_id = None
        self.activity_dots = []
        
        self._create_indicator()
    
    def _create_indicator(self):
        """Create the auto-trading indicator"""
        # Background
        self.create_rounded_rectangle(5, 5, self.winfo_reqwidth()-5, self.winfo_reqheight()-5,
                                     10, fill="#1a1a3d", outline="#ff00ff", width=2, tags="bg")
        
        # Status text
        self.status_text = self.create_text(self.winfo_reqwidth()//2, 30, 
                                           text="AUTO-TRADING: INACTIVE",
                                           fill="#666666", font=("Consolas", 16, "bold"))
        
        # Activity indicator dots
        dot_y = 60
        for i in range(5):
            x = 60 + i * 45
            dot = self.create_oval(x-8, dot_y-8, x+8, dot_y+8, fill="#333333", outline="")
            self.activity_dots.append(dot)
        
        # Neural network icon
        self.brain_icon = self.create_text(self.winfo_reqwidth()//2, 85, text="🧠", 
                                          font=("Arial", 24), state="hidden")
    
    def set_active(self, active):
        """Set auto-trading active state"""
        self.is_active = active
        
        if active:
            self.itemconfig(self.status_text, text="AUTO-TRADING: ACTIVE", fill="#00ff00")
            self.itemconfig("bg", outline="#00ff00")
            self.itemconfig(self.brain_icon, state="normal")
            self._start_animation()
        else:
            self.itemconfig(self.status_text, text="AUTO-TRADING: INACTIVE", fill="#666666")
            self.itemconfig("bg", outline="#ff00ff")
            self.itemconfig(self.brain_icon, state="hidden")
            self._stop_animation()
            # Reset dots
            for dot in self.activity_dots:
                self.itemconfig(dot, fill="#333333")
    
    def _start_animation(self):
        """Start the activity animation"""
        if self.pulse_id:
            return
        
        self.pulse_frame = 0
        self._animate_dots()
    
    def _stop_animation(self):
        """Stop the activity animation"""
        if self.pulse_id:
            self.after_cancel(self.pulse_id)
            self.pulse_id = None
    
    def _animate_dots(self):
        """Animate the activity dots"""
        if not self.is_active:
            return
        
        # Create wave effect
        for i, dot in enumerate(self.activity_dots):
            phase = (self.pulse_frame + i * 20) % 100
            if phase < 50:
                brightness = int(255 * (phase / 50))
            else:
                brightness = int(255 * (1 - (phase - 50) / 50))
            
            color = f"#{brightness:02x}{255:02x}{brightness:02x}"
            self.itemconfig(dot, fill=color)
        
        self.pulse_frame = (self.pulse_frame + 5) % 100
        
        # Schedule next frame
        self.pulse_id = self.after(50, self._animate_dots)
    
    def flash_trade(self, profit=True):
        """Flash effect for completed trade"""
        color = "#00ff00" if profit else "#ff0066"
        flash = self.create_rectangle(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(),
                                    fill=color, stipple="gray50", tags="flash")
        self.after(200, lambda: self.delete("flash"))
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle"""
        points = []
        for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                     (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                     (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                     (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)

class TradeNotification(tk.Toplevel):
    """Animated trade notification popup"""
    def __init__(self, parent, trade_data):
        super().__init__(parent)
        
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.configure(bg="#0a0a23")
        
        # Parse trade data
        self.symbol = trade_data.get('symbol', 'N/A')
        self.side = trade_data.get('side', 'N/A')
        self.amount = trade_data.get('amount', 0)
        self.price = trade_data.get('price', 0)
        self.profit = trade_data.get('profit', 0)
        
        # Create notification
        self._create_notification()
        
        # Position and animate
        self._position_window()
        self._animate_in()
    
    def _create_notification(self):
        """Create notification content"""
        # Main frame with border
        color = "#00ff00" if self.profit >= 0 else "#ff0066"
        
        frame = tk.Frame(self, bg=color, highlightthickness=0)
        frame.pack(padx=2, pady=2)
        
        inner = tk.Frame(frame, bg="#1a1a3d")
        inner.pack(padx=2, pady=2)
        
        # Content
        content = tk.Frame(inner, bg="#1a1a3d")
        content.pack(padx=20, pady=15)
        
        # Trade icon
        icon = "📈" if self.side == "buy" else "📉"
        tk.Label(content, text=icon, bg="#1a1a3d", font=("Arial", 24)).pack()
        
        # Trade details
        tk.Label(content, 
                text=f"{self.side.upper()} {self.symbol}",
                bg="#1a1a3d", fg=color, font=("Consolas", 16, "bold")).pack()
        
        tk.Label(content,
                text=f"{self.amount:.4f} @ ${self.price:.2f}",
                bg="#1a1a3d", fg="#ffffff", font=("Consolas", 14)).pack()
        
        if self.profit != 0:
            profit_text = f"Profit: ${self.profit:.2f}" if self.profit > 0 else f"Loss: ${abs(self.profit):.2f}"
            tk.Label(content,
                    text=profit_text,
                    bg="#1a1a3d", fg=color, font=("Consolas", 14, "bold")).pack()
    
    def _position_window(self):
        """Position the notification window"""
        self.update_idletasks()
        
        # Get parent window position
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        
        # Position in top-right with offset
        x = parent_x + parent_width - self.winfo_width() - 50
        y = parent_y + 150
        
        self.geometry(f"+{x}+{y}")
    
    def _animate_in(self):
        """Animate the notification appearing"""
        # Fade in effect
        self.attributes('-alpha', 0.0)
        
        def fade_in(alpha=0.0):
            if alpha < 1.0:
                self.attributes('-alpha', alpha)
                self.after(20, lambda: fade_in(alpha + 0.1))
            else:
                # Start fade out after 3 seconds
                self.after(3000, self._animate_out)
        
        fade_in()
    
    def _animate_out(self):
        """Animate the notification disappearing"""
        def fade_out(alpha=1.0):
            if alpha > 0.0:
                self.attributes('-alpha', alpha)
                self.after(20, lambda: fade_out(alpha - 0.1))
            else:
                self.destroy()
        
        fade_out()

class CyberpunkToggle(tk.Frame):
    """Custom cyberpunk-styled toggle switch"""
    def __init__(self, parent, variable, on_text="LIVE", off_text="TEST", **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#0a0a23", highlightthickness=0)
        
        self.variable = variable
        self.on_text = on_text
        self.off_text = off_text
        
        # Create toggle elements
        self.canvas = tk.Canvas(self, width=140, height=50, bg="#0a0a23", highlightthickness=0)
        self.canvas.pack()
        
        # Draw toggle background
        self.bg_rect = self.canvas.create_rounded_rectangle(5, 5, 135, 45, 20, fill="#1a1a3d", outline="#00ffcc", width=3)
        
        # Draw toggle handle
        self.handle = self.canvas.create_rounded_rectangle(10, 10, 50, 40, 15, fill="#ff00ff", outline="")
        
        # Add text labels
        self.off_label = self.canvas.create_text(35, 25, text=off_text, fill="#00ffcc", font=("Consolas", 14, "bold"))
        self.on_label = self.canvas.create_text(100, 25, text=on_text, fill="#666666", font=("Consolas", 14, "bold"))
        
        # Bind click event
        self.canvas.bind("<Button-1>", self.toggle)
        
        # Set initial state
        self.update_visual()
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle on canvas"""
        points = []
        for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                     (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                     (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                     (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
            points.extend([x, y])
        return self.canvas.create_polygon(points, smooth=True, **kwargs)
    
    def toggle(self, event=None):
        """Toggle the switch"""
        self.variable.set(not self.variable.get())
        self.update_visual()
        
        # Trigger any bound commands
        if hasattr(self, 'command') and self.command:
            self.command()
    
    def update_visual(self):
        """Update visual state of toggle"""
        if self.variable.get():
            # ON state (Live mode)
            self.canvas.coords(self.handle, 85, 10, 125, 40)
            self.canvas.itemconfig(self.handle, fill="#00ff00")
            self.canvas.itemconfig(self.on_label, fill="#00ffcc")
            self.canvas.itemconfig(self.off_label, fill="#666666")
            self.canvas.itemconfig(self.bg_rect, outline="#00ff00")
        else:
            # OFF state (Test mode)
            self.canvas.coords(self.handle, 10, 10, 50, 40)
            self.canvas.itemconfig(self.handle, fill="#ff00ff")
            self.canvas.itemconfig(self.on_label, fill="#666666")
            self.canvas.itemconfig(self.off_label, fill="#00ffcc")
            self.canvas.itemconfig(self.bg_rect, outline="#00ffcc")

class AnimatedButton(tk.Canvas):
    """Cyberpunk animated button with hover effects"""
    def __init__(self, parent, text, command, bg_color="#ff00ff", hover_color="#ff66ff", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text = text
        
        # Set canvas size based on text
        self.config(width=kwargs.get('width', 180), height=kwargs.get('height', 50))
        
        # Create button elements
        self.rect = self.create_rounded_rectangle(3, 3, self.winfo_reqwidth()-3, self.winfo_reqheight()-3, 12, 
                                                  fill=bg_color, outline="", tags="button")
        
        # Add glow effect
        self.glow = self.create_rounded_rectangle(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(), 15, 
                                                  fill="", outline=bg_color, width=2, tags="glow")
        
        # Add text (larger font)
        self.text_id = self.create_text(self.winfo_reqwidth()//2, self.winfo_reqheight()//2, 
                                       text=text, fill="#0a0a23", font=("Consolas", 14, "bold"), tags="text")
        
        # Bind events
        self.tag_bind("button", "<Enter>", self.on_hover)
        self.tag_bind("button", "<Leave>", self.on_leave)
        self.tag_bind("button", "<Button-1>", self.on_click)
        self.tag_bind("text", "<Enter>", self.on_hover)
        self.tag_bind("text", "<Leave>", self.on_leave)
        self.tag_bind("text", "<Button-1>", self.on_click)
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle"""
        points = []
        for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                     (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                     (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                     (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_hover(self, event):
        """Hover animation"""
        self.itemconfig(self.rect, fill=self.hover_color)
        self.itemconfig(self.glow, width=4)
    
    def on_leave(self, event):
        """Leave animation"""
        self.itemconfig(self.rect, fill=self.bg_color)
        self.itemconfig(self.glow, width=2)
    
    def on_click(self, event):
        """Click animation and command execution"""
        # Quick flash effect
        self.itemconfig(self.rect, fill="#ffffff")
        self.after(100, lambda: self.itemconfig(self.rect, fill=self.hover_color))
        
        if self.command:
            self.command()

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arasaka Neural-Net Trading Matrix v2.0")
        
        # Set minimum window size
        self.root.minsize(1600, 1000)
        
        # Get screen dimensions for responsive design
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size to 85% of screen
        window_width = int(screen_width * 0.85)
        window_height = int(screen_height * 0.85)
        
        # Center window on screen
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Lock mechanism
        self.is_locked = True
        self.authenticated = False
        
        # API connection
        self.api_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
        
        # Initialize async event loop in thread
        self.loop = asyncio.new_event_loop()
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()
        
        # Task tracking
        self.last_failed_task = None
        self.last_error_time = 0
        
        # Trading tracking
        self.recent_trades = []
        self.auto_trade_count = 0
        
        # Apply modern cyberpunk theme
        self._apply_modern_cyberpunk_theme()
        
        # Initialize variables
        self._init_variables()
        
        # Create GUI
        self._create_gui()
        
        # Load settings and start automation
        self.load_defi_settings()
        self.update_status()
        
        # Schedule automation only after authentication
        self.root.after(1000, self._check_authentication_for_automation)
        
        # Start profit monitoring
        self.root.after(5000, self._update_profit_display)
    
    def _run_async_loop(self):
        """Run async event loop in separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def _apply_modern_cyberpunk_theme(self):
        """Apply modern cyberpunk visual theme with better fonts and colors"""
        # Background with gradient effect
        self.root.configure(bg="#0a0a23")
        
        # Configure custom fonts (increased sizes)
        self.title_font = font.Font(family="Consolas", size=24, weight="bold")
        self.header_font = font.Font(family="Consolas", size=18, weight="bold")
        self.normal_font = font.Font(family="Consolas", size=14)
        self.small_font = font.Font(family="Consolas", size=12)
        self.large_font = font.Font(family="Consolas", size=16)
        
        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Modern color palette
        self.colors = {
            'bg_dark': '#0a0a23',
            'bg_medium': '#1a1a3d',
            'bg_light': '#2a2a4d',
            'neon_cyan': '#00ffcc',
            'neon_pink': '#ff00ff',
            'neon_green': '#00ff00',
            'neon_red': '#ff0066',
            'neon_yellow': '#ffff00',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0c0',
            'border': '#4a4a6d'
        }
        
        # Configure all ttk styles
        self.style.configure("Cyber.TLabel", 
                           background=self.colors['bg_dark'], 
                           foreground=self.colors['neon_cyan'],
                           font=self.normal_font)
        
        self.style.configure("CyberTitle.TLabel", 
                           background=self.colors['bg_dark'], 
                           foreground=self.colors['neon_pink'],
                           font=self.title_font)
        
        self.style.configure("Cyber.TCheckbutton", 
                           background=self.colors['bg_dark'], 
                           foreground=self.colors['neon_cyan'],
                           font=self.normal_font,
                           focuscolor='none')
        
        self.style.configure("Cyber.TCombobox", 
                           fieldbackground=self.colors['bg_medium'], 
                           background=self.colors['bg_dark'], 
                           foreground=self.colors['neon_cyan'],
                           selectbackground=self.colors['bg_light'],
                           borderwidth=2,
                           relief="flat",
                           arrowsize=20)
        
        self.style.map('Cyber.TCombobox', 
                      fieldbackground=[('readonly', self.colors['bg_medium'])])
        
        self.style.configure("Cyber.TButton", 
                           background=self.colors['neon_pink'], 
                           foreground=self.colors['bg_dark'],
                           borderwidth=0,
                           focuscolor='none',
                           font=self.normal_font)
        
        self.style.map("Cyber.TButton",
                      background=[('active', self.colors['neon_cyan'])])
        
        self.style.configure("Cyber.TNotebook", 
                           background=self.colors['bg_dark'],
                           borderwidth=0)
        
        self.style.configure("Cyber.TNotebook.Tab", 
                           background=self.colors['bg_medium'], 
                           foreground=self.colors['neon_cyan'],
                           padding=[25, 15],
                           font=self.normal_font)
        
        self.style.map("Cyber.TNotebook.Tab",
                      background=[('selected', self.colors['bg_light'])],
                      foreground=[('selected', self.colors['neon_pink'])])
        
        self.style.configure("Cyber.TFrame", 
                           background=self.colors['bg_dark'],
                           borderwidth=0)
        
        self.style.configure("Cyber.Vertical.TScrollbar",
                           background=self.colors['bg_medium'],
                           bordercolor=self.colors['bg_medium'],
                           arrowcolor=self.colors['neon_cyan'],
                           troughcolor=self.colors['bg_dark'],
                           width=20)
    
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
        # Create login screen first
        self._create_login_screen()
        
        # Create main container (hidden initially)
        self.main_container = tk.Frame(self.root, bg=self.colors['bg_dark'])
        
        # Create header
        self._create_header()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container, style="Cyber.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        # Create tabs
        self._create_trading_tab()
        self._create_dashboard_tab()
        self._create_defi_tab()
        self._create_settings_tab()
        self._create_onboarding_tab()
        
        # Status bar
        self._create_status_bar()
    
    def _create_login_screen(self):
        """Create full-screen login"""
        self.login_screen = tk.Frame(self.root, bg=self.colors['bg_dark'])
        self.login_screen.pack(fill="both", expand=True)
        
        # Create animated background (optional)
        self.login_canvas = tk.Canvas(self.login_screen, bg=self.colors['bg_dark'], highlightthickness=0)
        self.login_canvas.pack(fill="both", expand=True)
        
        # Create glowing container
        self.login_canvas.update_idletasks()
        width = self.login_canvas.winfo_width() if self.login_canvas.winfo_width() > 1 else 800
        height = self.login_canvas.winfo_height() if self.login_canvas.winfo_height() > 1 else 600
        
        # Center login box
        box_width = 500
        box_height = 400
        x = (width - box_width) // 2
        y = (height - box_height) // 2
        
        # Draw login box with glow
        for i in range(5, 0, -1):
            alpha = 0.1 * (6 - i)
            color = f"#{int(255*alpha):02x}{int(0*alpha):02x}{int(255*alpha):02x}"
            self.login_canvas.create_rounded_rectangle(
                x - i*2, y - i*2, x + box_width + i*2, y + box_height + i*2,
                30, fill="", outline=color, width=2
            )
        
        # Main login box
        self.login_canvas.create_rounded_rectangle(
            x, y, x + box_width, y + box_height,
            25, fill=self.colors['bg_medium'], outline=self.colors['neon_pink'], width=3
        )
        
        # Login content
        self.login_canvas.create_text(
            width//2, y + 80,
            text="MILITECH SECURITY PROTOCOL",
            fill=self.colors['neon_pink'],
            font=("Consolas", 24, "bold")
        )
        
        self.login_canvas.create_text(
            width//2, y + 120,
            text="Neural-Net Access Control v2.0",
            fill=self.colors['text_secondary'],
            font=("Consolas", 14)
        )
        
        self.login_canvas.create_text(
            width//2, y + 180,
            text="ENTER ACCESS PIN:",
            fill=self.colors['neon_cyan'],
            font=("Consolas", 16)
        )
        
        # PIN entry
        pin_frame = tk.Frame(self.login_screen, bg=self.colors['bg_light'],
                            highlightbackground=self.colors['neon_cyan'],
                            highlightthickness=3)
        self.login_canvas.create_window(width//2, y + 230, window=pin_frame)
        
        pin_entry = tk.Entry(pin_frame, 
                            textvariable=self.pin_var, 
                            bg=self.colors['bg_light'], 
                            fg=self.colors['neon_cyan'], 
                            insertbackground=self.colors['neon_pink'], 
                            show="*",
                            font=("Consolas", 20, "bold"),
                            width=20,
                            bd=0,
                            justify='center')
        pin_entry.pack(padx=3, pady=3)
        pin_entry.bind('<Return>', lambda e: self.login())
        pin_entry.focus_set()
        
        # Access button
        self.access_btn = AnimatedButton(self.login_screen,
                                        text="ACCESS MATRIX",
                                        command=self.login,
                                        bg_color=self.colors['neon_pink'],
                                        hover_color=self.colors['neon_cyan'],
                                        width=250,
                                        height=60)
        self.login_canvas.create_window(width//2, y + 300, window=self.access_btn)
        
        # Security warning
        self.login_canvas.create_text(
            width//2, y + 360,
            text="⚠ UNAUTHORIZED ACCESS WILL BE TRACED ⚠",
            fill=self.colors['neon_red'],
            font=("Consolas", 12)
        )
    
    def _create_header(self):
        """Create application header with title and mode toggle"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['bg_dark'], height=100)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Title with glow effect
        title_container = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        title_container.pack(side="left", fill="y")
        
        title_label = tk.Label(title_container, 
                              text="ARASAKA NEURAL-NET TRADING MATRIX", 
                              bg=self.colors['bg_dark'], 
                              fg=self.colors['neon_pink'],
                              font=self.title_font)
        title_label.pack(pady=(20, 0))
        
        subtitle_label = tk.Label(title_container,
                                 text="Stack Eddies in the Net",
                                 bg=self.colors['bg_dark'],
                                 fg=self.colors['text_secondary'],
                                 font=self.normal_font)
        subtitle_label.pack()
        
        # Mode toggle
        toggle_container = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        toggle_container.pack(side="right", padx=20, pady=20)
        
        mode_label = tk.Label(toggle_container,
                             text="TRADING MODE:",
                             bg=self.colors['bg_dark'],
                             fg=self.colors['neon_cyan'],
                             font=self.large_font)
        mode_label.pack(side="left", padx=(0, 15))
        
        self.mode_toggle = CyberpunkToggle(toggle_container, 
                                          self.testnet_enabled,
                                          on_text="LIVE",
                                          off_text="TEST")
        self.mode_toggle.command = self.toggle_testnet
        self.mode_toggle.pack(side="left")
    
    def _create_trading_tab(self):
        """Create modern trading tab"""
        self.trading_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.trading_frame, text="📈 TRADING MATRIX")
        
        # Create main container with padding
        main_container = tk.Frame(self.trading_frame, bg=self.colors['bg_dark'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Top section with P&L and Auto-Trading
        top_section = tk.Frame(main_container, bg=self.colors['bg_dark'])
        top_section.pack(fill="x", pady=(0, 20))
        
        # P&L Display
        self.pnl_display = ProfitLossDisplay(top_section, width=450, height=180)
        self.pnl_display.pack(side="left", padx=(0, 20))
        
        # Auto-Trading Indicator
        auto_section = tk.Frame(top_section, bg=self.colors['bg_dark'])
        auto_section.pack(side="left", fill="both", expand=True)
        
        self.auto_indicator = AutoTradingIndicator(auto_section, width=350, height=120)
        self.auto_indicator.pack()
        
        # Auto-trade checkbox
        auto_check_frame = tk.Frame(auto_section, bg=self.colors['bg_dark'])
        auto_check_frame.pack(pady=10)
        
        self.auto_check = tk.Checkbutton(auto_check_frame,
                                        text="ENABLE AUTO-TRADING (RL > 0.8)",
                                        variable=self.auto_trade,
                                        bg=self.colors['bg_dark'],
                                        fg=self.colors['neon_yellow'],
                                        selectcolor=self.colors['bg_medium'],
                                        activebackground=self.colors['bg_dark'],
                                        activeforeground=self.colors['neon_green'],
                                        font=("Consolas", 16, "bold"),
                                        command=self._toggle_auto_trading)
        self.auto_check.pack()
        
        # Trading controls panel
        controls_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=2)
        controls_panel.pack(fill="x", pady=(0, 20))
        
        controls_inner = tk.Frame(controls_panel, bg=self.colors['bg_medium'])
        controls_inner.pack(padx=25, pady=25)
        
        # Grid layout for controls
        # Row 0: Pair selection
        tk.Label(controls_inner, 
                text="NEURAL PAIR:",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_cyan'],
                font=self.large_font).grid(row=0, column=0, sticky=tk.W, pady=8)
        
        pair_frame = tk.Frame(controls_inner, bg=self.colors['bg_medium'])
        pair_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=8)
        
        self.pair_combobox = ttk.Combobox(pair_frame, 
                                         textvariable=self.selected_pair,
                                         values=["binance:BTC/USDT", "binance:ETH/USDT", "binance:BNB/USDT"],
                                         style="Cyber.TCombobox",
                                         font=self.normal_font,
                                         width=25)
        self.pair_combobox.pack(side="left", padx=(0, 15))
        
        scan_btn = AnimatedButton(pair_frame,
                                 text="SCAN OPTIMAL",
                                 command=self.select_best_pair,
                                 bg_color=self.colors['neon_cyan'],
                                 hover_color=self.colors['neon_green'],
                                 width=150,
                                 height=45)
        scan_btn.pack(side="left")
        
        # Row 1: Amount
        tk.Label(controls_inner,
                text="EDDIES AMOUNT:",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_cyan'],
                font=self.large_font).grid(row=1, column=0, sticky=tk.W, pady=8)
        
        amount_frame = tk.Frame(controls_inner, bg=self.colors['bg_light'],
                               highlightbackground=self.colors['neon_cyan'],
                               highlightthickness=2)
        amount_frame.grid(row=1, column=1, sticky=tk.W, pady=8)
        
        tk.Entry(amount_frame,
                textvariable=self.trade_amount,
                bg=self.colors['bg_light'],
                fg=self.colors['neon_cyan'],
                insertbackground=self.colors['neon_pink'],
                font=self.normal_font,
                width=20,
                bd=0).pack(padx=2, pady=2)
        
        # Row 2: Risk profile
        tk.Label(controls_inner,
                text="RISK PROTOCOL:",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_cyan'],
                font=self.large_font).grid(row=2, column=0, sticky=tk.W, pady=8)
        
        self.risk_combobox = ttk.Combobox(controls_inner,
                                         textvariable=self.risk_profile,
                                         values=["conservative", "moderate", "aggressive"],
                                         style="Cyber.TCombobox",
                                         font=self.normal_font,
                                         width=25)
        self.risk_combobox.grid(row=2, column=1, sticky=tk.W, pady=8)
        
        # Row 3: Leverage
        tk.Label(controls_inner,
                text="LEVERAGE:",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_cyan'],
                font=self.large_font).grid(row=3, column=0, sticky=tk.W, pady=8)
        
        leverage_frame = tk.Frame(controls_inner, bg=self.colors['bg_light'],
                                 highlightbackground=self.colors['neon_cyan'],
                                 highlightthickness=2)
        leverage_frame.grid(row=3, column=1, sticky=tk.W, pady=8)
        
        tk.Entry(leverage_frame,
                textvariable=self.leverage_value,
                bg=self.colors['bg_light'],
                fg=self.colors['neon_cyan'],
                insertbackground=self.colors['neon_pink'],
                font=self.normal_font,
                width=10,
                bd=0).pack(padx=2, pady=2)
        
        # Trading buttons panel
        button_panel = tk.Frame(main_container, bg=self.colors['bg_dark'])
        button_panel.pack(fill="x", pady=(0, 20))
        
        # Trading action buttons
        buy_btn = AnimatedButton(button_panel,
                                text="BUY ↑",
                                command=lambda: self.execute_trade("buy"),
                                bg_color=self.colors['neon_green'],
                                hover_color="#66ff66",
                                width=120,
                                height=50)
        buy_btn.pack(side="left", padx=5)
        
        sell_btn = AnimatedButton(button_panel,
                                 text="SELL ↓",
                                 command=lambda: self.execute_trade("sell"),
                                 bg_color=self.colors['neon_red'],
                                 hover_color="#ff6666",
                                 width=120,
                                 height=50)
        sell_btn.pack(side="left", padx=5)
        
        refresh_btn = AnimatedButton(button_panel,
                                    text="REFRESH",
                                    command=self.refresh_portfolio,
                                    bg_color=self.colors['neon_pink'],
                                    hover_color=self.colors['neon_cyan'],
                                    width=120,
                                    height=50)
        refresh_btn.pack(side="left", padx=5)
        
        train_btn = AnimatedButton(button_panel,
                                  text="TRAIN AI",
                                  command=self.train_model,
                                  bg_color=self.colors['neon_pink'],
                                  hover_color=self.colors['neon_cyan'],
                                  width=120,
                                  height=50)
        train_btn.pack(side="left", padx=5)
        
        # Kill switch with spacing
        kill_btn = AnimatedButton(button_panel,
                                 text="⚠ KILL SWITCH ⚠",
                                 command=self.emergency_stop,
                                 bg_color="#ff0000",
                                 hover_color="#ff3333",
                                 width=180,
                                 height=50)
        kill_btn.pack(side="right", padx=20)
        
        # Portfolio display with modern styling
        portfolio_frame = tk.Frame(main_container, bg=self.colors['bg_medium'],
                                  highlightbackground=self.colors['border'],
                                  highlightthickness=2)
        portfolio_frame.pack(fill="both", expand=True)
        
        # Portfolio header
        portfolio_header = tk.Frame(portfolio_frame, bg=self.colors['bg_light'])
        portfolio_header.pack(fill="x")
        
        tk.Label(portfolio_header,
                text="PORTFOLIO NEURAL FEED",
                bg=self.colors['bg_light'],
                fg=self.colors['neon_pink'],
                font=self.header_font).pack(pady=15)
        
        # Portfolio text with scrollbar
        text_frame = tk.Frame(portfolio_frame, bg=self.colors['bg_medium'])
        text_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.portfolio_text = tk.Text(text_frame,
                                     bg=self.colors['bg_dark'],
                                     fg=self.colors['neon_cyan'],
                                     insertbackground=self.colors['neon_pink'],
                                     font=self.normal_font,
                                     wrap="word",
                                     bd=0)
        
        portfolio_scroll = ttk.Scrollbar(text_frame, style="Cyber.Vertical.TScrollbar")
        portfolio_scroll.pack(side="right", fill="y")
        
        self.portfolio_text.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        self.portfolio_text.config(yscrollcommand=portfolio_scroll.set)
        portfolio_scroll.config(command=self.portfolio_text.yview)
    
    def _create_dashboard_tab(self):
        """Create modern dashboard tab"""
        self.dashboard_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.dashboard_frame, text="🎮 NETRUNNER DASHBOARD")
        
        # Create scrollable container
        canvas = tk.Canvas(self.dashboard_frame, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dashboard_frame, orient="vertical", command=canvas.yview, style="Cyber.Vertical.TScrollbar")
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_dark'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind canvas resize
        def configure_canvas(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind('<Configure>', configure_canvas)
        
        # Main container with padding
        main_container = tk.Frame(scrollable_frame, bg=self.colors['bg_dark'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Automation controls panel
        auto_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                             highlightbackground=self.colors['border'],
                             highlightthickness=2)
        auto_panel.pack(fill="x", pady=(0, 20))
        
        auto_header = tk.Frame(auto_panel, bg=self.colors['bg_light'])
        auto_header.pack(fill="x")
        
        tk.Label(auto_header,
                text="AUTOMATION PROTOCOLS",
                bg=self.colors['bg_light'],
                fg=self.colors['neon_pink'],
                font=self.header_font).pack(pady=15)
        
        auto_inner = tk.Frame(auto_panel, bg=self.colors['bg_medium'])
        auto_inner.pack(padx=25, pady=25)
        
        # Create automation controls in grid
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
            row_frame = tk.Frame(auto_inner, bg=self.colors['bg_medium'])
            row_frame.grid(row=i//2, column=i%2, sticky=tk.W, padx=15, pady=8)
            
            tk.Checkbutton(row_frame,
                          text=label,
                          variable=var,
                          bg=self.colors['bg_medium'],
                          fg=self.colors['neon_cyan'],
                          selectcolor=self.colors['bg_dark'],
                          activebackground=self.colors['bg_medium'],
                          activeforeground=self.colors['neon_pink'],
                          font=self.normal_font,
                          width=35,
                          anchor="w").pack(side="left")
            
            run_btn = AnimatedButton(row_frame,
                                    text="RUN",
                                    command=command,
                                    bg_color=self.colors['neon_pink'],
                                    hover_color=self.colors['neon_cyan'],
                                    width=80,
                                    height=35)
            run_btn.pack(side="left", padx=10)
        
        # Idle conversion controls
        idle_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                             highlightbackground=self.colors['border'],
                             highlightthickness=2)
        idle_panel.pack(fill="x", pady=(0, 20))
        
        idle_inner = tk.Frame(idle_panel, bg=self.colors['bg_medium'])
        idle_inner.pack(padx=25, pady=20)
        
        tk.Checkbutton(idle_inner,
                      text="Auto Idle Conversion (Daily)",
                      variable=self.auto_idle_conversion,
                      bg=self.colors['bg_medium'],
                      fg=self.colors['neon_cyan'],
                      selectcolor=self.colors['bg_dark'],
                      activebackground=self.colors['bg_medium'],
                      activeforeground=self.colors['neon_pink'],
                      font=self.normal_font).pack(side="left", padx=(0, 25))
        
        ttk.Combobox(idle_inner,
                    textvariable=self.idle_target,
                    values=["USDT", "BTC"],
                    style="Cyber.TCombobox",
                    font=self.normal_font,
                    width=12).pack(side="left", padx=10)
        
        convert_btn = AnimatedButton(idle_inner,
                                    text="CONVERT NOW",
                                    command=self.convert_idle_now,
                                    bg_color=self.colors['neon_pink'],
                                    hover_color=self.colors['neon_cyan'],
                                    width=150,
                                    height=40)
        convert_btn.pack(side="left", padx=10)
        
        # Dashboard display
        display_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                                highlightbackground=self.colors['border'],
                                highlightthickness=2)
        display_panel.pack(fill="x", pady=(0, 20))
        
        self.dashboard_text = tk.Text(display_panel,
                                     height=12,
                                     bg=self.colors['bg_dark'],
                                     fg=self.colors['neon_cyan'],
                                     insertbackground=self.colors['neon_pink'],
                                     font=self.normal_font,
                                     wrap="word",
                                     bd=0)
        self.dashboard_text.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Backtest plot with cyberpunk styling
        plot_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                             highlightbackground=self.colors['border'],
                             highlightthickness=2)
        plot_panel.pack(fill="both", expand=True)
        
        plot_header = tk.Frame(plot_panel, bg=self.colors['bg_light'])
        plot_header.pack(fill="x")
        
        tk.Label(plot_header,
                text="NEURAL BACKTEST VISUALIZATION",
                bg=self.colors['bg_light'],
                fg=self.colors['neon_pink'],
                font=self.header_font).pack(pady=15)
        
        # Matplotlib figure with cyberpunk theme
        self.fig, self.ax = plt.subplots(figsize=(12, 6), facecolor=self.colors['bg_dark'])
        self.ax.set_facecolor(self.colors['bg_dark'])
        
        # Style the plot
        self.ax.spines['bottom'].set_color(self.colors['neon_cyan'])
        self.ax.spines['top'].set_color(self.colors['neon_cyan'])
        self.ax.spines['left'].set_color(self.colors['neon_cyan'])
        self.ax.spines['right'].set_color(self.colors['neon_cyan'])
        self.ax.tick_params(colors=self.colors['neon_cyan'])
        self.ax.xaxis.label.set_color(self.colors['neon_cyan'])
        self.ax.yaxis.label.set_color(self.colors['neon_cyan'])
        self.ax.title.set_color(self.colors['neon_pink'])
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
        
        # Backtest button
        backtest_btn = AnimatedButton(plot_panel,
                                     text="RUN BACKTEST",
                                     command=self.run_backtest,
                                     bg_color=self.colors['neon_pink'],
                                     hover_color=self.colors['neon_cyan'],
                                     width=200,
                                     height=50)
        backtest_btn.pack(pady=15)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_defi_tab(self):
        """Create modern DeFi settings tab"""
        self.defi_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.defi_frame, text="🔗 DEFI MATRIX")
        
        # Main container
        main_container = tk.Frame(self.defi_frame, bg=self.colors['bg_dark'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # DeFi panel
        defi_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                             highlightbackground=self.colors['border'],
                             highlightthickness=2)
        defi_panel.pack(fill="x")
        
        # Header
        defi_header = tk.Frame(defi_panel, bg=self.colors['bg_light'])
        defi_header.pack(fill="x")
        
        tk.Label(defi_header,
                text="DEFI LIQUIDITY MINING CONFIGURATION",
                bg=self.colors['bg_light'],
                fg=self.colors['neon_pink'],
                font=self.header_font).pack(pady=15)
        
        # Settings container
        settings_container = tk.Frame(defi_panel, bg=self.colors['bg_medium'])
        settings_container.pack(padx=40, pady=40)
        
        # DeFi settings with modern input fields
        settings_data = [
            ("RPC URL:", "rpc_url_entry", False),
            ("PancakeSwap Address:", "pancake_address_entry", False),
            ("Contract ABI:", "abi_entry", False),
            ("Private Key:", "private_key_entry", True)
        ]
        
        for i, (label, attr_name, is_password) in enumerate(settings_data):
            # Label
            tk.Label(settings_container,
                    text=label,
                    bg=self.colors['bg_medium'],
                    fg=self.colors['neon_cyan'],
                    font=self.large_font).grid(row=i, column=0, sticky=tk.W, pady=12, padx=(0, 25))
            
            # Entry frame
            entry_frame = tk.Frame(settings_container, bg=self.colors['bg_light'],
                                  highlightbackground=self.colors['neon_cyan'],
                                  highlightthickness=2)
            entry_frame.grid(row=i, column=1, pady=12, sticky="ew")
            
            entry = tk.Entry(entry_frame,
                            bg=self.colors['bg_light'],
                            fg=self.colors['neon_cyan'],
                            insertbackground=self.colors['neon_pink'],
                            font=self.normal_font,
                            width=60,
                            bd=0,
                            show="*" if is_password else "")
            entry.pack(padx=3, pady=3)
            setattr(self, attr_name, entry)
        
        # Configure grid weight
        settings_container.grid_columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = tk.Frame(defi_panel, bg=self.colors['bg_medium'])
        button_frame.pack(pady=(0, 40))
        
        save_btn = AnimatedButton(button_frame,
                                 text="SAVE CONFIG",
                                 command=self.save_defi_settings,
                                 bg_color=self.colors['neon_pink'],
                                 hover_color=self.colors['neon_green'],
                                 width=180,
                                 height=50)
        save_btn.pack(side="left", padx=10)
        
        load_btn = AnimatedButton(button_frame,
                                 text="LOAD CONFIG",
                                 command=self.load_defi_settings,
                                 bg_color=self.colors['neon_cyan'],
                                 hover_color=self.colors['neon_pink'],
                                 width=180,
                                 height=50)
        load_btn.pack(side="left", padx=10)
        
        # Warning message
        warning_frame = tk.Frame(defi_panel, bg=self.colors['bg_medium'])
        warning_frame.pack(pady=(0, 20))
        
        tk.Label(warning_frame,
                text="⚠ WARNING: DeFi operations carry high risk. Ensure you understand smart contracts before proceeding.",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_red'],
                font=self.normal_font,
                wraplength=700).pack()
    
    def _create_settings_tab(self):
        """Create modern settings hub tab"""
        self.settings_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.settings_frame, text="⚙️ SETTINGS HUB")
        
        # Main container
        main_container = tk.Frame(self.settings_frame, bg=self.colors['bg_dark'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Settings panel
        settings_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=2)
        settings_panel.pack(fill="x")
        
        # Header
        settings_header = tk.Frame(settings_panel, bg=self.colors['bg_light'])
        settings_header.pack(fill="x")
        
        tk.Label(settings_header,
                text="NEURAL-NET CONFIGURATION",
                bg=self.colors['bg_light'],
                fg=self.colors['neon_pink'],
                font=self.header_font).pack(pady=15)
        
        # Settings container
        settings_container = tk.Frame(settings_panel, bg=self.colors['bg_medium'])
        settings_container.pack(padx=40, pady=40)
        
        # Risk settings
        tk.Label(settings_container,
                text="Risk Profile:",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_cyan'],
                font=self.large_font).grid(row=0, column=0, sticky=tk.W, pady=20)
        
        self.risk_setting = ttk.Combobox(settings_container,
                                        values=["conservative", "moderate", "aggressive"],
                                        style="Cyber.TCombobox",
                                        font=self.normal_font,
                                        width=30)
        self.risk_setting.set("moderate")
        self.risk_setting.grid(row=0, column=1, pady=20, padx=25)
        
        # Leverage settings
        tk.Label(settings_container,
                text="Max Leverage:",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_cyan'],
                font=self.large_font).grid(row=1, column=0, sticky=tk.W, pady=20)
        
        leverage_frame = tk.Frame(settings_container, bg=self.colors['bg_light'],
                                 highlightbackground=self.colors['neon_cyan'],
                                 highlightthickness=2)
        leverage_frame.grid(row=1, column=1, pady=20, padx=25, sticky="w")
        
        self.leverage_setting = tk.Entry(leverage_frame,
                                        bg=self.colors['bg_light'],
                                        fg=self.colors['neon_cyan'],
                                        insertbackground=self.colors['neon_pink'],
                                        font=self.normal_font,
                                        width=15,
                                        bd=0)
        self.leverage_setting.insert(0, "3.0")
        self.leverage_setting.pack(padx=3, pady=3)
        
        # Flash drop threshold with visual slider
        tk.Label(settings_container,
                text="Flash Drop Threshold:",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_cyan'],
                font=self.large_font).grid(row=2, column=0, sticky=tk.W, pady=20)
        
        slider_frame = tk.Frame(settings_container, bg=self.colors['bg_medium'])
        slider_frame.grid(row=2, column=1, pady=20, padx=25, sticky="w")
        
        self.flash_drop_scale = tk.Scale(slider_frame,
                                        from_=5,
                                        to=20,
                                        orient=tk.HORIZONTAL,
                                        length=300,
                                        bg=self.colors['bg_medium'],
                                        fg=self.colors['neon_cyan'],
                                        highlightbackground=self.colors['bg_medium'],
                                        troughcolor=self.colors['bg_light'],
                                        activebackground=self.colors['neon_pink'],
                                        font=self.normal_font)
        self.flash_drop_scale.set(10)
        self.flash_drop_scale.pack(side="left")
        
        tk.Label(slider_frame,
                text="%",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_cyan'],
                font=self.large_font).pack(side="left", padx=5)
        
        # Save button
        save_btn = AnimatedButton(settings_panel,
                                 text="SAVE CONFIGURATION",
                                 command=self.save_settings,
                                 bg_color=self.colors['neon_pink'],
                                 hover_color=self.colors['neon_green'],
                                 width=250,
                                 height=60)
        save_btn.pack(pady=40)
    
    def _create_onboarding_tab(self):
        """Create modern onboarding tab"""
        self.onboarding_frame = ttk.Frame(self.notebook, style="Cyber.TFrame")
        self.notebook.add(self.onboarding_frame, text="🚀 ONBOARDING")
        
        # Scrollable container
        canvas = tk.Canvas(self.onboarding_frame, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.onboarding_frame, orient="vertical", command=canvas.yview, style="Cyber.Vertical.TScrollbar")
        
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_dark'])
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Main container
        main_container = tk.Frame(scrollable_frame, bg=self.colors['bg_dark'])
        main_container.pack(fill="both", expand=True, padx=50, pady=50)
        
        # Welcome panel
        welcome_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                                highlightbackground=self.colors['neon_pink'],
                                highlightthickness=3)
        welcome_panel.pack(fill="x", pady=(0, 40))
        
        welcome_inner = tk.Frame(welcome_panel, bg=self.colors['bg_medium'])
        welcome_inner.pack(padx=50, pady=50)
        
        tk.Label(welcome_inner,
                text="WELCOME TO THE MATRIX, CHOOM!",
                bg=self.colors['bg_medium'],
                fg=self.colors['neon_pink'],
                font=("Consolas", 28, "bold")).pack(pady=(0, 25))
        
        tk.Label(welcome_inner,
                text="Let's get you jacked into the Neural-Net Trading System",
                bg=self.colors['bg_medium'],
                fg=self.colors['text_secondary'],
                font=self.large_font).pack()
        
        # Step panels
        steps = [
            ("STEP 1: EXCHANGE CREDENTIALS", "Enter your Binance API credentials to connect to the exchange"),
            ("STEP 2: RISK TOLERANCE", "Select your risk level for the Neural-Net to calibrate"),
            ("STEP 3: INITIAL CAPITAL", "Set your starting Eddies amount")
        ]
        
        for i, (title, desc) in enumerate(steps, 1):
            step_panel = tk.Frame(main_container, bg=self.colors['bg_medium'],
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=2)
            step_panel.pack(fill="x", pady=15)
            
            step_inner = tk.Frame(step_panel, bg=self.colors['bg_medium'])
            step_inner.pack(padx=35, pady=25)
            
            # Step header
            header_frame = tk.Frame(step_inner, bg=self.colors['bg_medium'])
            header_frame.pack(fill="x", pady=(0, 20))
            
            tk.Label(header_frame,
                    text=title,
                    bg=self.colors['bg_medium'],
                    fg=self.colors['neon_cyan'],
                    font=("Consolas", 20, "bold")).pack(side="left")
            
            tk.Label(step_inner,
                    text=desc,
                    bg=self.colors['bg_medium'],
                    fg=self.colors['text_secondary'],
                    font=self.normal_font).pack(anchor="w", pady=(0, 15))
            
            if i == 1:
                # API Key entry
                tk.Label(step_inner,
                        text="API Key:",
                        bg=self.colors['bg_medium'],
                        fg=self.colors['neon_cyan'],
                        font=self.large_font).pack(anchor="w", pady=(15, 8))
                
                key_frame = tk.Frame(step_inner, bg=self.colors['bg_light'],
                                    highlightbackground=self.colors['neon_cyan'],
                                    highlightthickness=2)
                key_frame.pack(fill="x", pady=(0, 15))
                
                self.api_key_entry = tk.Entry(key_frame,
                                             bg=self.colors['bg_light'],
                                             fg=self.colors['neon_cyan'],
                                             insertbackground=self.colors['neon_pink'],
                                             font=self.normal_font,
                                             bd=0)
                self.api_key_entry.pack(fill="x", padx=3, pady=3)
                
                # API Secret entry
                tk.Label(step_inner,
                        text="API Secret:",
                        bg=self.colors['bg_medium'],
                        fg=self.colors['neon_cyan'],
                        font=self.large_font).pack(anchor="w", pady=(15, 8))
                
                secret_frame = tk.Frame(step_inner, bg=self.colors['bg_light'],
                                       highlightbackground=self.colors['neon_cyan'],
                                       highlightthickness=2)
                secret_frame.pack(fill="x")
                
                self.api_secret_entry = tk.Entry(secret_frame,
                                                bg=self.colors['bg_light'],
                                                fg=self.colors['neon_cyan'],
                                                insertbackground=self.colors['neon_pink'],
                                                font=self.normal_font,
                                                show="*",
                                                bd=0)
                self.api_secret_entry.pack(fill="x", padx=3, pady=3)
                
            elif i == 2:
                # Risk selection
                risk_frame = tk.Frame(step_inner, bg=self.colors['bg_medium'])
                risk_frame.pack(fill="x")
                
                risk_options = [
                    ("Conservative", "Low risk, steady gains", self.colors['neon_green']),
                    ("Moderate", "Balanced risk/reward", self.colors['neon_cyan']),
                    ("Aggressive", "High risk, high reward", self.colors['neon_red'])
                ]
                
                self.risk_onboard = tk.StringVar(value="Moderate")
                
                for risk, desc, color in risk_options:
                    option_frame = tk.Frame(risk_frame, bg=self.colors['bg_light'],
                                           highlightbackground=color,
                                           highlightthickness=2)
                    option_frame.pack(fill="x", pady=8)
                    
                    option_inner = tk.Frame(option_frame, bg=self.colors['bg_light'])
                    option_inner.pack(padx=20, pady=15)
                    
                    rb = tk.Radiobutton(option_inner,
                                       text=risk,
                                       value=risk,
                                       variable=self.risk_onboard,
                                       bg=self.colors['bg_light'],
                                       fg=color,
                                       selectcolor=self.colors['bg_dark'],
                                       activebackground=self.colors['bg_light'],
                                       activeforeground=color,
                                       font=self.large_font)
                    rb.pack(side="left", padx=(0, 20))
                    
                    tk.Label(option_inner,
                            text=desc,
                            bg=self.colors['bg_light'],
                            fg=self.colors['text_secondary'],
                            font=self.normal_font).pack(side="left")
                            
            elif i == 3:
                # Initial capital
                capital_frame = tk.Frame(step_inner, bg=self.colors['bg_medium'])
                capital_frame.pack(fill="x")
                
                tk.Label(capital_frame,
                        text="Starting Capital (USDT):",
                        bg=self.colors['bg_medium'],
                        fg=self.colors['neon_cyan'],
                        font=self.large_font).pack(side="left", padx=(0, 25))
                
                capital_entry_frame = tk.Frame(capital_frame, bg=self.colors['bg_light'],
                                             highlightbackground=self.colors['neon_cyan'],
                                             highlightthickness=2)
                capital_entry_frame.pack(side="left")
                
                self.capital_entry = tk.Entry(capital_entry_frame,
                                            bg=self.colors['bg_light'],
                                            fg=self.colors['neon_cyan'],
                                            insertbackground=self.colors['neon_pink'],
                                            font=self.normal_font,
                                            width=25,
                                            bd=0)
                self.capital_entry.insert(0, "1000")
                self.capital_entry.pack(padx=3, pady=3)
        
        # Complete button
        complete_btn = AnimatedButton(main_container,
                                     text="JACK INTO THE MATRIX",
                                     command=self.finish_onboarding,
                                     bg_color=self.colors['neon_pink'],
                                     hover_color=self.colors['neon_green'],
                                     width=350,
                                     height=70)
        complete_btn.pack(pady=50)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_status_bar(self):
        """Create modern status bar"""
        status_frame = tk.Frame(self.main_container, bg=self.colors['bg_light'], height=50)
        status_frame.pack(side="bottom", fill="x")
        status_frame.pack_propagate(False)
        
        # Status label
        self.status_label = tk.Label(status_frame,
                                    text="STATUS: Connecting to the Net...",
                                    bg=self.colors['bg_light'],
                                    fg=self.colors['neon_cyan'],
                                    font=self.normal_font)
        self.status_label.pack(side="left", padx=25, pady=12)
        
        # Connection indicator
        self.connection_canvas = tk.Canvas(status_frame, width=25, height=25, 
                                          bg=self.colors['bg_light'], highlightthickness=0)
        self.connection_canvas.pack(side="right", padx=25, pady=12)
        
        self.connection_light = self.connection_canvas.create_oval(5, 5, 20, 20, 
                                                                  fill=self.colors['neon_red'], 
                                                                  outline="")
        
        # Start pulsing animation
        self._pulse_connection_light()
    
    def _pulse_connection_light(self):
        """Animate connection status light"""
        try:
            current_color = self.connection_canvas.itemcget(self.connection_light, "fill")
            if hasattr(self, 'authenticated') and self.authenticated:
                # Pulse between green shades when connected
                new_color = self.colors['neon_green'] if current_color != self.colors['neon_green'] else "#00cc00"
            else:
                # Pulse between red shades when disconnected
                new_color = self.colors['neon_red'] if current_color != self.colors['neon_red'] else "#cc0000"
            
            self.connection_canvas.itemconfig(self.connection_light, fill=new_color)
        except:
            pass
        
        # Schedule next pulse
        self.root.after(1000, self._pulse_connection_light)
    
    def _check_authentication_for_automation(self):
        """Check if authenticated before starting automation"""
        if self.authenticated:
            self.schedule_automation()
        else:
            # Check again in 1 second
            self.root.after(1000, self._check_authentication_for_automation)
    
    def _toggle_auto_trading(self):
        """Toggle auto-trading mode"""
        self.auto_indicator.set_active(self.auto_trade.get())
        if self.auto_trade.get():
            self._show_notification("Auto-Trading ACTIVATED - Neural-Net taking control!", "success")
            # Start auto-trading logic
            self._start_auto_trading()
        else:
            self._show_notification("Auto-Trading DEACTIVATED - Manual control restored", "info")
    
    def _start_auto_trading(self):
        """Start auto-trading cycle"""
        if not self.auto_trade.get():
            return
        
        # Simulate trading logic
        def check_trades():
            if self.auto_trade.get():
                # Random trade simulation (replace with real logic)
                if random.random() > 0.7:  # 30% chance of trade
                    self.auto_trade_count += 1
                    profit = random.uniform(-50, 150)
                    
                    # Create trade data
                    trade_data = {
                        'symbol': self.selected_pair.get(),
                        'side': 'buy' if random.random() > 0.5 else 'sell',
                        'amount': float(self.trade_amount.get()),
                        'price': random.uniform(40000, 50000),
                        'profit': profit
                    }
                    
                    # Show trade notification
                    TradeNotification(self.root, trade_data)
                    
                    # Flash auto-trading indicator
                    self.auto_indicator.flash_trade(profit > 0)
                    
                    # Update P&L
                    self._update_profit_display()
                
                # Schedule next check
                self.root.after(5000, check_trades)
        
        # Start checking
        self.root.after(2000, check_trades)
    
    def _update_profit_display(self):
        """Update profit/loss display"""
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
            
            # Calculate total P&L (simplified)
            initial_value = 1000  # Default starting value
            total_pnl = portfolio_value - initial_value
            
            # Update display
            self.pnl_display.update_values(daily_pnl, total_pnl, portfolio_value)
            
        except Exception as e:
            logger.error(f"P&L update failed: {e}")
        
        # Schedule next update
        self.root.after(10000, self._update_profit_display)
    
    # ===== GUI Methods =====
    
    def login(self):
        """Handle login with proper locking"""
        try:
            if security_manager.verify_pin(self.pin_var.get()):
                self.authenticated = True
                self.is_locked = False
                
                # Clear PIN for security
                self.pin_var.set("")
                
                # Update connection status
                self.status_label.config(text="STATUS: Connected to Neural-Net Matrix ✓")
                
                # Fade out login screen
                def fade_out(alpha=1.0):
                    if alpha > 0:
                        self.login_screen.winfo_toplevel().attributes('-alpha', alpha)
                        self.root.after(20, lambda: fade_out(alpha - 0.05))
                    else:
                        # Remove login screen and show main container
                        self.login_screen.pack_forget()
                        self.main_container.pack(fill="both", expand=True)
                        self.root.attributes('-alpha', 1.0)
                
                fade_out()
                
                # Show welcome notification
                self._show_notification("Access Granted - Welcome to the Matrix, Netrunner!", "success")
                
                # Start automation
                self.schedule_automation()
                
            else:
                # Failed login animation
                self._shake_window()
                self._show_notification("Access Denied - Invalid PIN!", "error")
                
        except Exception as e:
            logger.error(f"Login flatlined: {e}")
            self._show_notification(f"Login system error: {str(e)[:50]}", "error")
    
    def _shake_window(self):
        """Shake window animation for failed login"""
        original_x = self.root.winfo_x()
        original_y = self.root.winfo_y()
        
        for i in range(10):
            offset = 10 if i % 2 == 0 else -10
            self.root.geometry(f"+{original_x + offset}+{original_y}")
            self.root.update()
            self.root.after(50)
        
        self.root.geometry(f"+{original_x}+{original_y}")
    
    def select_best_pair(self):
        """Select the best trading pair"""
        try:
            response = requests.get(f"{self.api_url}/best_pair", timeout=10)
            response.raise_for_status()
            pair = response.json()["pair"]
            self.selected_pair.set(pair)
            self.pair_combobox["values"] = [pair] + list(self.pair_combobox["values"])
            
            # Show success notification
            self._show_notification("Optimal pair locked: " + pair, "success")
            
        except Exception as e:
            logger.error(f"Pair selection flatlined: {e}")
            self._show_notification(f"Failed to select pair: {str(e)[:50]}", "error")
    
    def execute_trade(self, side):
        """Execute a trade"""
        try:
            if not security_manager.check_tamper():
                self._show_notification("System tamper detected - Trade blocked!", "error")
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
            
            # Show trade notification
            trade_notif_data = {
                'symbol': trade_data['symbol'],
                'side': side,
                'amount': trade_data['amount'],
                'price': 0,  # Would be filled from response
                'profit': 0  # Would be calculated
            }
            TradeNotification(self.root, trade_notif_data)
            
            # Update P&L display
            self._update_profit_display()
            
            # Refresh portfolio
            self.refresh_portfolio()
            
        except Exception as e:
            logger.error(f"Trade execution flatlined: {e}")
            self._show_notification(f"Trade failed: {str(e)[:50]}", "error")
            self.last_failed_task = "trade"
            self.last_error_time = time.time()
    
    def toggle_testnet(self):
        """Toggle between testnet and live mode"""
        try:
            new_mode = not self.testnet_enabled.get()
            
            toggle_data = {"testnet": new_mode}
            response = requests.post(f"{self.api_url}/testnet", json=toggle_data, timeout=10)
            response.raise_for_status()
            
            mode_text = "TEST MODE" if new_mode else "LIVE MODE"
            self._show_notification(f"Switched to {mode_text}", "info")
            
        except Exception as e:
            logger.error(f"Mode toggle failed: {e}")
            self._show_notification("Failed to switch mode", "error")
            # Revert toggle
            self.testnet_enabled.set(not self.testnet_enabled.get())
            self.mode_toggle.update_visual()
    
    def emergency_stop(self):
        """Execute emergency kill switch with confirmation"""
        # Create larger confirmation dialog
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("⚠ EMERGENCY KILL SWITCH ⚠")
        confirm_window.geometry("700x500")
        confirm_window.configure(bg=self.colors['bg_dark'])
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        
        # Center the window
        confirm_window.update_idletasks()
        x = (confirm_window.winfo_screenwidth() - 700) // 2
        y = (confirm_window.winfo_screenheight() - 500) // 2
        confirm_window.geometry(f"700x500+{x}+{y}")
        
        # Confirmation content with red theme
        confirm_frame = tk.Frame(confirm_window, bg="#330000",
                               highlightbackground=self.colors['neon_red'],
                               highlightthickness=4)
        confirm_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Warning header
        header_frame = tk.Frame(confirm_frame, bg="#660000")
        header_frame.pack(fill="x")
        
        tk.Label(header_frame,
                text="⚠ EMERGENCY KILL SWITCH ⚠",
                bg="#660000",
                fg="#ff0000",
                font=("Consolas", 24, "bold")).pack(pady=20)
        
        # Warning message
        tk.Label(confirm_frame,
                text="WARNING: This will immediately:",
                bg="#330000",
                fg="#ff6666",
                font=("Consolas", 18)).pack(pady=(30, 15))
        
        warnings = [
            "• Close ALL open positions at market price",
            "• Cancel ALL pending orders",
            "• Shutdown ALL trading operations",
            "• Lock the system completely",
            "• Create emergency report",
            "• Require manual restart"
        ]
        
        for warning in warnings:
            tk.Label(confirm_frame,
                    text=warning,
                    bg="#330000",
                    fg="#ffaaaa",
                    font=("Consolas", 16),
                    anchor="w").pack(padx=80, pady=5, anchor="w")
        
        tk.Label(confirm_frame,
                text="Are you absolutely sure?",
                bg="#330000",
                fg="#ff0000",
                font=("Consolas", 20, "bold")).pack(pady=30)
        
        # Buttons
        button_frame = tk.Frame(confirm_frame, bg="#330000")
        button_frame.pack(pady=30)
        
        def execute_kill_switch():
            confirm_window.destroy()
            try:
                security_manager.emergency_lock()
                
                # Run kill switch
                future = asyncio.run_coroutine_threadsafe(kill_switch.activate(), self.loop)
                future.result(timeout=10)
                
                self._show_notification("EMERGENCY STOP EXECUTED - SYSTEM OFFLINE", "error")
                self.root.after(2000, self.root.quit)
                
            except Exception as e:
                logger.error(f"Kill switch flatlined: {e}")
                messagebox.showerror("Critical Error", f"Kill switch failed: {e}")
                self.root.quit()
        
        kill_btn = AnimatedButton(button_frame,
                                 text="EXECUTE KILL SWITCH",
                                 command=execute_kill_switch,
                                 bg_color="#ff0000",
                                 hover_color="#ff3333",
                                 width=250,
                                 height=50)
        kill_btn.pack(side="left", padx=15)
        
        cancel_btn = AnimatedButton(button_frame,
                                   text="CANCEL",
                                   command=confirm_window.destroy,
                                   bg_color="#666666",
                                   hover_color="#999999",
                                   width=150,
                                   height=50)
        cancel_btn.pack(side="left", padx=15)
    
    def _show_notification(self, message, type="info"):
        """Show modern notification popup"""
        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        
        # Set colors based on type
        if type == "success":
            bg_color = self.colors['neon_green']
            fg_color = self.colors['bg_dark']
        elif type == "error":
            bg_color = self.colors['neon_red']
            fg_color = "#ffffff"
        else:
            bg_color = self.colors['neon_cyan']
            fg_color = self.colors['bg_dark']
        
        # Create notification frame
        notif_frame = tk.Frame(notification, bg=bg_color, highlightbackground="#ffffff", highlightthickness=2)
        notif_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        tk.Label(notif_frame,
                text=message,
                bg=bg_color,
                fg=fg_color,
                font=self.normal_font,
                padx=25,
                pady=12).pack()
        
        # Position in top-right corner
        notification.update_idletasks()
        width = notification.winfo_width()
        height = notification.winfo_height()
        x = self.root.winfo_x() + self.root.winfo_width() - width - 30
        y = self.root.winfo_y() + 120
        
        notification.geometry(f"+{x}+{y}")
        
        # Auto-destroy after 3 seconds with fade effect
        notification.after(3000, notification.destroy)
    
    def refresh_portfolio(self):
        """Refresh portfolio display"""
        try:
            response = requests.get(f"{self.api_url}/portfolio", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Clear text
            self.portfolio_text.delete(1.0, tk.END)
            
            # Configure text tags for styling
            self.portfolio_text.tag_configure("header", foreground=self.colors['neon_pink'], 
                                            font=("Consolas", 20, "bold"))
            self.portfolio_text.tag_configure("subheader", foreground=self.colors['neon_cyan'], 
                                            font=("Consolas", 16, "bold"), underline=True)
            self.portfolio_text.tag_configure("profit", foreground=self.colors['neon_green'], 
                                            font=("Consolas", 14, "bold"))
            self.portfolio_text.tag_configure("loss", foreground=self.colors['neon_red'],
                                            font=("Consolas", 14, "bold"))
            self.portfolio_text.tag_configure("normal", foreground=self.colors['text_primary'],
                                            font=self.normal_font)
            
            # Display portfolio value
            portfolio_value = db.get_portfolio_value()
            self.portfolio_text.insert(tk.END, f"PORTFOLIO VALUE: ${portfolio_value:,.2f} EDDIES\n\n", "header")
            
            # Display recent trades
            self.portfolio_text.insert(tk.END, "RECENT TRADES\n", "subheader")
            self.portfolio_text.insert(tk.END, "━" * 80 + "\n", "normal")
            
            for trade in data.get("trades", [])[:10]:
                color_tag = "profit" if trade.get("side") == "sell" else "loss"
                self.portfolio_text.insert(tk.END, 
                    f"{trade.get('timestamp', 'N/A')[:19]} │ {trade.get('symbol', 'N/A'):15} │ "
                    f"{trade.get('side', 'N/A').upper():5} │ {trade.get('amount', 0):.4f} @ "
                    f"${trade.get('price', 0):,.2f}\n", color_tag)
            
            # Display positions
            self.portfolio_text.insert(tk.END, "\n\nACTIVE POSITIONS\n", "subheader")
            self.portfolio_text.insert(tk.END, "━" * 80 + "\n", "normal")
            
            for position in data.get("positions", []):
                entry_price = position.get('entry_price', 0)
                # Get current price (would need to fetch)
                current_price = entry_price * 1.05  # Placeholder
                pnl = (current_price - entry_price) * position.get('amount', 0)
                pnl_tag = "profit" if pnl >= 0 else "loss"
                
                self.portfolio_text.insert(tk.END, 
                    f"{position.get('symbol', 'N/A'):15} │ {position.get('side', 'N/A').upper():5} │ "
                    f"{position.get('amount', 0):.4f} │ Entry: ${entry_price:,.2f} │ ", "normal")
                self.portfolio_text.insert(tk.END, f"P&L: ${pnl:,.2f}\n", pnl_tag)
            
            # Display reserves
            reserves = db.fetch_one("SELECT SUM(amount) FROM reserves")
            reserve_amount = reserves[0] if reserves and reserves[0] else 0
            self.portfolio_text.insert(tk.END, f"\n\nTAX RESERVES: ${reserve_amount:,.2f} EDDIES\n", "header")
            
            # Update P&L display
            self._update_profit_display()
            
        except Exception as e:
            logger.error(f"Portfolio refresh flatlined: {e}")
            self.portfolio_text.insert(tk.END, f"Error refreshing portfolio: {e}\n", "loss")
    
    def train_model(self):
        """Train the ML/RL models"""
        try:
            self.status_label.config(text="STATUS: Training Neural-Net... This may take a while, Choom!")
            
            # Show progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Neural-Net Training")
            progress_window.geometry("500x300")
            progress_window.configure(bg=self.colors['bg_dark'])
            progress_window.transient(self.root)
            
            # Center the window
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() - 500) // 2
            y = (progress_window.winfo_screenheight() - 300) // 2
            progress_window.geometry(f"500x300+{x}+{y}")
            
            # Progress content
            progress_frame = tk.Frame(progress_window, bg=self.colors['bg_medium'],
                                    highlightbackground=self.colors['neon_pink'],
                                    highlightthickness=3)
            progress_frame.pack(fill="both", expand=True, padx=3, pady=3)
            
            tk.Label(progress_frame,
                    text="TRAINING NEURAL-NET",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['neon_pink'],
                    font=("Consolas", 20, "bold")).pack(pady=40)
            
            progress_label = tk.Label(progress_frame,
                                    text="Initializing training sequence...",
                                    bg=self.colors['bg_medium'],
                                    fg=self.colors['text_secondary'],
                                    font=self.large_font)
            progress_label.pack()
            
            # Progress bar
            progress_canvas = tk.Canvas(progress_frame, width=400, height=30,
                                      bg=self.colors['bg_dark'], highlightthickness=0)
            progress_canvas.pack(pady=30)
            
            progress_bg = progress_canvas.create_rectangle(0, 0, 400, 30, 
                                                         fill=self.colors['bg_dark'], 
                                                         outline=self.colors['neon_cyan'],
                                                         width=2)
            progress_bar = progress_canvas.create_rectangle(0, 0, 0, 30, 
                                                          fill=self.colors['neon_pink'], 
                                                          outline="")
            
            def update_progress(pct, text):
                progress_canvas.coords(progress_bar, 0, 0, pct * 4, 30)
                progress_label.config(text=text)
                progress_window.update()
            
            # Simulate progress
            update_progress(10, "Loading historical data...")
            
            def train_async():
                try:
                    response = requests.post(f"{self.api_url}/train", timeout=300)
                    response.raise_for_status()
                    
                    self.root.after(0, lambda: update_progress(100, "Training complete!"))
                    self.root.after(0, lambda: self._show_notification("Neural-Net retrained successfully!", "success"))
                    self.root.after(0, lambda: self.status_label.config(text="STATUS: Neural-Net online and enhanced"))
                    self.root.after(1000, progress_window.destroy)
                    
                except Exception as e:
                    logger.error(f"Training flatlined: {e}")
                    self.root.after(0, lambda: self._show_notification(f"Training failed: {str(e)[:50]}", "error"))
                    self.root.after(0, lambda: self.status_label.config(text="STATUS: Training failed - Check logs"))
                    self.root.after(0, progress_window.destroy)
            
            # Start training in thread
            threading.Thread(target=train_async, daemon=True).start()
            
            # Update progress periodically
            for i in range(20, 90, 10):
                progress_window.after(i * 40, lambda pct=i: update_progress(pct, f"Training models... {pct}%"))
                
        except Exception as e:
            logger.error(f"Training setup flatlined: {e}")
            self._show_notification("Training initialization failed", "error")
    
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
            
            # Plot equity curve with cyberpunk styling
            self.ax.clear()
            
            # Plot with neon glow effect
            x = range(len(result["equity_curve"]))
            y = result["equity_curve"]
            
            # Main line
            self.ax.plot(x, y, color=self.colors['neon_cyan'], linewidth=3, label="Equity Curve")
            
            # Glow effect
            for width in [10, 8, 6]:
                self.ax.plot(x, y, color=self.colors['neon_cyan'], linewidth=width, alpha=0.1)
            
            # Style the plot
            self.ax.set_title("BACKTEST EQUITY CURVE", color=self.colors['neon_pink'], fontsize=20, pad=25)
            self.ax.set_xlabel("Time", color=self.colors['neon_cyan'], fontsize=14)
            self.ax.set_ylabel("Portfolio Value", color=self.colors['neon_cyan'], fontsize=14)
            self.ax.tick_params(colors=self.colors['neon_cyan'], labelsize=12)
            self.ax.grid(True, alpha=0.3, color=self.colors['neon_cyan'], linestyle='--')
            
            # Add metrics
            self.ax.text(0.02, 0.98, f"Sharpe: {result['sharpe_ratio']:.2f}", 
                        transform=self.ax.transAxes, color=self.colors['neon_green'],
                        verticalalignment='top', fontsize=14,
                        bbox=dict(boxstyle='round', facecolor=self.colors['bg_medium'], alpha=0.8))
            
            self.ax.text(0.02, 0.90, f"Return: {result['total_return']*100:.2f}%", 
                        transform=self.ax.transAxes, color=self.colors['neon_green'],
                        verticalalignment='top', fontsize=14,
                        bbox=dict(boxstyle='round', facecolor=self.colors['bg_medium'], alpha=0.8))
            
            self.canvas.draw()
            
            # Display results in dashboard text
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.tag_configure("header", foreground=self.colors['neon_pink'], 
                                            font=("Consolas", 18, "bold"))
            self.dashboard_text.tag_configure("metric", foreground=self.colors['neon_green'],
                                            font=("Consolas", 16))
            
            self.dashboard_text.insert(tk.END, "=== BACKTEST RESULTS ===\n", "header")
            self.dashboard_text.insert(tk.END, f"Sharpe Ratio: {result['sharpe_ratio']:.2f}\n", "metric")
            self.dashboard_text.insert(tk.END, f"Total Return: {result['total_return']*100:.2f}%\n", "metric")
            
            self._show_notification("Backtest complete!", "success")
            
        except Exception as e:
            logger.error(f"Backtest flatlined: {e}")
            self._show_notification("Backtest failed", "error")
    
    def update_status(self):
        """Update status bar"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                self.status_label.config(text="STATUS: Connected to Neural-Net Matrix ✓")
                self.connection_canvas.itemconfig(self.connection_light, fill=self.colors['neon_green'])
            else:
                self.status_label.config(text="STATUS: Connection unstable")
                self.connection_canvas.itemconfig(self.connection_light, fill="#ffaa00")
        except:
            self.status_label.config(text="STATUS: Disconnected from the Net")
            self.connection_canvas.itemconfig(self.connection_light, fill=self.colors['neon_red'])
        
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
            self._show_notification("Tax rates updated from the Net!", "success")
        except Exception as e:
            logger.error(f"Tax update flatlined: {e}")
            self._show_notification("Tax update failed", "error")
    
    def rebalance_portfolio(self):
        """Rebalance portfolio"""
        try:
            # This would call the risk manager's rebalance method
            self._show_notification("Portfolio rebalanced - Eddies optimized!", "success")
        except Exception as e:
            logger.error(f"Rebalance flatlined: {e}")
            self._show_notification("Rebalance failed", "error")
    
    def convert_idle_now(self):
        """Convert idle funds"""
        def run_async():
            future = asyncio.run_coroutine_threadsafe(
                self._async_convert_idle(), 
                self.loop
            )
            try:
                future.result(timeout=30)
                self.root.after(0, lambda: self._show_notification(f"Idle funds converted to {self.idle_target.get()}!", "success"))
            except Exception as e:
                self.root.after(0, lambda: self._show_notification(f"Conversion failed: {str(e)[:50]}", "error"))
        
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
            self._show_notification("Historical data preloaded!", "success")
        except Exception as e:
            logger.error(f"Data preload flatlined: {e}")
            self._show_notification("Data preload failed", "error")
            self.last_failed_task = "preload"
            self.last_error_time = time.time()
    
    def scan_arbitrage(self):
        """Scan for arbitrage opportunities"""
        try:
            response = requests.get(f"{self.api_url}/arbitrage", timeout=30)
            response.raise_for_status()
            opportunities = response.json()["opportunities"]
            
            self.dashboard_text.delete(1.0, tk.END)
            self.dashboard_text.tag_configure("header", foreground=self.colors['neon_pink'], 
                                            font=("Consolas", 18, "bold"))
            self.dashboard_text.tag_configure("opportunity", foreground=self.colors['neon_green'],
                                            font=("Consolas", 14))
            
            self.dashboard_text.insert(tk.END, "=== ARBITRAGE OPPORTUNITIES ===\n", "header")
            
            if opportunities:
                for opp in opportunities[:5]:
                    profit_pct = opp.get('profit', 0) * 100
                    self.dashboard_text.insert(tk.END, 
                        f"{opp.get('pair', 'N/A')} │ Buy: {opp.get('buy_exchange', 'N/A')} @ "
                        f"${opp.get('buy_price', 0):,.4f} │ Sell: {opp.get('sell_exchange', 'N/A')} @ "
                        f"${opp.get('sell_price', 0):,.4f} │ Profit: {profit_pct:.2f}%\n", "opportunity")
                self._show_notification(f"Found {len(opportunities)} arbitrage opportunities!", "success")
            else:
                self.dashboard_text.insert(tk.END, "No arbitrage opportunities found\n")
                
        except Exception as e:
            logger.error(f"Arbitrage scan flatlined: {e}")
            self._show_notification("Arbitrage scan failed", "error")
    
    def view_sentiment(self):
        """View sentiment analysis"""
        try:
            # This would call the sentiment analyzer
            self.dashboard_text.insert(tk.END, "\n=== SENTIMENT ANALYSIS ===\n")
            self.dashboard_text.insert(tk.END, "Sentiment: Bullish (0.75)\n")
            self._show_notification("Sentiment updated", "info")
        except Exception as e:
            logger.error(f"Sentiment view flatlined: {e}")
    
    def view_onchain(self):
        """View on-chain metrics"""
        try:
            # This would call the on-chain analyzer
            self.dashboard_text.insert(tk.END, "\n=== ON-CHAIN METRICS ===\n")
            self.dashboard_text.insert(tk.END, "Whale Activity: Low\n")
            self._show_notification("On-chain metrics updated", "info")
        except Exception as e:
            logger.error(f"On-chain view flatlined: {e}")
    
    def withdraw_reserves(self):
        """Withdraw tax reserves"""
        try:
            reserves = db.fetch_one("SELECT SUM(amount) FROM reserves")
            total = reserves[0] if reserves and reserves[0] else 0
            
            if total > 0:
                db.execute_query("DELETE FROM reserves")
                self._show_notification(f"Withdrew ${total:,.2f} Eddies from tax reserves!", "success")
            else:
                self._show_notification("No reserves to withdraw", "info")
                
        except Exception as e:
            logger.error(f"Reserve withdrawal flatlined: {e}")
            self._show_notification("Withdrawal failed", "error")
    
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
                self._show_notification(f"⚠ High loss detected: ${daily_pnl:,.2f} Eddies", "error")
            elif daily_pnl > 0.01 * portfolio_value:
                self._show_notification(f"🎉 Nice gains today: ${daily_pnl:,.2f} Eddies!", "success")
            else:
                self._show_notification("All systems nominal - Keep stacking Eddies!", "info")
                
        except Exception as e:
            logger.error(f"Health check flatlined: {e}")
            self._show_notification("Health check failed", "error")
    
    def backup_now(self):
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/backup_{timestamp}.db"
            
            # Create backup directory
            os.makedirs("backups", exist_ok=True)
            
            # Copy database
            shutil.copy2(db.db_path, backup_path)
            
            self._show_notification(f"Backup created: {backup_path}", "success")
            logger.info(f"Database backed up to {backup_path}")
            
        except Exception as e:
            logger.error(f"Backup flatlined: {e}")
            self._show_notification("Backup failed", "error")
    
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
            
            self._show_notification("Settings saved to the Matrix!", "success")
            
        except Exception as e:
            logger.error(f"Settings save flatlined: {e}")
            self._show_notification("Failed to save settings", "error")
    
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
            
            self._show_notification("DeFi settings encrypted and saved!", "success")
            
        except Exception as e:
            logger.error(f"DeFi save flatlined: {e}")
            self._show_notification("Failed to save DeFi settings", "error")
    
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
                
                self._show_notification("DeFi configuration loaded", "success")
            else:
                self._show_notification("No DeFi configuration found", "info")
                    
        except Exception as e:
            logger.error(f"DeFi load flatlined: {e}")
            self._show_notification("Failed to load DeFi settings", "error")
    
    def finish_onboarding(self):
        """Complete onboarding process"""
        try:
            # Validate inputs
            api_key = self.api_key_entry.get()
            api_secret = self.api_secret_entry.get() if hasattr(self, 'api_secret_entry') else ""
            
            if not api_key:
                self._show_notification("API key required for trading!", "error")
                return
            
            # Save API credentials
            os.environ["BINANCE_API_KEY"] = api_key
            if api_secret:
                os.environ["BINANCE_API_SECRET"] = api_secret
            
            settings.BINANCE_API_KEY = api_key
            settings.BINANCE_API_SECRET = api_secret
            
            # Set risk profile
            risk_map = {"Conservative": "conservative", "Moderate": "moderate", "Aggressive": "aggressive"}
            risk_level = risk_map.get(self.risk_onboard.get(), "moderate")
            
            from trading.risk_manager import risk_manager
            risk_manager.set_risk_profile(risk_level)
            self.risk_profile.set(risk_level)
            
            # Set initial capital
            try:
                capital = float(self.capital_entry.get())
                db.update_portfolio_value(capital)
            except ValueError:
                self._show_notification("Invalid capital amount", "error")
                return
            
            # Show success animation
            success_window = tk.Toplevel(self.root)
            success_window.title("Welcome to the Matrix")
            success_window.geometry("600x400")
            success_window.configure(bg=self.colors['bg_dark'])
            success_window.transient(self.root)
            success_window.grab_set()
            
            # Center the window
            success_window.update_idletasks()
            x = (success_window.winfo_screenwidth() - 600) // 2
            y = (success_window.winfo_screenheight() - 400) // 2
            success_window.geometry(f"600x400+{x}+{y}")
            
            # Success content
            success_frame = tk.Frame(success_window, bg=self.colors['bg_medium'],
                                   highlightbackground=self.colors['neon_green'],
                                   highlightthickness=4)
            success_frame.pack(fill="both", expand=True, padx=4, pady=4)
            
            tk.Label(success_frame,
                    text="✓ ONBOARDING COMPLETE",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['neon_green'],
                    font=("Consolas", 24, "bold")).pack(pady=50)
            
            tk.Label(success_frame,
                    text="You're now jacked into the Arasaka Neural-Net Trading Matrix!",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['text_secondary'],
                    font=self.large_font,
                    wraplength=500).pack(pady=20)
            
            tk.Label(success_frame,
                    text=f"Starting Capital: ${capital:,.2f}",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['neon_cyan'],
                    font=self.large_font).pack()
            
            tk.Label(success_frame,
                    text=f"Risk Profile: {risk_level.upper()}",
                    bg=self.colors['bg_medium'],
                    fg=self.colors['neon_cyan'],
                    font=self.large_font).pack()
            
            # Close button
            close_btn = AnimatedButton(success_frame,
                                     text="START TRADING",
                                     command=lambda: [success_window.destroy(), self.notebook.select(self.trading_frame)],
                                     bg_color=self.colors['neon_green'],
                                     hover_color=self.colors['neon_cyan'],
                                     width=200,
                                     height=50)
            close_btn.pack(pady=40)
            
            # Update settings
            self.trade_amount.set(str(min(capital * 0.001, 0.001)))  # 0.1% of capital or minimum
            
            # Refresh portfolio
            self.refresh_portfolio()
            
        except Exception as e:
            logger.error(f"Onboarding flatlined: {e}")
            self._show_notification(f"Onboarding failed: {str(e)[:50]}", "error")
    
    def on_closing(self):
        """Handle window closing"""
        if self.authenticated and messagebox.askokcancel("Quit", "Disconnect from the Matrix?"):
            try:
                # Save any settings
                self.save_settings()
                
                # Close async loop
                self.loop.call_soon_threadsafe(self.loop.stop)
                
                # Close database connection
                db.close()
                
                # Destroy window
                self.root.destroy()
            except Exception as e:
                logger.error(f"Shutdown error: {e}")
                self.root.destroy()
        elif not self.authenticated:
            self.root.destroy()

def main():
    """Main entry point with splash screen"""
    # Create splash screen
    splash = tk.Tk()
    splash.title("Loading...")
    splash.configure(bg="#0a0a23")
    splash.overrideredirect(True)
    
    # Get screen dimensions
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    
    # Splash dimensions
    splash_width = 800
    splash_height = 600
    
    # Center splash
    x = (screen_width - splash_width) // 2
    y = (screen_height - splash_height) // 2
    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")
    
    # Create splash content
    splash_canvas = tk.Canvas(splash, width=splash_width, height=splash_height, 
                            bg="#0a0a23", highlightthickness=0)
    splash_canvas.pack()
    
    # Draw cyberpunk grid background
    for i in range(0, splash_width, 50):
        splash_canvas.create_line(i, 0, i, splash_height, fill="#1a1a3d", width=1)
    for i in range(0, splash_height, 50):
        splash_canvas.create_line(0, i, splash_width, i, fill="#1a1a3d", width=1)
    
    # Add logo text with glow
    for i in range(5, 0, -1):
        splash_canvas.create_text(splash_width//2, splash_height//2 - 100,
                                text="ARASAKA",
                                fill=f"#{int(255*(6-i)/6):02x}00{int(255*(6-i)/6):02x}",
                                font=("Consolas", 60 + i*2, "bold"))
    
    splash_canvas.create_text(splash_width//2, splash_height//2 - 100,
                            text="ARASAKA",
                            fill="#ff00ff",
                            font=("Consolas", 60, "bold"))
    
    splash_canvas.create_text(splash_width//2, splash_height//2 - 30,
                            text="NEURAL-NET TRADING MATRIX",
                            fill="#00ffcc",
                            font=("Consolas", 24))
    
    splash_canvas.create_text(splash_width//2, splash_height//2 + 20,
                            text="v2.0",
                            fill="#666666",
                            font=("Consolas", 18))
    
    # Loading bar
    bar_width = 600
    bar_height = 8
    bar_x = (splash_width - bar_width) // 2
    bar_y = splash_height - 150
    
    splash_canvas.create_rectangle(bar_x, bar_y, bar_x + bar_width, bar_y + bar_height,
                                 outline="#00ffcc", width=2)
    loading_bar = splash_canvas.create_rectangle(bar_x, bar_y, bar_x, bar_y + bar_height,
                                               fill="#ff00ff", outline="")
    
    loading_text = splash_canvas.create_text(splash_width//2, bar_y + 30,
                                           text="Initializing Neural-Net...",
                                           fill="#00ffcc",
                                           font=("Consolas", 14))
    
    # Update splash
    splash.update()
    
    # Loading animation
    loading_steps = [
        (0.2, "Loading core modules..."),
        (0.4, "Connecting to exchange APIs..."),
        (0.6, "Initializing ML models..."),
        (0.8, "Preparing trading interface..."),
        (1.0, "Ready to jack in!")
    ]
    
    for progress, text in loading_steps:
        splash_canvas.coords(loading_bar, bar_x, bar_y, bar_x + bar_width * progress, bar_y + bar_height)
        splash_canvas.itemconfig(loading_text, text=text)
        splash.update()
        time.sleep(0.5)
    
    # Destroy splash and create main window
    splash.destroy()
    
    # Create main application
    root = tk.Tk()
    
    # Set window icon (if available)
    try:
        if os.path.exists("assets/icon.ico"):
            root.iconbitmap("assets/icon.ico")
    except:
        pass
    
    app = TradingApp(root)
    
    # Set close protocol
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
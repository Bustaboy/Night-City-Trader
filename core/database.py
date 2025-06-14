# core/database.py
"""
Arasaka Database Core - Handles all data operations in the Neural-Net Trading Matrix
"""
import sqlite3
from datetime import datetime
import threading
import os

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_path = os.getenv("DATABASE_URL", "sqlite:///local_trading.db").replace("sqlite:///", "")
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.init_tables()
            self.initialized = True

    def init_tables(self):
        """Initialize all database tables for the Trading Matrix"""
        # Main trading tables
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                amount REAL,
                price REAL,
                fee REAL,
                leverage REAL,
                timestamp TEXT
            )
        """)
        
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                amount REAL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                timestamp TEXT
            )
        """)
        
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS market_data (
                symbol TEXT,
                timestamp INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL
            )
        """)
        
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS historical_data (
                symbol TEXT,
                timestamp INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (symbol, timestamp)
            )
        """)
        
        # Analysis tables
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS market_regimes (
                timestamp INTEGER PRIMARY KEY,
                regime TEXT
            )
        """)
        
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS seasonality_patterns (
                symbol TEXT,
                period TEXT,
                mean_return REAL,
                volatility REAL,
                PRIMARY KEY (symbol, period)
            )
        """)
        
        # Financial tables
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS reserves (
                trade_id TEXT,
                amount REAL,
                timestamp TEXT,
                PRIMARY KEY (trade_id)
            )
        """)
        
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS tax_rates (
                country TEXT PRIMARY KEY,
                rate REAL
            )
        """)
        
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value REAL,
                timestamp TEXT
            )
        """)
        
        # Create indexes for performance
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_symbol ON historical_data(symbol)")
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_timestamp ON market_data(timestamp)")

    def execute_query(self, query, params=()):
        """Execute a query with thread safety"""
        with self._lock:
            self.cursor.execute(query, params)
            self.conn.commit()

    def executemany(self, query, params_list):
        """Execute many queries for batch operations"""
        with self._lock:
            self.cursor.executemany(query, params_list)
            self.conn.commit()

    def fetch_all(self, query, params=()):
        """Fetch all results from a query"""
        with self._lock:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()

    def fetch_one(self, query, params=()):
        """Fetch one result from a query"""
        with self._lock:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()

    def store_historical_data(self, symbol, data):
        """Store historical OHLCV data for a symbol"""
        if not data:
            return
            
        rows = []
        for row in data:
            if len(row) >= 6:
                rows.append((symbol, row[0], row[1], row[2], row[3], row[4], row[5]))
        
        if rows:
            self.executemany(
                """
                INSERT OR REPLACE INTO historical_data
                (symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows
            )

    def store_seasonality_pattern(self, symbol, period, mean_return, volatility):
        """Store seasonality patterns for market analysis"""
        self.execute_query(
            """
            INSERT OR REPLACE INTO seasonality_patterns
            (symbol, period, mean_return, volatility)
            VALUES (?, ?, ?, ?)
            """,
            (symbol, period, mean_return, volatility)
        )

    def update_portfolio_value(self, value):
        """Update portfolio value in Eddies"""
        try:
            self.execute_query(
                "INSERT INTO portfolio (value, timestamp) VALUES (?, ?)",
                (value, datetime.now().isoformat())
            )
        except Exception as e:
            print(f"Portfolio update flatlined: {e}")

    def get_portfolio_value(self):
        """Get current portfolio value in Eddies"""
        try:
            result = self.fetch_one("SELECT value FROM portfolio ORDER BY timestamp DESC LIMIT 1")
            return result[0] if result else 100  # Default 100 Eddies
        except Exception as e:
            print(f"Portfolio fetch flatlined: {e}")
            return 100

    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

# Singleton instance
db = DatabaseManager()

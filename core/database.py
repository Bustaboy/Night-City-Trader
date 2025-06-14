# core/database.py
import sqlite3
from config.settings import settings

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(settings.DATABASE_URL, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_tables()

    def init_tables(self):
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
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS reserves (
                trade_id TEXT,
                amount REAL,
                timestamp TEXT,
                PRIMARY KEY (trade_id)
            )
        """)

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def store_historical_data(self, symbol, data):
        for row in data:
            self.execute_query(
                """
                INSERT OR REPLACE INTO historical_data
                (symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (symbol, row[0], row[1], row[2], row[3], row[4], row[5])
            )

    def store_seasonality_pattern(self, symbol, period, mean_return, volatility):
        self.execute_query(
            """
            INSERT OR REPLACE INTO seasonality_patterns
            (symbol, period, mean_return, volatility)
            VALUES (?, ?, ?, ?)
            """,
            (symbol, period, mean_return, volatility)
        )

    def close(self):
        self.conn.close()

db = DatabaseManager()

# scripts/setup_database.py
from core.database import db

def init_database():
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            side TEXT,
            amount REAL,
            price REAL,
            fee REAL,
            timestamp TEXT
        )
    """)
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS positions (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            side TEXT,
            amount REAL,
            entry_price REAL,
            timestamp TEXT
        )
    """)
    db.execute_query("""
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
    print("Database initialized")

if __name__ == "__main__":
    init_database()

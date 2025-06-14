# core/database.py
import sqlite3
from config.settings import settings

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(settings.DATABASE_URL, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()

db = DatabaseManager()

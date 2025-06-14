import sqlite3
from config.settings import settings

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(settings.DATABASE_URL)
        self.cursor = self.conn.cursor()

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

db = DatabaseManager()

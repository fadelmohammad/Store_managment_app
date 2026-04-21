# connection.py

import sqlite3


class DatabaseConnection:
    def __init__(self, db_path="store.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def get_connection(self):
        return self.conn

    def close(self):
        self.conn.close()

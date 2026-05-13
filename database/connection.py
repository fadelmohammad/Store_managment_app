# connection.py

import sqlite3


class DatabaseConnection:
    def __init__(self, db_path="store.db"):
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Performance PRAGMAs for 1000+ products scale
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.conn.execute("PRAGMA cache_size = -10000")  # ~100MB cache
        except Exception:
            if self.conn is not None:
                self.conn.close()
            raise

    def get_connection(self):
        return self.conn

    def close(self):
        self.conn.close()

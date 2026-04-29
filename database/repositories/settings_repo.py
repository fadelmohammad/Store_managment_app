# settings_repo.py

class SettingRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, key, default):
        """Fetches a setting value from the database."""
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set(self, key, value):
        """Saves a setting value to the database."""
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
        self.conn.commit()
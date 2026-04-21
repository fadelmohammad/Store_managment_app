# settings_repo.py

def get_setting(self, key, default):
    """Fetches a setting value from the database."""
    # Ensure settings table exists
    self.cursor.execute(
        "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)"
    )
    row = self.cursor.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else default

def set_setting(self, key, value):
    """Saves a setting value to the database."""
    self.cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, str(value)),
    )
    self.conn.commit()
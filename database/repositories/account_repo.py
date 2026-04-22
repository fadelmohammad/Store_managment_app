# account_repo.py

class AccountRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_role(self, role):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE role = ? ORDER BY name", (role,)
        ).fetchall()

    def add(self, name, phone, address, role):
        with self.conn:
            conn = self.conn.execute(
                "INSERT INTO accounts (name, phone, address, role) VALUES (?, ?, ?, ?)",
                (name, phone, address, role),
            )
            return conn.lastrowid
    def delete(self, account_id):
        with self.conn:
            self.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
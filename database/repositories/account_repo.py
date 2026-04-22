# account_repo.py

def get_by_role(self, role):
    self.conn.execute(
        "SELECT * FROM accounts WHERE role = ? ORDER BY name", (role,)
    )
    return self.conn.fetchall()

def add(self, name, phone, address, role):
    with self.conn:
        conn = self.conn.execute(
            "INSERT INTO accounts (name, phone, address, role) VALUES (?, ?, ?, ?)",
            (name, phone, address, role),
        )
        return conn.lastrowid
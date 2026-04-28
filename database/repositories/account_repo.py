# account_repo.py

class AccountRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, account_id):
        """Fetches account details by ID."""
        query = "SELECT * FROM accounts WHERE id = ?"
        cursor = self.conn.execute(query, (account_id,))
        return cursor.fetchone()

    def fetch_accounts(self, search=None, role=None):
        query = "SELECT id, name, role, phone, balance FROM accounts WHERE 1=1"
        params = []

        if role and role != "All":
            query += " AND role = ?"
            params.append(role)

        if search:
            query += " AND (name LIKE ? OR phone LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        return self.conn.execute(query, params).fetchall()

    def add(self, name, role, phone, email, address, balance):

        query = """
            INSERT INTO accounts (name, role, phone, email, address, balance)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (name, role, phone, email, address, balance)

        cursor = self.conn.execute(query, params)
        return cursor.lastrowid

    def update(self, account_id, data):
        """Executes the update query on the database."""
        query = """
            UPDATE accounts 
            SET name=?, role=?, phone=?, email=?, address=? 
            WHERE id=?
        """
        params = (
            data['name'], data['role'], data['phone'], 
            data['email'], data['address'], account_id
        )
        
        self.conn.execute(query, params)

    def delete(self, account_id):
        """Removes the account record from the database."""
        query = "DELETE FROM accounts WHERE id = ?"
        self.conn.execute(query, (account_id,))


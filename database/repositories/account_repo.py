# account_repo.py

class AccountRepository(BaseRepository):
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, account_id):
        """Fetches account details by ID."""
        query = "SELECT * FROM accounts WHERE id = ?"
        cursor = self._execute(query, (account_id,))
        return cursor.fetchone()

    def get_by_role(self, role):
        """Fetches account details by ROLE."""
        query = "SELECT * FROM accounts WHERE role = ? ORDER BY name"

        cursor = self._execute(query, (role,))

        return cursor.fetchall

    def add(self, name, role, phone, email, address):
        cursor = self._execute(
            """
            INSERT INTO accounts (name, role, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, role, phone, email, address),
        )
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
        
        self._execute(query, params)

    def delete(self, account_id):
        """Removes the account record from the database."""
        query = "DELETE FROM accounts WHERE id = ?"
        self._execute(query, (account_id,))


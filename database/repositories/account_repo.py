# account_repo.py

class AccountRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, account_id):
        """Fetches account details by ID."""
        return self.conn.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()


    def get_by_role(self, role):
        """Fetches account details by ROLE."""
        try:
            results = self.conn.execute(
                "SELECT * FROM accounts WHERE role = ? ORDER BY name", (role,)
            ).fetchall()
            
            print(f"🔍 get_by_role('{role}'): found {len(results)} accounts")
            
            # Convert to list of dictionaries for easier access
            formatted = []
            for row in results:
                if hasattr(row, 'keys'):
                    formatted.append(dict(row))
                else:
                    formatted.append({
                        "id": row[0],
                        "name": row[1],
                        "role": row[2],
                        "phone": row[3] if len(row) > 3 else "",
                        "email": row[4] if len(row) > 4 else "",
                        "address": row[5] if len(row) > 5 else "",
                        "balance": row[6] if len(row) > 6 else 0
                    })
            return formatted
        except Exception as e:
            print(f"❌ Error in get_by_role: {e}")
            return []

    def add(self, name, role, phone, email, address):
        with self.conn:
            cursor = self.conn.execute(
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
        
        with self.conn:
            self.conn.execute(query, params)

    def delete(self, account_id):
        """Removes the account record from the database."""
        with self.conn:
            self.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))


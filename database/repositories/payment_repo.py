# payment_repo.py


class PaymentRepository:
    def __init__(self, conn):
        self.conn = conn

    def add_payment(self, account_id, amount, payment_type, payment_method=None, 
                   reference_number=None, notes=None, created_by=None):
        """Add a new payment record."""
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO payments 
                (account_id, amount, payment_type, payment_method, reference_number, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (account_id, amount, payment_type, payment_method, reference_number, notes, created_by)
            )
            return cursor.lastrowid

    def get_payments_by_account(self, account_id, limit=None):
        """Get all payments for a specific account."""
        query = """
            SELECT p.*, u.username as created_by_username
            FROM payments p
            LEFT JOIN users u ON p.created_by = u.id
            WHERE p.account_id = ?
            ORDER BY p.date DESC
        """
        params = [account_id]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        results = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in results]

    def get_payment_by_id(self, payment_id):
        """Get a specific payment by ID."""
        return self.conn.execute(
            """
            SELECT p.*, u.username as created_by_username
            FROM payments p
            LEFT JOIN users u ON p.created_by = u.id
            WHERE p.id = ?
            """,
            (payment_id,)
        ).fetchone()

    def get_all_payments(self, payment_type=None, date_from=None, date_to=None, limit=None):
        """Get all payments with optional filters."""
        query = """
            SELECT p.*, a.name as account_name, u.username as created_by_username
            FROM payments p
            LEFT JOIN accounts a ON p.account_id = a.id
            LEFT JOIN users u ON p.created_by = u.id
            WHERE 1=1
        """
        params = []
        
        if payment_type:
            query += " AND p.payment_type = ?"
            params.append(payment_type)
            
        if date_from:
            query += " AND p.date >= ?"
            params.append(date_from)
            
        if date_to:
            query += " AND p.date <= ?"
            params.append(date_to)
            
        query += " ORDER BY p.date DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        results = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in results]

    def delete_payment(self, payment_id):
        """Delete a payment record."""
        with self.conn:
            self.conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
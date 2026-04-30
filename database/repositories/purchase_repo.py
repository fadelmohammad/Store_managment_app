# database/repositories/purchase_repo.py

class PurchaseRepository:
    def __init__(self, conn):
        self.conn = conn

    def _execute(self, query, params=None):
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self.conn.commit()
        return cursor

    def create_invoice(self, partner_id, total_usd, tax, discount, payment_method):
        """Create purchase invoice"""
        cursor = self._execute("""
            INSERT INTO invoices (type, date, partner_id, total, tax, discount, payment_method, status) 
            VALUES ('PURCHASE', datetime('now'), ?, ?, ?, ?, ?, 'Completed')
        """, (partner_id, total_usd, tax, discount, payment_method))
        return cursor.lastrowid

    def add_invoice_item(self, invoice_id, product_id, quantity, price):
        """Add item to invoice"""
        self._execute("""
            INSERT INTO invoice_items (invoice_id, product_id, quantity, price) 
            VALUES (?, ?, ?, ?)
        """, (invoice_id, product_id, quantity, price))

    def update_account_balance(self, partner_id, total_usd):
        """Update supplier account balance"""
        self._execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (total_usd, partner_id)
        )

    def begin_transaction(self):
        self.conn.execute("BEGIN")

    def commit_transaction(self):
        self.conn.commit()

    def rollback_transaction(self):
        self.conn.rollback()
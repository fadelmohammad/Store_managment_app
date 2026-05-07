# database/repositories/purchase_repo.py


class PurchaseRepository:
    def __init__(self, conn):
        self.conn = conn

    def create_invoice(self, partner_id, total_usd, tax, discount, payment_method):
        cursor = self.conn.execute("""
            INSERT INTO invoices (type, date, partner_id, total, tax, discount, payment_method, status)
            VALUES ('PURCHASE', datetime('now'), ?, ?, ?, ?, ?, 'Completed')
        """, (partner_id, total_usd, tax, discount, payment_method))
        return cursor.lastrowid

    def add_invoice_item(self, invoice_id, product_id, quantity, price):
        self.conn.execute("""
            INSERT INTO invoice_items (invoice_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (invoice_id, product_id, quantity, price))

    def update_account_balance(self, partner_id, amount):
        self.conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, partner_id),
        )

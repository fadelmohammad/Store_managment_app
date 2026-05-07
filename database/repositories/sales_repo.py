# database/repositories/sales_repo.py


class SalesRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_product(self, product_id):
        return self.conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()

    def create_invoice(self, inv_type, partner_id, total_usd, total_syp, exchange_rate, tax, discount, payment_method):
        cursor = self.conn.execute(
            """INSERT INTO invoices (type, date, partner_id, total, total_syp, rate_at_time, tax, discount, payment_method, status)
               VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, 'Completed')""",
            (inv_type, partner_id, total_usd, total_syp, exchange_rate, tax, discount, payment_method),
        )
        return cursor.lastrowid

    def add_invoice_item(self, invoice_id, product_id, quantity, price):
        self.conn.execute(
            "INSERT INTO invoice_items (invoice_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
            (invoice_id, product_id, quantity, price),
        )

    def update_product_stock(self, product_id, delta):
        self.conn.execute(
            "UPDATE products SET quantity = quantity + ? WHERE id = ?",
            (delta, product_id),
        )

    def insert_stock_movement(self, product_id, movement_type, quantity, reason):
        self.conn.execute(
            "INSERT INTO stock_movements (product_id, movement_type, quantity, reason, date) VALUES (?, ?, ?, ?, datetime('now'))",
            (product_id, movement_type, quantity, reason),
        )

    def update_account_balance(self, account_id, amount):
        self.conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, account_id),
        )

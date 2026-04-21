# File: services/purchase_service.py

class PurchaseService:
    def __init__(self, db, ledger_service):
        self.db = db
        self.ledger = ledger_service

    def process_purchase(self, cart, partner_id, exchange_rate, payment_method="Cash", tax_pct=0, discount_pct=0):
        """
        Handles the end-to-end purchase workflow:
        Calculates totals, updates stock, records the invoice, and creates ledger entries.
        Includes exchange_rate for historical tracking.
        """
        if not cart:
            raise Exception("Cart is empty")

        try:
            # Start transaction for data integrity
            self.db.conn.execute("BEGIN")

            subtotal = 0.0
            for item in cart:
                if item: 
                    subtotal += item["price"] * item["qty"]

            tax = subtotal * tax_pct
            discount = subtotal * discount_pct
            total_usd = (subtotal - discount) + tax

            # 1. Create Purchase Invoice
            invoice_id = self.db.cursor.execute(
                """INSERT INTO invoices (type, date, partner_id, total, tax, discount, payment_method, status) 
                   VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?)""",
                ("PURCHASE", partner_id, total_usd, tax, discount, payment_method, "Completed")
            ).lastrowid

            # 2. Update Stock, Average Cost, and Movements
            for item in cart:
                if not item: continue

                # Update the Weighted Average Cost (stored in USD)
                self.db.update_weighted_average_cost(item["id"], item["qty"], item["price"])

                # Add to invoice items
                self.db.cursor.execute(
                    "INSERT INTO invoice_items (invoice_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                    (invoice_id, item["id"], item["qty"], item["price"])
                )

                # Update physical stock
                self.db.update_stock_with_log(
                    product_id=item["id"],
                    change=item["qty"],
                    m_type="IN",
                    reason=f"Purchase Invoice #{invoice_id} (Rate: {exchange_rate:,.0f} SYP)"
                )

            # 3. Handle Accounting Ledger based on Payment Method
            ledger_lines = [
                {"account": "Inventory", "debit": total_usd, "credit": 0}
            ]

            if payment_method == "Cash":
                ledger_lines.append({"account": "Cash", "debit": 0, "credit": total_usd})
            else:
                ledger_lines.append({"account": "Accounts Payable", "debit": 0, "credit": total_usd})
                self.db.cursor.execute(
                    "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                    (total_usd, partner_id)
                )

            self.ledger.create_entry(
                description=f"Purchase Invoice #{invoice_id} @ {exchange_rate:,.0f} SYP",
                reference_id=invoice_id,
                lines=ledger_lines
            )

            self.db.conn.commit()
            return invoice_id, total_usd

        except Exception as e:
            self.db.conn.rollback()
            raise e

    def pay_partner_balance(self, partner_id, amount, payment_account="Cash"):
        """
        Used for paying off a debt to a supplier later on.
        """
        try:
            self.db.conn.execute("BEGIN")

            # Update the unified accounts balance
            self.db.cursor.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (amount, partner_id)
            )

            # Create Ledger Entry
            self.ledger.create_entry(
                description=f"Payment to Partner ID: {partner_id}",
                reference_id=partner_id,
                lines=[
                    {"account": "Accounts Payable", "debit": amount, "credit": 0},
                    {"account": "Cash", "debit": 0, "credit": amount}
                ]
            )

            self.db.conn.commit()

        except Exception as e:
            self.db.conn.rollback()
            raise e
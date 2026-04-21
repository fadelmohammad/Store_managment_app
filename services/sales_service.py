# File: services/sales_service.py

class SalesService:
    def __init__(self, db, ledger_service):
        self.db = db
        self.ledger = ledger_service

    def process_sale(self, cart, inv_type, partner_id, discount_pct, tax_pct, payment_method, exchange_rate):
        """
        Processes a sale or return:
        1. Validates stock and products.
        2. Calculates Totals and COGS (USD).
        3. Applies Exchange Rate for SYP records.
        4. Updates Inventory and records Movements.
        5. Generates Double-Entry Ledger records.
        """
        if not cart:
            raise Exception("Cart is empty")

        try:
            # Start transaction for atomicity
            self.db.conn.execute("BEGIN")

            subtotal = 0.0
            total_cogs = 0.0
            valid_items = [item for item in cart if item is not None]

            # 1. Validation & Pre-calculation
            for item in valid_items:
                pid = item["id"]
                product = self.db.cursor.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()

                if product is None:
                    raise Exception(f"Product ID {pid} not found in database.")

                if item["qty"] > 0 and product["quantity"] < item["qty"]:
                    raise Exception(f"Insufficient stock for '{product['name']}'.")
                subtotal += item["price"] * item["qty"]
                total_cogs += product["cost"] * item["qty"]

            # 2. Calculate Financials (USD)
            tax = subtotal * tax_pct
            discount = subtotal * discount_pct
            total_usd = (subtotal - discount) + tax
            
            # --- SYP Calculation for Reference/Ledger ---
            total_syp = total_usd * exchange_rate

            # 3. Record Invoice (Unified Partner ID)
            # Note: If you update your DB schema, you should add columns for exchange_rate and total_syp here
            invoice_id = self.db.cursor.execute(
                """INSERT INTO invoices (type, date, partner_id, total, total_syp, rate_at_time, tax, discount, payment_method, status) 
                   VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)""",
                (inv_type, partner_id, total_usd, total_syp, exchange_rate, tax, discount, payment_method, "Completed")
            ).lastrowid

            # 4. Update Items & Inventory
            for item in valid_items:
                self.db.cursor.execute(
                    "INSERT INTO invoice_items (invoice_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                    (invoice_id, item["id"], item["qty"], item["price"])
                )

                stock_delta = -item["qty"] 
                move_type = "OUT" if item["qty"] > 0 else "IN"

                self.db.update_stock_with_log(
                    product_id=item["id"],
                    change=stock_delta,
                    m_type=move_type,
                    reason=f"{inv_type} #{invoice_id}"
                )

            # 5. Accounting Ledger - Revenue Entry
            if payment_method == "Credit":
                target_account = "Accounts Receivable"
                self.db.cursor.execute(
                    "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                    (total_usd, partner_id)
                )
            else:
                target_account = "Cash"

            # Determine direction for Revenue
            if total_usd >= 0:
                rev_lines = [
                    {"account": target_account, "debit": total_usd, "credit": 0},
                    {"account": "Sales Revenue", "debit": 0, "credit": total_usd}
                ]
            else:
                # It's a net Return: Debit Revenue (reduction) and Credit Asset (refund)
                rev_lines = [
                    {"account": "Sales Revenue", "debit": abs(total_usd), "credit": 0},
                    {"account": target_account, "debit": 0, "credit": abs(total_usd)}
                ]

            self.ledger.create_entry(
                description=f"{inv_type} #{invoice_id} ({payment_method}) @ {exchange_rate:,.0f} SYP",
                reference_id=invoice_id,
                lines=rev_lines
            )

            # 6. Accounting Ledger - COGS Entry
            if total_cogs >= 0:
                cogs_lines = [
                    {"account": "Cost of Goods Sold", "debit": total_cogs, "credit": 0},
                    {"account": "Inventory", "debit": 0, "credit": total_cogs}
                ]
            else:
                # Items returned to stock: Increase Inventory, Decrease COGS expense
                cogs_lines = [
                    {"account": "Inventory", "debit": abs(total_cogs), "credit": 0},
                    {"account": "Cost of Goods Sold", "debit": 0, "credit": abs(total_cogs)}
                ]

            self.ledger.create_entry(
                description=f"COGS for {inv_type} #{invoice_id}",
                reference_id=invoice_id,
                lines=cogs_lines
            )

            self.db.conn.commit()
            return invoice_id, total_usd

        except Exception as e:
            self.db.conn.rollback()
            raise e
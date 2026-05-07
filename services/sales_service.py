# File: services/sales_service.py

from database.repositories.sales_repo import SalesRepository


class SalesService:
    def __init__(self, conn, ledger_service):
        self.repo = SalesRepository(conn)
        self.ledger = ledger_service

    def process_sale(self, cart, inv_type, partner_id, discount_pct, tax_pct, payment_method, exchange_rate):
        if not cart:
            raise ValueError("Cart is empty")

        valid_items = [item for item in cart if item is not None]

        try:
            self.repo.conn.execute("BEGIN")

            subtotal = 0.0
            total_cogs = 0.0

            for item in valid_items:
                product = self.repo.get_product(item["id"])
                if product is None:
                    raise ValueError(f"Product ID {item['id']} not found in database.")
                if item["qty"] > 0 and product["quantity"] < item["qty"]:
                    raise ValueError(f"Insufficient stock for '{product['name']}'.")
                subtotal += item["price"] * item["qty"]
                total_cogs += product["cost"] * item["qty"]

            tax = subtotal * tax_pct
            discount = subtotal * discount_pct
            total_usd = (subtotal - discount) + tax
            total_syp = total_usd * exchange_rate

            invoice_id = self.repo.create_invoice(
                inv_type, partner_id, total_usd, total_syp,
                exchange_rate, tax, discount, payment_method,
            )

            for item in valid_items:
                self.repo.add_invoice_item(invoice_id, item["id"], item["qty"], item["price"])
                stock_delta = -item["qty"]
                move_type = "OUT" if item["qty"] > 0 else "IN"
                self.repo.update_product_stock(item["id"], stock_delta)
                self.repo.insert_stock_movement(item["id"], move_type, abs(item["qty"]), f"{inv_type} #{invoice_id}")

            if payment_method == "Credit":
                target_account = "Accounts Receivable"
                self.repo.update_account_balance(partner_id, total_usd)
            else:
                target_account = "Cash"

            rev_lines = (
                [
                    {"account": target_account, "debit": total_usd, "credit": 0},
                    {"account": "Sales Revenue", "debit": 0, "credit": total_usd},
                ]
                if total_usd >= 0 else
                [
                    {"account": "Sales Revenue", "debit": abs(total_usd), "credit": 0},
                    {"account": target_account, "debit": 0, "credit": abs(total_usd)},
                ]
            )
            self.ledger.create_entry(
                f"{inv_type} #{invoice_id} ({payment_method}) @ {exchange_rate:,.0f} SYP",
                invoice_id, rev_lines,
            )

            cogs_lines = (
                [
                    {"account": "Cost of Goods Sold", "debit": total_cogs, "credit": 0},
                    {"account": "Inventory", "debit": 0, "credit": total_cogs},
                ]
                if total_cogs >= 0 else
                [
                    {"account": "Inventory", "debit": abs(total_cogs), "credit": 0},
                    {"account": "Cost of Goods Sold", "debit": 0, "credit": abs(total_cogs)},
                ]
            )
            self.ledger.create_entry(f"COGS for {inv_type} #{invoice_id}", invoice_id, cogs_lines)

            self.repo.conn.commit()
            return invoice_id, total_usd

        except Exception:
            self.repo.conn.rollback()
            raise

# services/purchase_service.py

class PurchaseService:
    def __init__(self, purchase_repo, product_repo, stock_repo, inventory_service, ledger_service, account_repo):
        self.purchase_repo = purchase_repo
        self.product_repo = product_repo
        self.stock_repo = stock_repo
        self.inventory_service = inventory_service
        self.ledger = ledger_service
        self.account_repo = account_repo

    def process_purchase(self, cart, partner_id, exchange_rate, payment_method="Cash", tax_pct=0, discount_pct=0):
        """
        Handles the end-to-end purchase workflow
        """
        if not cart:
            raise Exception("Cart is empty")

        try:
            # Start transaction
            self.purchase_repo.begin_transaction()

            subtotal = 0.0
            for item in cart:
                subtotal += item["price"] * item["qty"]

            tax = subtotal * tax_pct
            discount = subtotal * discount_pct
            total_usd = (subtotal - discount) + tax

            # 1. Create Purchase Invoice
            invoice_id = self.purchase_repo.create_invoice(
                partner_id, total_usd, tax, discount, payment_method
            )

            # 2. Update Stock and Movements
            for item in cart:
                # Update weighted average cost using inventory service
                self.inventory_service.update_weighted_average_cost(
                    item["id"], item["qty"], item["price"]
                )

                # Add to invoice items
                self.purchase_repo.add_invoice_item(invoice_id, item["id"], item["qty"], item["price"])

                # Update stock with log
                self.inventory_service.update_stock_with_log(
                    product_id=item["id"],
                    change=item["qty"],
                    m_type="IN",
                    reason=f"Purchase Invoice #{invoice_id} (Rate: {exchange_rate:,.0f} SYP)"
                )

            # 3. Handle Accounting Ledger
            ledger_lines = [
                {"account": "Inventory", "debit": total_usd, "credit": 0}
            ]

            if payment_method == "Cash":
                ledger_lines.append({"account": "Cash", "debit": 0, "credit": total_usd})
            else:
                ledger_lines.append({"account": "Accounts Payable", "debit": 0, "credit": total_usd})
                self.purchase_repo.update_account_balance(partner_id, total_usd)

            self.ledger.create_entry(
                description=f"Purchase Invoice #{invoice_id} @ {exchange_rate:,.0f} SYP",
                reference_id=invoice_id,
                lines=ledger_lines
            )

            self.purchase_repo.commit_transaction()
            return invoice_id, total_usd

        except Exception as e:
            self.purchase_repo.rollback_transaction()
            raise e
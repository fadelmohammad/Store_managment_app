# inventory_service.py


class InventoryService:
    def __init__(self, product_repo, stock_repo, category_repo):
        self.product_repo = product_repo
        self.stock_repo = stock_repo
        self.category_repo = category_repo

        if product_repo.conn is not stock_repo.conn:
            raise ValueError("Repositories must share the same DB connection")

    def get_products(self):
        """Fetches all products"""
        return self.product_repo.get_all()

    def get_product_by_id(self, product_id):
        """Fetches a specific product based on its ID"""
        return self.product_repo.get_by_id(product_id)

    def add_product(self, name, category_id, price, cost, quantity, threshold):
        # basic validation (expand later)
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        movement_type = "IN"
        reason = "initial"

        self.product_repo.add(name, category_id, price, cost, quantity, threshold)
        self.stock_repo.insert_movement(product_id, movement_type, quantity, reason)

    def update_product(self, product_id, name, category_id, price, cost, quantity, min_threshold):
        self.product_repo.update(product_id, name, category_id, price, cost, quantity, min_threshold)

    def update_stock_with_log(self, product_id, change, m_type, reason):
        product = self.product_repo.get_by_id(product_id)

        if not product:
            raise ValueError("Product not found")

        new_qty = product["quantity"] + change

        if new_qty < 0:
            raise ValueError("Insufficient stock")

        # atomicity handled via connection shared across repos
        self.product_repo.update_quantity(product_id, new_qty)
        self.stock_repo.insert_movement(product_id, m_type, change, reason)

    def update_weighted_average_cost(self, product_id, new_qty, purchase_price):
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError("product not found")

        old_qty = product["quantity"]
        old_cost = product["cost"]

        total_qty = old_qty + new_qty

        if total_qty <= 0:
            new_cost = purchase_price
        else:
            total_value = (old_qty * old_cost) + (new_qty * purchase_price)
            new_cost = total_value / total_qty

        self.product_repo.update_cost(product_id, round(new_cost, 2))

    def get_product_history(self, product_id):
        """Fetches the stock movement timeline for a specific product."""
        self.product_repo.get_history(product_id)

    def get_category_history(self, category_path):
        """Fetches history for all products under a specific category path."""
        self.category_repo.get_history(category_path):

    def bulk_update_prices(self, percentage):
        multiplier = 1.0 + (percentage / 100.0)
        self.product_repo.bulk_update_prices(multiplier)
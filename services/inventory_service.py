# inventory_service.py

class InventoryService:
    def __init__(self, product_repo, stock_repo, category_service,category_repo):
        self.product_repo = product_repo
        self.stock_repo = stock_repo
        self.category_service = category_service
        self.category_repo = category_repo

        if not (product_repo.conn is stock_repo.conn):
            raise ValueError("Repositories must share the same DB connection")


    def get_products(self):
        products = self.product_repo.get_all()
        
        formatted_products = []
        for p in products:
            product = dict(p) if hasattr(p, 'keys') else {
                "id": p[0],
                "name": p[1],
                "category_id": p[2],
                "price": p[3],
                "cost": p[4],
                "quantity": p[5],
                "min_threshold": p[6] if len(p) > 6 else 0
            }
            
            if product.get("category_id"):
                product["category"] = self.category_service.get_category_path(product["category_id"])
            else:
                product["category"] = "Uncategorized"
            
            formatted_products.append(product)
        
        return formatted_products

    def search_products(self, term: str):
        """
        POS needs a 'path' string for category breadcrumb (recursive tree),
        so we return the same shape as ProductRepository.search_products(),
        but converted to dicts.
        """
        term = (term or "").strip()
        if not term:
            return []

        rows = self.product_repo.search_products(term)
        results = []
        for r in rows:
            results.append(dict(r) if hasattr(r, "keys") else r)
        return results

    def get_product_by_id(self, product_id):
        """Fetches a specific product based on its ID"""
        product = self.product_repo.get_by_id(product_id)
        if product:
            if hasattr(product, 'keys'):
                product_dict = dict(product)
            else:
                product_dict = {
                    "id": product[0],
                    "name": product[1],
                    "category_id": product[2],
                    "price": product[3],
                    "cost": product[4],
                    "quantity": product[5],
                    "min_threshold": product[6] if len(product) > 6 else 0
                }
            
            if product_dict.get("category_id"):
                product_dict["category_path"] = self.category_service.get_category_path(product_dict["category_id"])
            
            return product_dict
        return None

    def get_categories(self):
        """Get all categories"""
        categories = self.category_service.get_categories()
        formatted = []
        for cat in categories:
            if hasattr(cat, 'keys'):
                formatted.append(dict(cat))
            else:
                formatted.append({
                    "id": cat[0],
                    "name": cat[1],
                    "parent_id": cat[2] if len(cat) > 2 else None,
                    "path": cat[3] if len(cat) > 3 else cat[1],
                    "parent_name": cat[4] if len(cat) > 4 else None
                })
        return formatted

    def get_category_path(self, category_id):
        """Get category path by ID"""
        if not category_id:
            return "Uncategorized"
        return self.category_service.get_category_path(category_id)

    def add_category(self, name, parent_id):
        """Add a new category"""
        return self.category_service.add_category(name, parent_id)


    def delete_category(self, category_id):
        """Delete a category"""
        try:
            if not category_id:
                raise ValueError("Category ID is required")
            
            self.category_service.delete_category(category_id)
            print(f" Category {category_id} deleted via InventoryService")
            
        except Exception as e:
            print(f" Error in InventoryService.delete_category: {e}")
            raise

    def count_products_in_category(self, category_id):
        """Count products in a specific category using category_repo"""
        try:
            if not category_id:
                return 0
        
            if hasattr(self.category_repo, 'count_by_category'):
                return self.category_repo.count_by_category(category_id)
            else:
                print(" count_by_category method not found in category_repo")
                return 0
        except Exception as e:
            print(f" Error in count_products_in_category: {e}")
            return 0

    def get_category_history(self, category_path):
        """Get history for a category"""
        history = self.category_service.get_category_history(category_path)
        if history and len(history) > 0 and hasattr(history[0], 'keys'):
            return [dict(row) for row in history]
        return history

    def add_product(self, name, category_id, price, cost, quantity, threshold):
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

   
        product_id = self.product_repo.add(name, category_id, price, cost, quantity, threshold)
        
  
        self.stock_repo.insert_movement(product_id, "IN", quantity, "Initial stock")

        return product_id

    def update_product(self, product_id, name, category_id, price, cost, quantity, min_threshold):
        self.product_repo.update(product_id, name, category_id, price, cost, quantity, min_threshold)

    def delete_product(self, product_id):
        self.product_repo.delete(product_id)


    def update_stock_with_log(self, product_id, change, m_type, reason):
        """Update stock with logging"""
        product = self.get_product_by_id(product_id)

        if not product:
            raise ValueError("Product not found")

        new_qty = product["quantity"] + change

        if new_qty < 0:
            raise ValueError("Insufficient stock")

        self.product_repo.update_quantity(product_id, new_qty)
        
       
        self.stock_repo.insert_movement(product_id, m_type, change, reason)


    def update_weighted_average_cost(self, product_id, new_qty, purchase_price):
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        old_qty = product["quantity"]
        old_cost = product["cost"]

        total_qty = old_qty + new_qty

        if total_qty <= 0:
            new_cost = purchase_price
        else:
            total_value = (old_qty * old_cost) + (new_qty * purchase_price)
            new_cost = total_value / total_qty

        self.product_repo.update_cost(product_id, round(new_cost, 2))

    def bulk_update_prices(self, percentage):
        multiplier = 1.0 + (percentage / 100.0)
        self.product_repo.bulk_update_prices(multiplier)

    def get_product_history(self, product_id):
        history = self.stock_repo.get_movements(product_id)

        if history and len(history) > 0 and hasattr(history[0], 'keys'):
            return [dict(row) for row in history]
        return history

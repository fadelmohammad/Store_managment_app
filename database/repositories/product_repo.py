# product_repo.py


class ProductRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_all(self):
        return self.conn.execute(
            """
            SELECT 
                p.*, 
                c.name AS category
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
            """
        ).fetchall()

    def search_products(self, term):
        """Search products by name OR category path (recursive)."""
        query = """
            WITH RECURSIVE cat_tree(id, path) AS (
                SELECT id, name FROM categories WHERE parent_id IS NULL
                UNION ALL
                SELECT c.id, ct.path || ' > ' || c.name
                FROM categories c
                JOIN cat_tree ct ON c.parent_id = ct.id
            )
            SELECT p.*, ct.path
            FROM products p
            LEFT JOIN cat_tree ct ON p.category_id = ct.id
            WHERE p.name LIKE ? OR ct.path LIKE ?
            ORDER BY p.id
        """
        like = f"%{term}%"
        return self.conn.execute(query, (like, like)).fetchall()

    def get_by_id(self, product_id):
        return self.conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()

    def add(self, name, category_id, price, cost, quantity, min_threshold):
        with self.conn:
            cursor = self.conn.execute(
                """INSERT INTO products 
                (name, category_id, price, cost, quantity, min_threshold)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, category_id, price, cost, quantity, min_threshold),
            )
            return cursor

    def update(self, product_id, name, category_id, price, cost, quantity, min_threshold):
        with self.conn:
            self.conn.execute(
                """UPDATE products SET name=?, category_id=?, price=?, cost=?, quantity=?, min_threshold=? WHERE id=?""",
                (name, category_id, price, cost, quantity, min_threshold, product_id),
            )

    def delete(self, product_id):
        with self.conn:
            self.conn.execute("DELETE FROM products WHERE id = ?", (product_id,))

    def update_quantity(self, product_id, new_qty):
        with self.conn:
            self.conn.execute(
                "UPDATE products SET quantity = ? WHERE id = ?",
                (new_qty, product_id),
            )

    def update_cost(self, product_id, new_cost):
        with self.conn:
            self.conn.execute(
                "UPDATE products SET cost = ? WHERE id = ?",
                (new_cost, product_id),
            )

    def bulk_update_prices(self, multiplier):
        with self.conn:
            self.conn.execute(
                "UPDATE products SET price = ROUND(price * ?, 2)", (multiplier,)
            )

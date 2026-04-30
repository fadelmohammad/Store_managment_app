class CategoryRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_path(self, cat_id):
        """Returns 'Electrical > Lights > Bulbs' for a given category ID."""
        query = """
            WITH RECURSIVE category_path(id, name, parent_id, path) AS (
                SELECT id, name, parent_id, name FROM categories WHERE parent_id IS NULL
                UNION ALL
                SELECT c.id, c.name, c.parent_id, cp.path || ' > ' || c.name
                FROM categories c JOIN category_path cp ON c.parent_id = cp.id
            )
            SELECT path FROM category_path WHERE id = ?;
        """
        row = self.conn.execute(query, (cat_id,)).fetchone()
        return row["path"] if row else "Uncategorized"

    def get_all_flat(self):
        """Get all categories with their full paths"""
        results = self.conn.execute("""
            WITH RECURSIVE category_tree AS (
                SELECT id, name, parent_id, name as path, NULL as parent_name
                FROM categories WHERE parent_id IS NULL
                UNION ALL
                SELECT c.id, c.name, c.parent_id, ct.path || ' > ' || c.name, ct.name
                FROM categories c
                JOIN category_tree ct ON c.parent_id = ct.id
            )
            SELECT id, name, parent_id, path, parent_name FROM category_tree ORDER BY path
        """).fetchall()
        formatted = []
        for row in results:
            if isinstance(row, tuple):
                formatted.append({
                    "id": row[0],
                    "name": row[1],
                    "parent_id": row[2],
                    "path": row[3],
                    "parent_name": row[4]
                })
            else:
                formatted.append(dict(row))
        
        return formatted

    def add(self, name, parent_id=None):
        """Add a new category"""
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO categories (name, parent_id) VALUES (?, ?)",
                (name, parent_id)
            )
            return cursor.lastrowid


    def delete(self, category_id):
        """Delete a category (moves child products to parent)"""
        try:
            row = self.conn.execute("SELECT parent_id FROM categories WHERE id = ?", (category_id,)).fetchone()
            
            if not row:
                raise ValueError(f"Category with id {category_id} not found")
            
            parent_id = row[0] if row[0] else None
            
            with self.conn:
                self.conn.execute(
                    "UPDATE products SET category_id = ? WHERE category_id = ?",
                    (parent_id, category_id)
                )
                
                self.conn.execute(
                    "UPDATE categories SET parent_id = ? WHERE parent_id = ?",
                    (parent_id, category_id)
                )
                
                self.conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            
            print(f"Category {category_id} deleted successfully")
            
        except Exception as e:
            print(f"Error deleting category {category_id}: {e}")
            raise

    def get_history(self, category_path):
        """Fetches history for all products under a specific category path."""
        query = """
            SELECT h.date, h.movement_type, h.quantity, h.reason, p.name
            FROM stock_movements h
            JOIN products p ON h.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            -- This CTE logic ensures we get the path to compare
            WHERE p.id IN (
                WITH RECURSIVE sub_cats AS (
                    SELECT id FROM categories WHERE name = ? 
                    UNION ALL
                    SELECT c.id FROM categories c JOIN sub_cats sc ON c.parent_id = sc.id
                )
                SELECT id FROM products WHERE category_id IN (SELECT id FROM sub_cats)
            )
            ORDER BY h.date DESC
        """

        return self.conn.execute(query, (category_path.split(" > ")[-1],)).fetchall()


    def get_by_id(self, category_id):
        """Get category by ID"""
        return self.conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()

    def count_products(self, category_id):
        """Count products in a category"""
        result = self.conn.execute(
            "SELECT COUNT(*) FROM products WHERE category_id = ?",
            (category_id,)
        ).fetchone()
        return result[0] if result else 0
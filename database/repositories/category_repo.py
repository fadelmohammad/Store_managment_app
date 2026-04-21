# category_repo.py

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
	    row = self.cursor.execute(query, (cat_id,)).fetchone()
	    return row["path"] if row else "Uncategorized"

    def get_all_flat(self):
    """Returns all categories with their full breadcrumb paths for dropdowns."""
    query = """
        WITH RECURSIVE category_path(id, name, parent_id, path) AS (
            SELECT id, name, parent_id, name FROM categories WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.name, c.parent_id, cp.path || ' > ' || c.name
            FROM categories c JOIN category_path cp ON c.parent_id = cp.id
        )
        SELECT id, path FROM category_path ORDER BY path;
    """
    return self.cursor.execute(query).fetchall()

    def add(self, name, parent_id=None):
        with self.conn:
            self.conn.execute(
                "INSERT INTO categories (name, parent_id) VALUES (?, ?)",
                (name, parent_id),
            )

    def delete(self, cat_id):
        with self.conn:
            # 1. Find the parent of the category we are about to delete
            res = self.conn.execute(
                "SELECT parent_id FROM categories WHERE id = ?", (cat_id,)
            ).fetchone()
            new_parent_id = res["parent_id"] if res else None

            # 2. Move sub-categories up to the new parent
            self.conn.execute(
                "UPDATE categories SET parent_id = ? WHERE parent_id = ?",
                (new_parent_id, cat_id),
            )

            # 3. Move products up to the new parent category
            self.conn.execute(
                "UPDATE products SET category_id = ? WHERE category_id = ?",
                (new_parent_id, cat_id),
            )

            # 4. Finally, delete the category
            self.conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))

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
        # Note: Depending on your schema, you might need to adjust the WHERE
        # to match how you store/identify categories.
        return self.cursor.execute(query, (category_path.split(" > ")[-1],)).fetchall()
# database.py

import sqlite3
from datetime import datetime


class Database:
    def __init__(self, conn):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()

    # --- PARTNER METHODS ---

    # --- INVENTORY METHODS ---
    def get_all_products(self):
        query = """
            WITH RECURSIVE cat_tree(id, path) AS (
                SELECT id, name FROM categories WHERE parent_id IS NULL
                UNION ALL
                SELECT c.id, ct.path || ' > ' || c.name FROM categories c 
                JOIN cat_tree ct ON c.parent_id = ct.id
            )
            SELECT p.id, p.name, p.price, p.cost, p.quantity, p.min_threshold, 
                   COALESCE(ct.path, 'Uncategorized') as category
            FROM products p
            LEFT JOIN cat_tree ct ON p.category_id = ct.id
        """
        return self.cursor.execute(query).fetchall()

try:
    pass
except Exception as e:
    raise e







    # --- CATEGORY LOGIC ---










    # --- REPORTING METHODS ---





    def close(self):
        self.conn.close()

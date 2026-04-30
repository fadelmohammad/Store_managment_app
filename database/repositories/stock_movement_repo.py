# stock_movement_repo.py - نسخة مبسطة

class StockMovementRepository:
    def __init__(self, conn):
        self.conn = conn

    def insert_movement(self, product_id, movement_type, quantity, reason):
        """Insert a stock movement record"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO stock_movements (product_id, movement_type, quantity, date, reason)
                VALUES (?, ?, ?, datetime('now'), ?)
            """, (product_id, movement_type, quantity, reason))
            self.conn.commit()
            print(f" Stock movement recorded: Product {product_id}, {movement_type}, {quantity}")
        except Exception as e:
            print(f" Error inserting movement: {e}")
            raise

    def get_movements(self, product_id):
        """Get all movements for a specific product"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT date, movement_type, quantity, reason 
                FROM stock_movements 
                WHERE product_id = ? 
                ORDER BY date DESC
            """, (product_id,))
            return cursor.fetchall()
        except Exception as e:
            print(f" Error getting movements: {e}")
            return []
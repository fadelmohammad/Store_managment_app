
import logging

class StockMovementRepository:
    def __init__(self, conn):
        self.conn = conn

    def insert_movement(self, product_id, movement_type, quantity, reason):
        """Insert a stock movement record"""
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO stock_movements (product_id, movement_type, quantity, date, reason)
                    VALUES (?, ?, ?, datetime('now'), ?)
                """, (product_id, movement_type, quantity, reason))
            logging.info(f"Stock movement recorded: Product {product_id}, {movement_type}, {quantity}")
        except Exception as e:
            logging.error(f"Error inserting movement: {e}")
            raise

    def get_movements(self, product_id):
        """Get all movements for a specific product"""
        try:
            return self.conn.execute("""
                SELECT date, movement_type, quantity, reason 
                FROM stock_movements 
                WHERE product_id = ? 
                ORDER BY date DESC
            """, (product_id,)).fetchall()
        except Exception as e:
            logging.error(f"Error getting movements: {e}")
            return []

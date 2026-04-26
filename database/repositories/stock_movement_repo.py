# stock_movement_repo.py

class StockMovementRepository:
	def __init__(self, conn):
		self.conn = conn

	def insert_movement(self, product_id, movement_type, quantity, reason):
		with self.conn:
			self.conn.execute(
                """INSERT INTO stock_movements 
                (product_id, movement_type, quantity, date, reason)
                VALUES (?, ?, ?, datetime('now'), ?)""",
                (product_id, movement_type, quantity, reason),
            )
	def get_movements(self, product_id):
        return self.conn.execute(
            """
            SELECT date, movement_type, quantity, reason 
            FROM stock_movements 
            WHERE product_id = ? 
            ORDER BY date DESC
        """,
            (product_id,),
        ).fetchall()
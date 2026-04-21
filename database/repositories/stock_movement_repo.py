# stock_movement_repo.py

class StockMovementRepo:
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
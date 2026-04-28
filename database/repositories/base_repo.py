# base_repo.py

# not used for now!!
class BaseRepository:
    def __init__(self, conn):
        self.conn = conn

    def _execute(self, query, params=()):
        try:
            cursor = self.conn.execute(query, params)
            return cursor
        except Exception as e:
            raise RuntimeError(f"Database error: {e}")

    def _execute_many(self, query, seq_of_params, commit=False):
        try:
            cursor = self.conn.executemany(query, seq_of_params)
            if commit:
                self.conn.commit()
            return cursor
        except Exception as e:
            raise RuntimeError(f"Database error: {e}")
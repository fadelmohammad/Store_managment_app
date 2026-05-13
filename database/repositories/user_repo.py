# user_repo.py


class UserRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_id(self, user_id):
        return self.conn.execute(
            "SELECT id, username, full_name, role, is_active, last_login, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    def get_by_credentials(self, username, hashed_password):
        return self.conn.execute(
            "SELECT id, username, full_name, role, is_active FROM users WHERE username = ? AND password = ?",
            (username, hashed_password),
        ).fetchone()

    def update_last_login(self, user_id):
        with self.conn:
            self.conn.execute(
                "UPDATE users SET last_login = datetime('now') WHERE id = ?", (user_id,)
            )

    def get_by_username(self, username):
        return self.conn.execute(
            "SELECT id, username, full_name, role, is_active FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    def get_all(self):
        return self.conn.execute(
            "SELECT id, username, full_name, role, is_active FROM users ORDER BY id"
        ).fetchall()

    def get_password(self, user_id):
        row = self.conn.execute(
            "SELECT password FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return row[0] if row else None

    def get_username(self, user_id):
        row = self.conn.execute(
            "SELECT username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return row[0] if row else None

    def create(self, username, hashed_password, full_name, role):
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO users (username, password, full_name, role, is_active) VALUES (?, ?, ?, ?, 1)",
                (username, hashed_password, full_name, role),
            )
            return cursor.lastrowid

    def update_full_name(self, user_id, full_name):
        with self.conn:
            self.conn.execute(
                "UPDATE users SET full_name = ? WHERE id = ?", (full_name, user_id)
            )

    def update_full_name_and_password(self, user_id, full_name, hashed_password):
        with self.conn:
            self.conn.execute(
                "UPDATE users SET full_name = ?, password = ? WHERE id = ?",
                (full_name, hashed_password, user_id),
            )

    def update_role(self, user_id, role):
        with self.conn:
            self.conn.execute(
                "UPDATE users SET role = ? WHERE id = ?", (role, user_id)
            )

    def update_status(self, user_id, is_active):
        with self.conn:
            self.conn.execute(
                "UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id)
            )

    def update_password(self, user_id, hashed_password):
        with self.conn:
            self.conn.execute(
                "UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id)
            )

    def delete(self, user_id):
        with self.conn:
            self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def get_permissions(self, role):
        return self.conn.execute(
            "SELECT * FROM permissions WHERE role = ?", (role,)
        ).fetchone()

    def log_action(self, user_id, action, details):
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO user_logs (user_id, action, details, ip_address, timestamp)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (user_id, action, details, "system"),
            )

    def get_logs(self, user_id=None, limit=100):
        if user_id:
            return self.conn.execute(
                """
                SELECT l.id, u.username, l.action, l.details, l.ip_address, l.timestamp
                FROM user_logs l
                LEFT JOIN users u ON l.user_id = u.id
                WHERE l.user_id = ?
                ORDER BY l.timestamp DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return self.conn.execute(
            """
            SELECT l.id, u.username, l.action, l.details, l.ip_address, l.timestamp
            FROM user_logs l
            LEFT JOIN users u ON l.user_id = u.id
            ORDER BY l.timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

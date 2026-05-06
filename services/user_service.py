# services/user_service.py

import hashlib
import sqlite3

class UserService:
    def __init__(self, conn):
        self.conn = conn
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, is_active FROM users ORDER BY id")
        users = cursor.fetchall()
        
        return [
            {
                'id': u[0],
                'username': u[1],
                'full_name': u[2],
                'role': u[3],
                'is_active': u[4]
            }
            for u in users
        ]
    
    def get_user_by_id(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, full_name, role, is_active, last_login, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'full_name': user[2],
                'role': user[3],
                'is_active': user[4],
                'last_login': user[5],
                'created_at': user[6]
            }
        return None
    
    def create_user(self, username, password, full_name, role):
        hashed_pass = self.hash_password(password)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, full_name, role, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (username, hashed_pass, full_name, role))
        self.conn.commit()
        
        cursor.execute("SELECT last_insert_rowid()")
        user_id = cursor.fetchone()[0]
        
        self.log_user_action(user_id, "user_created", f"User {username} created by system")
        return user_id
    
    def update_user_role(self, user_id, role):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        username = cursor.fetchone()[0]
        
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        self.conn.commit()
        
        self.log_user_action(user_id, "role_changed", f"Role changed to {role}")
    
    def update_user_status(self, user_id, is_active):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        username = cursor.fetchone()[0]
        
        status_text = "activated" if is_active else "deactivated"
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
        self.conn.commit()
        
        self.log_user_action(user_id, "status_changed", f"Account {status_text}")
    
    def update_user_password(self, user_id, new_password):
        hashed_pass = self.hash_password(new_password)
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        username = cursor.fetchone()[0]
        
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pass, user_id))
        self.conn.commit()
        
        self.log_user_action(user_id, "password_changed", "Password changed")
    
    def delete_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        username = cursor.fetchone()[0]
        
        self.log_user_action(user_id, "user_deleted", f"User {username} deleted")
        
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()
    
    def get_user_permissions(self, role):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM permissions WHERE role = ?", (role,))
        perm = cursor.fetchone()
        
        if perm:
            permission_keys = [
                'can_view_products', 'can_edit_products', 'can_delete_products',
                'can_view_invoices', 'can_create_invoices', 'can_edit_invoices',
                'can_delete_invoices', 'can_view_accounts', 'can_edit_accounts',
                'can_view_reports', 'can_manage_users', 'can_manage_settings'
            ]
            return dict(zip(permission_keys, perm[2:]))
        return {}
    
    def log_user_action(self, user_id, action, details):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO user_logs (user_id, action, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (user_id, action, details, "system"))
        self.conn.commit()
    
    def get_user_logs(self, user_id=None, limit=100):
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute("""
                SELECT l.id, u.username, l.action, l.details, l.ip_address, l.timestamp
                FROM user_logs l
                LEFT JOIN users u ON l.user_id = u.id
                WHERE l.user_id = ?
                ORDER BY l.timestamp DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT l.id, u.username, l.action, l.details, l.ip_address, l.timestamp
                FROM user_logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.timestamp DESC
                LIMIT ?
            """, (limit,))
        
        logs = cursor.fetchall()
        return [
            {
                'id': log[0],
                'username': log[1] if log[1] else 'System',
                'action': log[2],
                'details': log[3],
                'ip_address': log[4],
                'timestamp': log[5]
            }
            for log in logs
        ]
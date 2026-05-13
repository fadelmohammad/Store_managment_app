# services/user_service.py

from database.repositories.user_repo import UserRepository
from services.password_service import hash_password_pbkdf2, verify_password


class UserService:
    def __init__(self, conn):
        self.repo = UserRepository(conn)

    def hash_password(self, password):
        return hash_password_pbkdf2(password)

    def get_user_profile(self, user_id):
        user = self.repo.get_by_id(user_id)
        if not user:
            return None
        return {
            "username": user[1],
            "full_name": user[2],
            "role": user[3],
            "is_active": user[4],
            "last_login": user[5] or "Never",
            "created_at": user[6] or "Unknown",
        }

    def update_own_profile(self, user_id, new_full_name, current_password, new_password, confirm_password):
        new_full_name = (new_full_name or "").strip()
        if not new_full_name:
            raise ValueError("Please enter your full name")

        password_changed = False
        if new_password:
            if not current_password:
                raise ValueError("Please enter your current password to change password")

            stored = self.repo.get_password(user_id)
            if not stored:
                raise ValueError("Current password is incorrect")

            ok, _ = verify_password(stored, current_password)
            if not ok:
                raise ValueError("Current password is incorrect")

            if len(new_password) < 4:
                raise ValueError("New password must be at least 4 characters")

            if new_password != confirm_password:
                raise ValueError("New passwords do not match")

            self.repo.update_full_name_and_password(user_id, new_full_name, self.hash_password(new_password))
            password_changed = True
        else:
            self.repo.update_full_name(user_id, new_full_name)

        if password_changed:
            self.repo.log_action(user_id, "profile_updated_password", "Profile updated (password changed)")
        else:
            self.repo.log_action(user_id, "profile_updated", "Profile updated")

        return {"user_id": user_id, "full_name": new_full_name, "password_changed": password_changed}

    def get_all_users(self):
        return [
            {"id": u[0], "username": u[1], "full_name": u[2], "role": u[3], "is_active": u[4]}
            for u in self.repo.get_all()
        ]

    def get_user_by_id(self, user_id):
        user = self.repo.get_by_id(user_id)
        if not user:
            return None
        return {
            "id": user[0], "username": user[1], "full_name": user[2],
            "role": user[3], "is_active": user[4], "last_login": user[5], "created_at": user[6],
        }

    def create_user(self, username, password, full_name, role):
        user_id = self.repo.create(username, self.hash_password(password), full_name, role)
        self.repo.log_action(user_id, "user_created", f"User {username} created by system")
        return user_id

    def update_user_role(self, user_id, role):
        self.repo.update_role(user_id, role)
        self.repo.log_action(user_id, "role_changed", f"Role changed to {role}")

    def update_user_status(self, user_id, is_active):
        self.repo.update_status(user_id, is_active)
        status_text = "activated" if is_active else "deactivated"
        self.repo.log_action(user_id, "status_changed", f"Account {status_text}")

    def update_user_password(self, user_id, new_password):
        self.repo.update_password(user_id, self.hash_password(new_password))
        self.repo.log_action(user_id, "password_changed", "Password changed")

    def delete_user(self, user_id):
        username = self.repo.get_username(user_id)
        self.repo.log_action(user_id, "user_deleted", f"User {username} deleted")
        self.repo.delete(user_id)

    def get_user_permissions(self, role):
        perm = self.repo.get_permissions(role)
        if not perm:
            return {}
        keys = [
            "can_view_products", "can_edit_products", "can_delete_products",
            "can_view_invoices", "can_create_invoices", "can_edit_invoices",
            "can_delete_invoices", "can_view_accounts", "can_edit_accounts",
            "can_view_reports", "can_manage_users", "can_manage_settings",
        ]
        return dict(zip(keys, perm[2:]))

    def reset_password(self, username, new_password, confirm_password):
        if len(new_password) < 4:
            raise ValueError("Password must be at least 4 characters")
        if new_password != confirm_password:
            raise ValueError("Passwords do not match")

        user = self.repo.get_by_username(username)
        if not user:
            raise ValueError("Username not found")
        if not user[3]:
            raise ValueError("This account is inactive")

        self.repo.update_password(user[0], self.hash_password(new_password))
        self.repo.log_action(user[0], "password_reset", "Password reset from login screen")

    def log_user_action(self, user_id, action, details):
        self.repo.log_action(user_id, action, details)

    def get_user_logs(self, user_id=None, limit=100):
        return [
            {
                "id": log[0],
                "username": log[1] or "System",
                "action": log[2],
                "details": log[3],
                "ip_address": log[4],
                "timestamp": log[5],
            }
            for log in self.repo.get_logs(user_id, limit)
        ]

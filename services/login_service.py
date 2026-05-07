# services/login_service.py

import hashlib
from database.repositories.user_repo import UserRepository

PERMISSION_KEYS = [
    "can_view_products", "can_edit_products", "can_delete_products",
    "can_view_invoices", "can_create_invoices", "can_edit_invoices",
    "can_delete_invoices", "can_view_accounts", "can_edit_accounts",
    "can_view_reports", "can_manage_users", "can_manage_settings",
]


class LoginService:
    def __init__(self, conn):
        self.repo = UserRepository(conn)

    def _hash(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        """
        Authenticates a user.
        Returns a user dict with permissions on success.
        Raises ValueError for invalid credentials or inactive account.
        """
        user = self.repo.get_by_credentials(username, self._hash(password))

        if not user:
            self.repo.log_action(None, "login_failed", f"Failed attempt for user: {username}")
            raise ValueError("Invalid username or password")

        user_id, username, full_name, role, is_active = user

        if not is_active:
            raise ValueError("This account is inactive. Please contact administrator.")

        perm_row = self.repo.get_permissions(role)
        permissions = dict(zip(PERMISSION_KEYS, perm_row[2:])) if perm_row else {}

        self.repo.update_last_login(user_id)
        self.repo.log_action(user_id, "login", "Successful login")

        return {
            "id": user_id,
            "username": username,
            "full_name": full_name,
            "role": role,
            "permissions": permissions,
        }

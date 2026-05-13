# services/login_service.py

from database.repositories.user_repo import UserRepository
from services.password_service import hash_password_pbkdf2, verify_password

PERMISSION_KEYS = [
    "can_view_products", "can_edit_products", "can_delete_products",
    "can_view_invoices", "can_create_invoices", "can_edit_invoices",
    "can_delete_invoices", "can_view_accounts", "can_edit_accounts",
    "can_view_reports", "can_manage_users", "can_manage_settings",
]


class LoginService:
    def __init__(self, conn):
        self.repo = UserRepository(conn)


    def login(self, username, password):
        """
        Authenticates a user.
        Returns a user dict with permissions on success.
        Raises ValueError for invalid credentials or inactive account.
        """
        user = self.repo.get_by_username(username)
        if not user:
            self.repo.log_action(None, "login_failed", f"Failed attempt for user: {username}")
            raise ValueError("Invalid username or password")

        # UserRepository.get_by_username returns:
        # (id, username, full_name, role, is_active)
        if len(user) < 5:
            self.repo.log_action(None, "login_failed", f"Failed attempt for user: {username}")
            raise ValueError("Invalid username or password")

        user_id, username_db, full_name, role, is_active = user[0], user[1], user[2], user[3], user[4]

        stored_hash = self.repo.get_password(user_id)
        if not stored_hash:
            self.repo.log_action(None, "login_failed", f"Failed attempt for user: {username}")
            raise ValueError("Invalid username or password")

        is_valid, needs_rehash = verify_password(stored_hash, password)
        if not is_valid:
            self.repo.log_action(None, "login_failed", f"Failed attempt for user: {username}")
            raise ValueError("Invalid username or password")

        # Upgrade legacy/weak hashes after successful login
        if needs_rehash:
            new_hash = hash_password_pbkdf2(password)
            self.repo.update_password(user_id, new_hash)

        if not is_active:
            raise ValueError("This account is inactive. Please contact administrator.")

        perm_row = self.repo.get_permissions(role)
        permissions = dict(zip(PERMISSION_KEYS, perm_row[2:])) if perm_row else {}

        self.repo.update_last_login(user_id)
        self.repo.log_action(user_id, "login", "Successful login")

        return {
            "id": user_id,
            "username": username_db,
            "full_name": full_name,
            "role": role,
            "permissions": permissions,
        }

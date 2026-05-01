from typing import Dict, List, Optional


class AccountService:
    def __init__(self, account_repo):
        self.account_repo = account_repo

    def get_by_id(self, account_id: int) -> Optional[Dict]:
        row = self.account_repo.get_by_id(account_id)
        if not row:
            return None
        # sqlite3.Row supports dict(row) via iteration over keys
        try:
            return dict(row)
        except Exception:
            return row

    def get_accounts(self, role: str = "All", search: str = "") -> List[Dict]:
        """
        Business-level listing:
        - role filter handled by repo where possible
        - search filter handled in service (keeps UI free of SQL)
        """
        role = role or "All"
        search_normalized = (search or "").strip().lower()

        if role == "All":
            accounts = self.account_repo.get_all()
        else:
            accounts = self.account_repo.get_by_role(role)

        if not search_normalized:
            return accounts

        def matches(acc: Dict) -> bool:
            name = (acc.get("name") or "").lower()
            phone = (acc.get("phone") or "").lower()
            return search_normalized in name or search_normalized in phone

        return [acc for acc in accounts if matches(acc)]

    def get_by_role(self, role: str) -> List[Dict]:
        """Backward-compatible helper."""
        return self.get_accounts(role=role, search="")

    def add_account(self, name, role, phone, email, address) -> int:
        name = (name or "").strip()
        if not name:
            raise ValueError("Name is required")

        role = (role or "").strip()
        if role not in ("Customer", "Supplier"):
            raise ValueError("Invalid role")

        email = (email or "").strip()
        if email and "@" not in email:
            raise ValueError("Invalid email format")

        with self.account_repo.conn:
            account_id = self.account_repo.add(name, role, phone, email, address)
            return account_id

    def update_account(self, account_id, data: Dict) -> None:
        if not account_id:
            raise ValueError("Account ID is required!")

        existing = self.account_repo.get_by_id(account_id)
        if not existing:
            raise ValueError("Account not found.")

        name = (data.get("name") or "").strip()
        if not name:
            raise ValueError("Name cannot be empty!")

        role = (data.get("role") or "").strip()
        if role not in ("Customer", "Supplier"):
            raise ValueError("Invalid role")

        email = (data.get("email") or "").strip()
        if email and "@" not in email:
            raise ValueError("Invalid email format")

        phone = (data.get("phone") or "").strip()
        address = (data.get("address") or "").strip()

        account_data = {
            "name": name,
            "role": role,
            "phone": phone,
            "email": email,
            "address": address,
        }
        self.account_repo.update(account_id, account_data)

    def delete_account(self, account_id) -> None:
        """Validates business rules before allowing deletion."""
        account = self.account_repo.get_by_id(account_id)
        if not account:
            raise ValueError("Account not found.")

        # account is sqlite3.Row due to row_factory
        balance = float(account["balance"] if "balance" in account.keys() else 0.0)

        # Business Rule: Block deletion if balance is non-zero
        if abs(balance) > 0.01:
            raise PermissionError("Cannot delete account with a non-zero balance.")

        self.account_repo.delete(account_id)

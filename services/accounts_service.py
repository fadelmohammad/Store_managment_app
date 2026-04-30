# account_service.py

class AccountService:
    def __init__(self, account_repo):
        self.account_repo = account_repo

    def get_by_role(self, role):
        """Fetches accounts based on role"""
        return 

    def add_account(self, name, role, phone, email, address):
        """adds a new account"""
        name = name.strip()

        if not name:
            raise ValueError("Name is required")

        # Optional but recommended
        if email and "@" not in email:
            raise ValueError("Invalid email format")

        with self.account_repo.conn:
            account_id = self.account_repo.add(
                name, role, phone, email, address
            )

            return account_id

    def update_account(self, account_id, data):
        """Orchestrates business logic and calls the repository."""
        if not account_id:
            raise ValueError("Account ID is required!")

        if not name:
            raise ValueError("Name cannot be empty!")

        account = self.account_repo.get_by_id(account_id)
        if not account:
            raise ValueError("Account not found.")

        self.account_repo.update(account_id, account_data)

    def delete_account(self, account_id):
        """Validates business rules before allowing deletion."""
        account = self.account_repo.get_by_id(account_id)
        
        if not account:
            raise ValueError("Account not found.")

        # Business Rule: Block deletion if balance is non-zero
        if abs(account["balance"]) > 0.01:
            raise PermissionError("Cannot delete account with a non-zero balance.")

        self.account_repo.delete(account_id)
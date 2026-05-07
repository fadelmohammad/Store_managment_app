# File: services/ledger_service.py

from database.repositories.ledger_repo import LedgerRepository


class LedgerService:
    def __init__(self, conn):
        self.ledger_repo = LedgerRepository(conn)

    def get_cash_balance(self) -> float:
        return self.ledger_repo.get_cash_balance()

    def get_recent_cash_transactions(self, limit: int = 20):
        return self.ledger_repo.get_recent_cash_transactions(limit=limit)

    def create_entry(self, description, reference_id, lines):
        return self.ledger_repo.create_entry(description, reference_id, lines)

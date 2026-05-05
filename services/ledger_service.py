# File: services/ledger_service.py

from database.repositories.ledger_repo import LedgerRepository


class LedgerService:
    def __init__(self, db):
        """
        db: sqlite3 connection wrapper used across the app (self.db in main.py).
        """
        self.db = db
        self.ledger_repo = LedgerRepository(db)

    # ==========================================
    # Cashbox / Ledger Queries
    # ==========================================
    def get_cash_balance(self) -> float:
        return self.ledger_repo.get_cash_balance()

    def get_recent_cash_transactions(self, limit: int = 20):
        return self.ledger_repo.get_recent_cash_transactions(limit=limit)

    # ==========================================
    # Journal Write
    # ==========================================
    def create_entry(self, description, reference_id, lines):
        """
        Writes journal_entries + journal_lines.
        Commits at the end so UI never needs to call db.conn.commit().
        """
        self.db.cursor.execute("SELECT datetime('now')").fetchone()[0]

        self.db.cursor.execute(
            "INSERT INTO journal_entries (date, description, reference_id) VALUES (datetime('now'), ?, ?)",
            (description, reference_id),
        )
        entry_id = self.db.cursor.lastrowid

        for line in lines:
            result = self.db.cursor.execute(
                "SELECT id FROM accounts_ledger WHERE name=?",
                (line["account"],),
            ).fetchone()

            if not result:
                raise Exception(f"Account not found in DB: {line['account']}")

            acc_id = result[0]

            self.db.cursor.execute(
                """
                INSERT INTO journal_lines 
                (entry_id, account_id, debit, credit)
                VALUES (?, ?, ?, ?)
                """,
                (entry_id, acc_id, line["debit"], line["credit"]),
            )

        self.db.conn.commit()
        return entry_id

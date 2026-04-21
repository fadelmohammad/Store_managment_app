# File: services/ledger_service.py

class LedgerService:
    def __init__(self, db):
        self.db = db

    def create_entry(self, description, reference_id, lines):
        date = self.db.cursor.execute("SELECT datetime('now')").fetchone()[0]

        self.db.cursor.execute(
            "INSERT INTO journal_entries (date, description, reference_id) VALUES (datetime('now'), ?, ?)",
            (description, reference_id)
        )
        entry_id = self.db.cursor.lastrowid

        for line in lines:
            result = self.db.cursor.execute(
                "SELECT id FROM accounts_ledger WHERE name=?",
                (line["account"],)
            ).fetchone()

            if not result:
                raise Exception(f"Account not found in DB: {line['account']}")

            acc_id = result[0]

            self.db.cursor.execute(
                """INSERT INTO journal_lines 
                (entry_id, account_id, debit, credit)
                VALUES (?, ?, ?, ?)""",
                (entry_id, acc_id, line["debit"], line["credit"])
            )

        return entry_id

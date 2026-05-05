# ledger_repo.py

from typing import List, Dict, Optional


class LedgerRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_cash_balance(self) -> float:
        """
        Returns: SUM(debit) - SUM(credit) for the ledger account named 'Cash'
        """
        row = self.conn.execute(
            """
            SELECT SUM(debit) - SUM(credit) as balance
            FROM journal_lines l
            JOIN accounts_ledger a ON l.account_id = a.id
            WHERE a.name = 'Cash'
            """
        ).fetchone()

        if not row:
            return 0.0
        # sqlite3.Row supports dict-like access
        return float(row["balance"] or 0.0)

    def get_recent_cash_transactions(self, limit: int = 20) -> List[Dict]:
        """
        Returns recent cash ledger movements:
        date, description, debit, credit
        """
        rows = self.conn.execute(
            """
            SELECT e.date, e.description, l.debit, l.credit
            FROM journal_entries e
            JOIN journal_lines l ON e.id = l.entry_id
            JOIN accounts_ledger a ON l.account_id = a.id
            WHERE a.name = 'Cash'
            ORDER BY e.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        result: List[Dict] = []
        for r in rows:
            if hasattr(r, "keys"):
                result.append(dict(r))
            else:
                result.append(
                    {
                        "date": r[0],
                        "description": r[1],
                        "debit": r[2],
                        "credit": r[3],
                    }
                )
        return result

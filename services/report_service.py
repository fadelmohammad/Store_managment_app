# report_service.py

class ReportingService:
    def __init__(self, product_repo, stock_repo):
        self.product_repo = product_repo
        self.stock_repo = stock_repo
        
    def get_sales_trend(self, start_date, end_date):
        query = """
            SELECT date(e.date) as day, SUM(l.credit) as daily_sales
            FROM journal_entries e
            JOIN journal_lines l ON e.id = l.entry_id
            JOIN accounts_ledger a ON l.account_id = a.id
            WHERE a.name = 'Sales Revenue' AND date(e.date) BETWEEN ? AND ?
            GROUP BY day ORDER BY day ASC
        """
        self.cursor.execute(query, (start_date, end_date))
        rows = self.cursor.fetchall()
        return [row["day"] for row in rows], [row["daily_sales"] for row in rows]

    def get_financial_report(self, start_date, end_date):
        query = """
            SELECT a.name, SUM(l.debit) as total_debit, SUM(l.credit) as total_credit
            FROM journal_lines l
            JOIN journal_entries e ON l.entry_id = e.id
            JOIN accounts_ledger a ON l.account_id = a.id
            WHERE date(e.date) BETWEEN ? AND ?
            GROUP BY a.name
        """
        self.cursor.execute(query, (start_date, end_date))
        rows = self.cursor.fetchall()

        report = {"sales": 0.0, "cogs": 0.0, "expenses": 0.0, "net_profit": 0.0}
        for row in rows:
            if row["name"] == "Sales Revenue":
                report["sales"] = row["total_credit"] or 0.0
            elif row["name"] == "Cost of Goods Sold":
                report["cogs"] = row["total_debit"] or 0.0
            elif row["type"] == "Expense":
                report["expenses"] += row["total_debit"] or 0.0

        report["net_profit"] = report["sales"] - report["cogs"] - report["expenses"]
        return report
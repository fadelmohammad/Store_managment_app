# report_repo.py
import logging

class ReportRepository:
    def __init__(self, conn):
        self.conn = conn

    # ==========================================
    # Inventory Reports
    # ==========================================

 
    # report_repo.py - في دالة get_all_products_for_report

    def get_all_products_for_report(self):
        """Get all products with full details for inventory report"""
        try:
            results = self.conn.execute("""
                SELECT 
                    p.id, 
                    p.name,  
                    p.price, 
                    p.cost, 
                    p.quantity, 
                    p.min_threshold,
                    c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.name
            """).fetchall()
            
            logging.info(f"get_all_products_for_report: found {len(results)} products")
            
            if results:
                logging.debug(f"First product sample: {results[0]}")
            
            return results
        except Exception as e:
            logging.error(f"Error in get_all_products_for_report: {e}")
            return []
    

    def get_total_inventory_value(self):
        """Calculate total inventory value (sum of quantity * cost)"""
        result = self.conn.execute("""
            SELECT SUM(quantity * cost) as total_value 
            FROM products
        """).fetchone()
        return result[0] if result and result[0] else 0.0

    def get_low_stock_products(self, threshold=5):
        """Get products with quantity below threshold"""
        return self.conn.execute("""
            SELECT p.id, p.name, p.quantity, p.min_threshold
            FROM products p
            WHERE p.quantity <= ?
            ORDER BY p.quantity ASC
        """, (threshold,)).fetchall()

    # ==========================================
    # Stock Movement Reports
    # ==========================================

    def get_stock_movements(self, start_date=None, end_date=None):
        """Get stock movements with optional date range"""
        query = """
            SELECT sm.id, sm.product_id, p.name as product_name,
                   sm.movement_type, sm.quantity, sm.reason, sm.created_at
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.id
        """
        params = []
        
        if start_date and end_date:
            query += " WHERE sm.created_at BETWEEN ? AND ?"
            params = [start_date, end_date]
        elif start_date:
            query += " WHERE sm.created_at >= ?"
            params = [start_date]
        elif end_date:
            query += " WHERE sm.created_at <= ?"
            params = [end_date]
        
        query += " ORDER BY sm.created_at DESC"
        
        return self.conn.execute(query, params).fetchall()

    # ==========================================
    # Profit & Loss Reports
    # ==========================================

    def get_ledger_account_balance(self, account_name, column_calc, date_clause=""):
        """
        Get balance for a specific ledger account
        account_name: Name of the account (e.g., 'Sales Revenue')
        column_calc: SQL calculation (e.g., 'SUM(credit) - SUM(debit)')
        date_clause: SQL WHERE clause for date filtering
        """
        query = f"""
            SELECT {column_calc} as balance
            FROM journal_lines l
            JOIN journal_entries e ON l.entry_id = e.id
            JOIN accounts_ledger a ON l.account_id = a.id
            WHERE a.name = ? {date_clause}
        """
        result = self.conn.execute(query, (account_name,)).fetchone()
        return result[0] if result and result[0] else 0.0

    def get_expense_breakdown(self, date_clause=""):
        """Get breakdown of expenses by description"""
        query = f"""
            SELECT e.description, SUM(l.debit) as total
            FROM journal_entries e
            JOIN journal_lines l ON e.id = l.entry_id
            JOIN accounts_ledger a ON l.account_id = a.id
            WHERE a.name = 'General Expense' {date_clause}
            GROUP BY e.description
            ORDER BY total DESC
        """
        return self.conn.execute(query).fetchall()

    def get_revenue_by_period(self, period_type="day", start_date=None, end_date=None):
        """
        Get revenue grouped by day, week, or month
        period_type: 'day', 'week', 'month'
        """
        if period_type == "day":
            group_by = "date(e.date)"
        elif period_type == "week":
            group_by = "strftime('%Y-%W', e.date)"
        else:  # month
            group_by = "strftime('%Y-%m', e.date)"
        
        query = f"""
            SELECT {group_by} as period, SUM(l.credit) as total
            FROM journal_entries e
            JOIN journal_lines l ON e.id = l.entry_id
            JOIN accounts_ledger a ON l.account_id = a.id
            WHERE a.name = 'Sales Revenue'
        """
        params = []
        
        if start_date and end_date:
            query += " AND e.date BETWEEN ? AND ?"
            params = [start_date, end_date]
        
        query += f" GROUP BY period ORDER BY period ASC"
        
        return self.conn.execute(query, params).fetchall()

    # ==========================================
    # Dashboard / Summary Reports
    # ==========================================

    def get_dashboard_summary(self):
        """Get key metrics for dashboard"""
        return self.conn.execute("""
            SELECT 
                (SELECT COUNT(*) FROM products) as total_products,
                (SELECT COUNT(*) FROM products WHERE quantity <= min_threshold) as low_stock_count,
                (SELECT COUNT(*) FROM invoices) as total_invoices,
                (SELECT SUM(total) FROM invoices) as total_sales,
                (SELECT COUNT(*) FROM accounts WHERE role = 'Customer') as total_customers,
                (SELECT COUNT(*) FROM accounts WHERE role = 'Supplier') as total_suppliers
        """).fetchone()

    def get_top_products(self, limit=10, start_date=None, end_date=None):
        """Get top selling products"""
        query = """
            SELECT p.id, p.name, SUM(ii.quantity) as total_sold, 
                   SUM(ii.quantity * ii.price) as total_revenue
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            JOIN invoices i ON ii.invoice_id = i.id
        """
        params = []
        
        if start_date and end_date:
            query += " WHERE i.date BETWEEN ? AND ?"
            params = [start_date, end_date]
        
        query += """ GROUP BY p.id, p.name 
                     ORDER BY total_sold DESC 
                     LIMIT ?"""
        params.append(limit)
        
        return self.conn.execute(query, params).fetchall()

    # ==========================================
    # Dashboard-specific metrics (no UI SQL)
    # ==========================================

    def get_today_sales_totals(self, today_like_prefix):
        """
        Returns (sales_usd, sales_syp, transactions_count)
        today_like_prefix example: '2026-05-08%'
        """
        sales_usd = self.conn.execute(
            "SELECT COALESCE(SUM(total), 0) FROM invoices WHERE type = 'SALE' AND date LIKE ?",
            (today_like_prefix,),
        ).fetchone()[0]

        sales_syp = self.conn.execute(
            "SELECT COALESCE(SUM(total_syp), 0) FROM invoices WHERE type = 'SALE' AND date LIKE ?",
            (today_like_prefix,),
        ).fetchone()[0]

        trans_count = self.conn.execute(
            "SELECT COUNT(*) FROM invoices WHERE type = 'SALE' AND date LIKE ?",
            (today_like_prefix,),
        ).fetchone()[0]

        return sales_usd, sales_syp, trans_count

    def get_best_selling_products_this_month(self, limit=5):
        """
        Best selling products for current month based on invoice_items quantities
        where invoices.type='SALE'
        Returns list of tuples: [(product_name, total_qty), ...]
        """
        rows = self.conn.execute(
            """
            SELECT p.name, SUM(ii.quantity) as total_sold
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            JOIN products p ON ii.product_id = p.id
            WHERE i.type = 'SALE'
              AND strftime('%Y-%m', i.date) = strftime('%Y-%m', 'now')
            GROUP BY p.id
            ORDER BY total_sold DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return rows

    def get_top_stock_items(self, limit=5):
        """Returns list of tuples: [(product_name, quantity), ...]"""
        return self.conn.execute(
            """
            SELECT name, quantity
            FROM products
            ORDER BY quantity DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def get_best_selling_hours_this_month(self):
        """
        Returns list of tuples: [(hour_int, sales_count), ...]
        where hour is derived from invoices.date
        """
        return self.conn.execute(
            """
            SELECT CAST(strftime('%H', i.date) AS INTEGER) as hour, COUNT(*) as sales_count
            FROM invoices i
            WHERE i.type = 'SALE'
              AND strftime('%Y-%m', i.date) = strftime('%Y-%m', 'now')
            GROUP BY hour
            ORDER BY hour
            """,
        ).fetchall()

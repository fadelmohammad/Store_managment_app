import logging

class ReportRepository:
    def __init__(self, conn):
        self.conn = conn

    # ==========================================
    # Invoice Reports
    # ==========================================

    def get_all_invoices(self, date_clause=""):
        """
        Get all invoices with optional date filter
        date_clause: SQL WHERE clause for date filtering (e.g., "WHERE date >= date('now')")
        """
        query = f"""
            SELECT i.id, i.type, i.date, a.name AS partner_name, 
                   i.total, i.payment_method, i.status, i.tax, i.discount
            FROM invoices i
            LEFT JOIN accounts a ON i.partner_id = a.id
            {date_clause}
            ORDER BY i.id DESC
        """
        return self.conn.execute(query).fetchall()

    def get_invoice_by_id(self, invoice_id):
        """Get a single invoice with partner details"""
        return self.conn.execute("""
            SELECT i.*, a.name as partner_name 
            FROM invoices i 
            LEFT JOIN accounts a ON i.partner_id = a.id 
            WHERE i.id = ?
        """, (invoice_id,)).fetchone()

    def get_invoice_items(self, invoice_id):
        """Get all items for a specific invoice"""
        return self.conn.execute("""
            SELECT p.name, ii.quantity, ii.price, (ii.quantity * ii.price) as subtotal
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = ?
        """, (invoice_id,)).fetchall()

    def get_invoice_count(self, date_clause=""):
        """Get total number of invoices with optional date filter"""
        query = f"SELECT COUNT(*) as count FROM invoices i {date_clause}"
        result = self.conn.execute(query).fetchone()
        return result[0] if result else 0

    def get_invoice_total_sum(self, date_clause=""):
        """Get sum of all invoice totals with optional date filter"""
        query = f"SELECT SUM(total) as total FROM invoices i {date_clause}"
        result = self.conn.execute(query).fetchone()
        return result[0] if result and result[0] else 0.0

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

    def get_stock_value_by_category(self):
        """Get inventory value grouped by category"""
        return self.conn.execute("""
            SELECT c.name as category, SUM(p.quantity * p.cost) as total_value
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            GROUP BY c.id, c.name
            ORDER BY total_value DESC
        """).fetchall()

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

    def get_movements_by_product(self, product_id, start_date=None, end_date=None):
        """Get stock movements for a specific product"""
        query = """
            SELECT sm.id, sm.movement_type, sm.quantity, sm.reason, sm.created_at
            FROM stock_movements sm
            WHERE sm.product_id = ?
        """
        params = [product_id]
        
        if start_date and end_date:
            query += " AND sm.created_at BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND sm.created_at >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND sm.created_at <= ?"
            params.append(end_date)
        
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

import logging
from datetime import datetime


class ReportingService:
    def __init__(self, report_repo, product_repo, stock_repo):
        """
        Initialize ReportingService with required repositories
        """
        self.report_repo = report_repo
        self.product_repo = product_repo
        self.stock_repo = stock_repo

    # ==========================================
    # Helper Methods
    # ==========================================

    def _get_date_clause_from_period(self, period, table_alias=""):
        """
        Convert period string to SQL date clause
        period: "Today", "Last 7 Days", "This Month", "All Time"
        table_alias: Optional table alias (e.g., "i." for invoices)
        """
        prefix = f"{table_alias}" if table_alias else ""
        
        if period == "Today":
            return f"WHERE {prefix}date >= date('now')"
        elif period == "Last 7 Days":
            return f"WHERE {prefix}date >= date('now', '-7 days')"
        elif period == "This Month":
            return f"WHERE {prefix}date >= date('now', 'start of month')"
        else:
            return ""

    def _get_date_filter_for_ledger(self, period):
        """Get date filter for ledger/journals (uses e.date format)"""
        if period == "Today":
            return "AND e.date >= date('now')"
        elif period == "Last 7 Days":
            return "AND e.date >= date('now', '-7 days')"
        elif period == "This Month":
            return "AND e.date >= date('now', 'start of month')"
        return ""

    # ==========================================
    # Invoice Reports
    # ==========================================

    def get_invoices(self, period="All Time"):
        """Get all invoices with date filter"""
        date_clause = self._get_date_clause_from_period(period, "")
        return self.report_repo.get_all_invoices(date_clause)

    def get_invoice_details(self, invoice_id):
        """Get full details of a specific invoice"""
        invoice = self.report_repo.get_invoice_by_id(invoice_id)
        if not invoice:
            return None, None
        
        items = self.report_repo.get_invoice_items(invoice_id)
        return invoice, items

    def get_invoice_summary(self, period="All Time"):
        """Get summary statistics for invoices"""
        date_clause = self._get_date_clause_from_period(period, "")
        
        return {
            "count": self.report_repo.get_invoice_count(date_clause),
            "total": self.report_repo.get_invoice_total_sum(date_clause)
        }

    # ==========================================
    # Inventory Reports
    # ==========================================

    # report_service.py - في دالة get_inventory_report

    def get_inventory_report(self):
        """Get complete inventory report with all products"""
        try:
            logging.info("Getting inventory report...")
            
            products = self.report_repo.get_all_products_for_report()
            logging.debug(f"Raw products from repo: {len(products) if products else 0}")
            
            total_value = self.report_repo.get_total_inventory_value()
            logging.info(f"Total inventory value: {total_value}")
            
            low_stock = self.report_repo.get_low_stock_products(5)
            
            formatted_products = [dict(p) for p in products]
            logging.debug(f"Formatted {len(formatted_products)} products")
            
            return {
                "products": formatted_products,
                "total_value": total_value if total_value else 0,
                "low_stock_count": len(low_stock) if low_stock else 0,
                "low_stock_products": low_stock if low_stock else []
            }
        except Exception as e:
            logging.error(f"Error in get_inventory_report: {e}", exc_info=True)
            return {
                "products": [],
                "total_value": 0,
                "low_stock_count": 0,
                "low_stock_products": []
            }
        
    def get_stock_movements(self, start_date=None, end_date=None, period="All Time"):
        """Get stock movements with optional date filter"""
        if period != "All Time":
            # Convert period to dates if needed
            pass
        
        return self.report_repo.get_stock_movements(start_date, end_date)

    # ==========================================
    # Profit & Loss Reports
    # ==========================================

    def get_financial_report(self, period="All Time"):
        """
        Generate complete Profit & Loss statement
        Returns dictionary with sales, cogs, expenses, net_profit
        """
        date_clause = self._get_date_filter_for_ledger(period)
        
        try:
            revenue = self.report_repo.get_ledger_account_balance(
                'Sales Revenue', 'SUM(credit) - SUM(debit)', date_clause
            )
            cogs = self.report_repo.get_ledger_account_balance(
                'Cost of Goods Sold', 'SUM(debit) - SUM(credit)', date_clause
            )
            expenses = self.report_repo.get_ledger_account_balance(
                'General Expense', 'SUM(debit) - SUM(credit)', date_clause
            )
            
            net_profit = revenue - cogs - expenses
            
            # Get expense breakdown
            expense_breakdown = self.report_repo.get_expense_breakdown(date_clause)
            
            formatted_expenses = [dict(exp) for exp in expense_breakdown]
            
            return {
                "sales": revenue,
                "cogs": cogs,
                "expenses": expenses,
                "net_profit": net_profit,
                "expense_breakdown": formatted_expenses,
                "period": period
            }
            
        except Exception as e:
            logging.error(f"Error in get_financial_report: {e}", exc_info=True)
            return {
                "sales": 0.0,
                "cogs": 0.0,
                "expenses": 0.0,
                "net_profit": 0.0,
                "expense_breakdown": [],
                "period": period,
                "error": str(e)
            }

    def get_sales_trend(self, period="All Time"):
        """Get sales trend data for charts"""
        date_clause = self._get_date_filter_for_ledger(period)
        
        # Determine grouping based on period
        if period == "Today":
            group_by = "hour"
        elif period == "Last 7 Days":
            group_by = "day"
        else:
            group_by = "day"
        
        # For now, return revenue by day
        revenue_data = self.report_repo.get_revenue_by_period(
            period_type="day" if group_by == "day" else "month"
        )
        
        days = [row['period'] for row in revenue_data]
        sales = [row['total'] or 0 for row in revenue_data]
        return days, sales

    # ==========================================
    # Dashboard Reports
    # ==========================================

    def get_dashboard_summary(self):
        """Get all metrics for dashboard"""
        return self.report_repo.get_dashboard_summary()

    def get_top_products(self, limit=10, period="All Time"):
        """Get top selling products"""
        # For now, ignore period for top products
        return self.report_repo.get_top_products(limit)
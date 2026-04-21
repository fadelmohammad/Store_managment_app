# reports_module.py

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime

class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent, app, db):
        super().__init__(parent)
        self.app = app
        self.db = db

        # --- NAVIGATION BAR ---
        nav_bar = ctk.CTkFrame(self, fg_color="transparent")
        nav_bar.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkButton(nav_bar, text="Back", width=100, fg_color="#444444", hover_color="#555555",
                      command=self.app.go_back).pack(side="left", padx=5)
        ctk.CTkButton(nav_bar, text="Home", width=100, command=self.app.go_home).pack(side="left", padx=5)

        # Date Filter
        self.period_var = ctk.StringVar(value="All Time")
        self.period_menu = ctk.CTkComboBox(nav_bar,
                                           values=["Today", "Last 7 Days", "This Month", "All Time"],
                                           variable=self.period_var,
                                           command=lambda _: self.refresh_reports())
        self.period_menu.pack(side="left", padx=20)

        ctk.CTkLabel(nav_bar,
        text="Business Intelligence & Reports",
        font=("Arial", 16, "bold")).pack(side="right",padx=20)

        # --- TABVIEW ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_pl = self.tabs.add("Profit & Loss")
        self.tab_inv_list = self.tabs.add("Invoices")  # NEW TAB
        self.tab_stock = self.tabs.add("Inventory Report")

        self.setup_pl_tab()
        self.setup_invoice_tab() # NEW SETUP
        self.setup_stock_tab()

        # Initial Load
        self.refresh_reports()

    # ==========================================
    # INVOICE EXPLORER SECTION (NEW)
    # ==========================================
    def setup_invoice_tab(self):
        header = ctk.CTkFrame(self.tab_inv_list, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header, text="Transaction History", font=("Arial", 20, "bold")).pack(side="left")
        
        ctk.CTkButton(header, text="View Selected Details", width=150, 
                      command=self.open_invoice_details).pack(side="right", padx=5)

        # Invoice Table
        cols = ("ID", "Type", "Date", "Customer/Supplier", "Total", "Method", "Status")
        self.inv_tree = ttk.Treeview(self.tab_inv_list, columns=cols, show="headings")
        for col in cols:
            self.inv_tree.heading(col, text=col)
            self.inv_tree.column(col, width=100 if col != "Date" else 180)
        
        self.inv_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.inv_tree.bind("<Double-1>", lambda e: self.open_invoice_details())

    def open_invoice_details(self):
        sel = self.inv_tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "Please select an invoice to view.")
            return
        
        inv_id = self.inv_tree.item(sel[0])["values"][0]
        
        # Create a Detail Window
        detail_win = ctk.CTkToplevel(self)
        detail_win.title(f"Invoice Details - #{inv_id}")
        detail_win.geometry("600x500")
        detail_win.attributes("-topmost", True)

        # Fetch Data
        inv_data = self.db.cursor.execute("""
            SELECT i.*, a.name as partner_name 
            FROM invoices i 
            LEFT JOIN accounts a ON i.partner_id = a.id 
            WHERE i.id = ?
        """, (inv_id,)).fetchone()

        items = self.db.cursor.execute("""
            SELECT p.name, ii.quantity, ii.price, (ii.quantity * ii.price) as subtotal
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = ?
        """, (inv_id,)).fetchall()

        # UI for Detail Window
        top_f = ctk.CTkFrame(detail_win)
        top_f.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(top_f, text=f"Invoice #{inv_id}", font=("Arial", 18, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top_f, text=f"Partner: {inv_data['partner_name']}").grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(top_f, text=f"Date: {inv_data['date']}").grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(top_f, text=f"Method: {inv_data['payment_method']}").grid(row=1, column=1, sticky="e")
        top_f.grid_columnconfigure(1, weight=1)

        # Items Table
        item_cols = ("Product", "Qty", "Price", "Subtotal")
        tree = ttk.Treeview(detail_win, columns=item_cols, show="headings", height=8)
        for c in item_cols:
            tree.heading(c, text=c)
            tree.column(c, width=100)
        tree.pack(fill="both", expand=True, padx=20)

        for item in items:
            tree.insert("", "end", values=(item[0], item[1], f"€{item[2]:.2f}", f"€{item[3]:.2f}"))

        # Footer
        bot_f = ctk.CTkFrame(detail_win, fg_color="transparent")
        bot_f.pack(fill="x", padx=20, pady=20)
        
        summary_text = (f"Tax: €{inv_data['tax']:.2f}    "
                        f"Discount: €{inv_data['discount']:.2f}    "
                        f"TOTAL: €{inv_data['total']:.2f}")
        
        ctk.CTkLabel(bot_f, text=summary_text, font=("Arial", 14, "bold")).pack(side="right")

    # ==========================================
    # PROFIT & LOSS SECTION
    # ==========================================
    def setup_pl_tab(self):
        header = ctk.CTkFrame(self.tab_pl, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text="Financial Performance Statement", font=("Arial", 20, "bold")).pack(side="left")
        ctk.CTkButton(header, text="Refresh Data", width=120, command=self.refresh_reports).pack(side="right")

        cards_frame = ctk.CTkFrame(self.tab_pl, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=10)
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.sales_card = self.create_stat_card(cards_frame, 0, 0, "TOTAL REVENUE", "#2ecc71")
        self.cogs_card = self.create_stat_card(cards_frame, 0, 1, "COST OF SALES", "#e67e22")
        self.expense_card = self.create_stat_card(cards_frame, 0, 2, "EXPENSES", "#e74c3c")
        self.profit_card = self.create_stat_card(cards_frame, 0, 3, "NET PROFIT", "#3498db")

        ctk.CTkLabel(self.tab_pl, text="Expense Breakdown", font=("Arial", 14, "bold")).pack(pady=(20, 5), padx=10, anchor="w")
        cols = ("Category", "Total Spent")
        self.expense_tree = ttk.Treeview(self.tab_pl, columns=cols, show="headings", height=10)
        for col in cols: self.expense_tree.heading(col, text=col)
        self.expense_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def create_stat_card(self, parent, r, c, title, color):
        frame = ctk.CTkFrame(parent, border_width=2, border_color=color)
        frame.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(frame, text=title, font=("Arial", 12, "bold"), text_color=color).pack(pady=(10, 0))
        val_label = ctk.CTkLabel(frame, text="€0.00", font=("Arial", 24, "bold"))
        val_label.pack(pady=(0, 10))
        return val_label

    # ==========================================
    # INVENTORY REPORT SECTION
    # ==========================================
    def setup_stock_tab(self):
        header = ctk.CTkFrame(self.tab_stock, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text="Stock Valuation & Levels", font=("Arial", 20, "bold")).pack(side="left")
        self.stock_val_lbl = ctk.CTkLabel(header, text="Total Inventory Value: €0.00", font=("Arial", 16, "bold"), text_color="#f1c40f")
        self.stock_val_lbl.pack(side="right", padx=20)

        cols = ("SKU", "Product Name", "In Stock", "Avg Cost", "Retail Price", "Asset Value")
        self.stock_tree = ttk.Treeview(self.tab_stock, columns=cols, show="headings")
        for col in cols:
            self.stock_tree.heading(col, text=col)
            self.stock_tree.column(col, width=120)
        self.stock_tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ==========================================
    # DATA CALCULATION LOGIC
    # ==========================================
    def refresh_reports(self):
        self.calculate_pl()
        self.calculate_inventory()
        self.load_invoices() # NEW

    def load_invoices(self):
        """Loads and filters the invoice list."""
        for i in self.inv_tree.get_children(): self.inv_tree.delete(i)
        
        # Use a version of get_date_filter compatible with invoices table 'date' column
        period = self.period_var.get()
        if period == "Today":
            date_clause = "WHERE date >= date('now')"
        elif period == "Last 7 Days":
            date_clause = "WHERE date >= date('now', '-7 days')"
        elif period == "This Month":
            date_clause = "WHERE date >= date('now', 'start of month')"
        else:
            date_clause = ""

        query = f"""
            SELECT i.id, i.type, i.date, a.name AS partner_name, i.total, i.payment_method, i.status, i.total_syp
            FROM invoices i
            LEFT JOIN accounts a ON i.partner_id = a.id
            {date_clause}
            ORDER BY i.id DESC
        """
        rows = self.db.cursor.execute(query).fetchall()
        
        for r in rows:
            self.inv_tree.insert("", "end", values=(
                r["id"], 
                r["type"], 
                r["date"], 
                r["partner_name"] if r["partner_name"] else "Walk-in", 
                f"€{r['total']:.2f}",  # Matches P&L currency
                r["payment_method"],
                r["status"]
            ))

    def calculate_pl(self):
        date_clause = self.get_date_filter()
        try:
            def get_total(account_name, column_calc):
                query = f"""
                    SELECT {column_calc} FROM journal_lines l
                    JOIN journal_entries e ON l.entry_id = e.id
                    JOIN accounts_ledger a ON l.account_id = a.id
                    WHERE a.name = ? {date_clause}
                """
                return self.db.cursor.execute(query, (account_name,)).fetchone()[0] or 0.0

            revenue = get_total('Sales Revenue', 'SUM(credit) - SUM(debit)')
            cogs = get_total('Cost of Goods Sold', 'SUM(debit) - SUM(credit)')
            expenses = get_total('General Expense', 'SUM(debit) - SUM(credit)')
            net_profit = revenue - cogs - expenses

            self.sales_card.configure(text=f"€{revenue:,.2f}")
            self.cogs_card.configure(text=f"€{cogs:,.2f}")
            self.expense_card.configure(text=f"€{expenses:,.2f}")
            self.profit_card.configure(text=f"€{net_profit:,.2f}",
                                       text_color="#2ecc71" if net_profit >= 0 else "#e74c3c")

            for i in self.expense_tree.get_children(): self.expense_tree.delete(i)
            expense_details = self.db.cursor.execute(f"""
                SELECT e.description, SUM(l.debit) as total
                FROM journal_entries e
                JOIN journal_lines l ON e.id = l.entry_id
                JOIN accounts_ledger a ON l.account_id = a.id
                WHERE a.name = 'General Expense' {date_clause}
                GROUP BY e.description
            """).fetchall()

            for row in expense_details:
                self.expense_tree.insert("", "end", values=(row[0], f"€{row[1]:,.2f}"))
        except Exception as e:
            print(f"P&L Error: {e}")

    def calculate_inventory(self):
        try:
            for i in self.stock_tree.get_children(): self.stock_tree.delete(i)
            products = self.db.cursor.execute("SELECT * FROM products").fetchall()
            total_valuation = 0.0
            for p in products:
                asset_value = p["quantity"] * p["cost"]
                total_valuation += asset_value
                tags = ("low_stock",) if p["quantity"] <= 5 else ()
                self.stock_tree.insert("", "end", values=(
                    p["id"], p["name"], p["quantity"],
                    f"€{p['cost']:,.2f}", f"€{p['price']:,.2f}",
                    f"€{asset_value:,.2f}"
                ), tags=tags)
            self.stock_val_lbl.configure(text=f"Total Inventory Value: €{total_valuation:,.2f}")
            self.stock_tree.tag_configure("low_stock", foreground="#e74c3c")
        except Exception as e:
            print(f"Inventory Report Error: {e}")

    def get_date_filter(self):
        period = self.period_var.get()
        if period == "Today": return "AND e.date >= date('now')"
        elif period == "Last 7 Days": return "AND e.date >= date('now', '-7 days')"
        elif period == "This Month": return "AND e.date >= date('now', 'start of month')"
        return ""
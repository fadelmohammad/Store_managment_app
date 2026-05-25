# print_dialog.py

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk


class PrintDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Print Data")
        self.geometry("600x700")  # Changed from 500x650 to 600x700 for wider and taller dialog
        self.resizable(False, False)
        
        # Center the dialog on the parent window
        self.transient(parent)
        self.grab_set()  # Make this window modal
        
        # Bring to front and force focus
        self.lift()
        self.focus_force()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.create_widgets()
        
        # Ensure the dialog appears properly
        self.wait_visibility()
    
    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Select Data to Print", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 20))
        
        # Data type selection
        data_type_frame = ctk.CTkFrame(main_frame)
        data_type_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        data_type_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            data_type_frame, 
            text="What would you like to print?", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        self.data_type_var = ctk.StringVar(value="inventory")
        data_types = [
            ("Inventory Report", "inventory"),
            ("Sales Report", "sales"),
            ("Purchase Report", "purchases"),
            ("Customers/Suppliers", "accounts"),
            ("Categories", "categories")
        ]
        
        for i, (text, value) in enumerate(data_types):
            radio_btn = ctk.CTkRadioButton(
                data_type_frame,
                text=text,
                variable=self.data_type_var,
                value=value,
                command=self.on_data_type_change
            )
            radio_btn.grid(row=i+1, column=0, sticky="w", padx=30, pady=5)
        
        # Options frame
        self.options_frame = ctk.CTkFrame(main_frame)
        self.options_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        self.options_frame.grid_columnconfigure(0, weight=1)
        
        # Initially show inventory options
        self.show_inventory_options()
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkButton(
            button_frame,
            text="Print",
            command=self.on_print_clicked,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            height=40
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            height=40
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    def on_data_type_change(self):
        """Handle data type selection change"""
        # Clear the options frame
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Show appropriate options based on selection
        data_type = self.data_type_var.get()
        if data_type == "inventory":
            self.show_inventory_options()
        elif data_type == "sales":
            self.show_sales_options()
        elif data_type == "purchases":
            self.show_purchases_options()
        elif data_type == "accounts":
            self.show_accounts_options()
        elif data_type == "categories":
            self.show_categories_options()
    
    def show_inventory_options(self):
        """Show options for inventory report"""
        ctk.CTkLabel(
            self.options_frame,
            text="Inventory Report Options",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        # Include costs option
        self.include_costs_var = ctk.BooleanVar(value=True)
        costs_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Include cost information",
            variable=self.include_costs_var
        )
        costs_checkbox.pack(anchor="w", padx=30, pady=5)
        
        # Include prices option
        self.include_prices_var = ctk.BooleanVar(value=True)
        prices_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Include price information",
            variable=self.include_prices_var
        )
        prices_checkbox.pack(anchor="w", padx=30, pady=5)
        
        # Include stock option
        self.include_stock_var = ctk.BooleanVar(value=True)
        stock_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Include stock information",
            variable=self.include_stock_var
        )
        stock_checkbox.pack(anchor="w", padx=30, pady=5)
        
        # Filter options
        ctk.CTkLabel(
            self.options_frame,
            text="Filter Options:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(15, 5))
        
        # Category filter
        ctk.CTkLabel(
            self.options_frame,
            text="Category:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30, pady=2)
        
        # Get categories from inventory service
        categories = ["All"]  # Default
        try:
            cats = self.app.inventory_service.get_categories()
            categories.extend([cat.get("path", cat.get("name", "Unknown")) for cat in cats])
        except:
            pass  # Use default if service unavailable
        
        self.category_filter_var = ctk.StringVar(value="All")
        self.category_dropdown = ctk.CTkOptionMenu(
            self.options_frame,
            variable=self.category_filter_var,
            values=categories
        )
        self.category_dropdown.pack(anchor="w", padx=30, pady=5)
        
        # Stock level filter
        ctk.CTkLabel(
            self.options_frame,
            text="Stock Level:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30, pady=2)
        
        self.stock_filter_var = ctk.StringVar(value="All")
        self.stock_dropdown = ctk.CTkOptionMenu(
            self.options_frame,
            variable=self.stock_filter_var,
            values=["All", "In Stock", "Low Stock", "Out of Stock"]
        )
        self.stock_dropdown.pack(anchor="w", padx=30, pady=5)
    
    def show_sales_options(self):
        """Show options for sales report"""
        ctk.CTkLabel(
            self.options_frame,
            text="Sales Report Options",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        # Period selection
        ctk.CTkLabel(
            self.options_frame,
            text="Time Period:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30, pady=2)
        
        self.period_var = ctk.StringVar(value="All Time")
        period_dropdown = ctk.CTkOptionMenu(
            self.options_frame,
            variable=self.period_var,
            values=["Today", "Last 7 Days", "This Month", "This Year", "All Time"]
        )
        period_dropdown.pack(anchor="w", padx=30, pady=5)
        
        # Include details option
        self.include_details_var = ctk.BooleanVar(value=True)
        details_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Include detailed item breakdown",
            variable=self.include_details_var
        )
        details_checkbox.pack(anchor="w", padx=30, pady=5)
    
    def show_purchases_options(self):
        """Show options for purchase report"""
        ctk.CTkLabel(
            self.options_frame,
            text="Purchase Report Options",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        # Period selection
        ctk.CTkLabel(
            self.options_frame,
            text="Time Period:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30, pady=2)
        
        self.purchases_period_var = ctk.StringVar(value="All Time")
        period_dropdown = ctk.CTkOptionMenu(
            self.options_frame,
            variable=self.purchases_period_var,
            values=["Today", "Last 7 Days", "This Month", "This Year", "All Time"]
        )
        period_dropdown.pack(anchor="w", padx=30, pady=5)
        
        # Include details option
        self.include_purchases_details_var = ctk.BooleanVar(value=True)
        details_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Include detailed item breakdown",
            variable=self.include_purchases_details_var
        )
        details_checkbox.pack(anchor="w", padx=30, pady=5)
    
    def show_accounts_options(self):
        """Show options for accounts report"""
        ctk.CTkLabel(
            self.options_frame,
            text="Accounts Report Options",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        # Account type filter
        ctk.CTkLabel(
            self.options_frame,
            text="Account Type:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=30, pady=2)
        
        self.account_type_var = ctk.StringVar(value="All")
        account_type_dropdown = ctk.CTkOptionMenu(
            self.options_frame,
            variable=self.account_type_var,
            values=["All", "Customers", "Suppliers"]
        )
        account_type_dropdown.pack(anchor="w", padx=30, pady=5)
    
    def show_categories_options(self):
        """Show options for categories report"""
        ctk.CTkLabel(
            self.options_frame,
            text="Categories Report Options",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        # Include subcategories option
        self.include_subcats_var = ctk.BooleanVar(value=True)
        subcats_checkbox = ctk.CTkCheckBox(
            self.options_frame,
            text="Include subcategories in hierarchy",
            variable=self.include_subcats_var
        )
        subcats_checkbox.pack(anchor="w", padx=30, pady=5)
    
    def on_print_clicked(self):
        """Handle the print button click"""
        data_type = self.data_type_var.get()
        
        try:
            if data_type == "inventory":
                self.print_inventory_report()
            elif data_type == "sales":
                self.print_sales_report()
            elif data_type == "purchases":
                self.print_purchases_report()
            elif data_type == "accounts":
                self.print_accounts_report()
            elif data_type == "categories":
                self.print_categories_report()
        except Exception as e:
            messagebox.showerror("Print Error", f"An error occurred while printing: {str(e)}")
    
    def print_inventory_report(self):
        """Generate and print inventory report"""
        # Get all products from inventory service
        products = self.app.inventory_service.get_products()
        
        # Apply filters if needed
        category_filter = self.category_filter_var.get()
        stock_filter = self.stock_filter_var.get()
        
        filtered_products = []
        for product in products:
            # Apply category filter
            if category_filter != "All" and product.get("category") != category_filter:
                continue
                
            # Apply stock filter
            qty = product.get("quantity", 0)
            min_thresh = product.get("min_threshold", 0)
            
            if stock_filter == "In Stock" and qty <= 0:
                continue
            elif stock_filter == "Low Stock" and (qty > min_thresh or qty <= 0):
                continue
            elif stock_filter == "Out of Stock" and qty > 0:
                continue
                
            filtered_products.append(product)
        
        # Use print service to generate the report
        if hasattr(self.app, 'print_service'):
            self.app.print_service.print_inventory_report(
                filtered_products,
                include_costs=self.include_costs_var.get(),
                include_prices=self.include_prices_var.get(),
                include_stock=self.include_stock_var.get()
            )
        else:
            messagebox.showerror("Error", "Print service not available")
    
    def print_sales_report(self):
        """Generate and print sales report"""
        period = self.period_var.get()
        
        # Get sales data from report service
        sales_data = self.app.report_service.get_invoices(period)
        
        # Use print service to generate the report
        if hasattr(self.app, 'print_service'):
            self.app.print_service.print_sales_report(sales_data, period)
        else:
            messagebox.showerror("Error", "Print service not available")
    
    def print_purchases_report(self):
        """Generate and print purchases report"""
        period = self.purchases_period_var.get()
        
        # Get purchase data from report service
        # Note: We'll use the same method for invoices but filter for purchases
        purchase_data = self.app.report_service.get_invoices(period)
        
        # Use print service to generate the report
        if hasattr(self.app, 'print_service'):
            self.app.print_service.print_purchase_report(purchase_data, period)
        else:
            messagebox.showerror("Error", "Print service not available")
    
    def print_accounts_report(self):
        """Generate and print accounts report"""
        account_type = self.account_type_var.get()
        
        # Get accounts from account service
        if account_type == "Customers":
            accounts = self.app.account_service.get_by_role("Customer")
        elif account_type == "Suppliers":
            accounts = self.app.account_service.get_by_role("Supplier")
        else:
            # Get both customers and suppliers
            customers = self.app.account_service.get_by_role("Customer")
            suppliers = self.app.account_service.get_by_role("Supplier")
            accounts = customers + suppliers
        
        # Use print service to generate the report
        if hasattr(self.app, 'print_service'):
            self.app.print_service.print_accounts_report(accounts, account_type)
        else:
            messagebox.showerror("Error", "Print service not available")
    
    def print_categories_report(self):
        """Generate and print categories report"""
        # Get categories from inventory service
        categories = self.app.inventory_service.get_categories()
        
        # Use print service to generate the report
        if hasattr(self.app, 'print_service'):
            self.app.print_service.print_categories_report(
                categories, 
                include_subcategories=self.include_subcats_var.get()
            )
        else:
            messagebox.showerror("Error", "Print service not available")
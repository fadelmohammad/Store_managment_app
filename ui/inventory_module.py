# inventory_module.py

import customtkinter as ctk
import logging
from tkinter import ttk, messagebox, Menu
import csv
import os
from datetime import datetime
from collections import defaultdict
from ui.print_dialog import PrintDialog  # Import the print dialog


class InventoryFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.selected_product_id = None
        self.current_rate = 15000
        self.page_size = 25
        self.current_page = 0
        self.filtered_products = []
        self.sort_col = None
        self.sort_reverse = False

        # --- NAVIGATION BAR ---
        nav_bar = ctk.CTkFrame(self, fg_color="transparent")
        nav_bar.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkButton(
            nav_bar,
            text="Back",
            width=100,
            fg_color="#444444",
            hover_color="#555555",
            command=self.app.go_back,
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(nav_bar, text="Home", width=100, command=self.app.go_home).pack(
            side="left", padx=5
        )
        
        # Add Print button
        ctk.CTkButton(
            nav_bar,
            text="Print",
            width=100,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.open_print_dialog
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            nav_bar, text="Inventory Management", font=("Arial", 16, "bold")
        ).pack(side="right", padx=20)

        # --- MAIN CONTENT PANE ---
        pane = ctk.CTkFrame(self)
        pane.pack(fill="both", expand=True, padx=15, pady=10)

        # LEFT side: Product List
        left_panel = ctk.CTkFrame(pane)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Search Bar
        search_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_data())
        ctk.CTkEntry(
            search_frame,
            placeholder_text="Search products...",
            textvariable=self.search_var,
        ).pack(fill="x", padx=5)

        # Low Stock Alerts
        alert_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        alert_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.alert_label = ctk.CTkLabel(alert_frame, text="", font=("Arial", 12, "bold"))
        self.alert_label.pack(side="left")
        
        self.alert_btn = ctk.CTkButton(
            alert_frame, 
            text="Show Low Stock", 
            fg_color="#e74c3c", 
            width=120,
            command=self.show_low_stock_alert
        )
        self.alert_btn.pack(side="right")

        # Filter toolbar - using grid only
        filter_frame = ctk.CTkFrame(left_panel, fg_color="#2b2b2b", corner_radius=8)
        filter_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Configure grid columns
        filter_frame.grid_columnconfigure(0, weight=0)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(2, weight=0)
        filter_frame.grid_columnconfigure(3, weight=1)
        
        # Category filter
        ctk.CTkLabel(filter_frame, text="Category:", font=("Arial", 12)).grid(row=0, column=0, padx=(10, 5), pady=8, sticky="w")
        self.category_filter_var = ctk.StringVar(value="All")
        self.category_filter_var.trace_add("write", lambda *args: self.refresh_data())
        self.category_filter_dropdown = ctk.CTkOptionMenu(
            filter_frame, 
            variable=self.category_filter_var, 
            values=["All"],
            width=150
        )
        self.category_filter_dropdown.grid(row=0, column=1, padx=(0, 15), pady=8, sticky="w")
        
        # Stock filter
        ctk.CTkLabel(filter_frame, text="Stock:", font=("Arial", 12)).grid(row=0, column=2, padx=(5, 5), pady=8, sticky="w")
        self.stock_filter_var = ctk.StringVar(value="All")
        self.stock_filter_var.trace_add("write", lambda *args: self.refresh_data())
        stock_options = ["All", "Low", "Critical"]
        self.stock_filter_dropdown = ctk.CTkOptionMenu(
            filter_frame, 
            variable=self.stock_filter_var, 
            values=stock_options,
            width=150
        )
        self.stock_filter_dropdown.grid(row=0, column=3, padx=(0, 10), pady=8, sticky="w")

        # Treeview
        cols = (
            "ID",
            "Name",
            "Category",
            "Cost ($)",
            "Price ($)",
            "Price (SYP)",
            "Stock",
            "Min",
        )
        
        # Main frame for treeview
        main_tree_frame = ctk.CTkFrame(left_panel)
        main_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tree = ttk.Treeview(main_tree_frame, columns=cols, show="headings", height=15)
        
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=80 if col != "Name" else 150)
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(main_tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="left", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)
        self.tree.bind("<Double-1>", self.on_product_double_click)
        
        # Pagination buttons
        pag_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        pag_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.prev_btn = ctk.CTkButton(pag_frame, text="<< Prev", width=80, command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_label = ctk.CTkLabel(pag_frame, text="Page 1", font=("Arial", 12))
        self.page_label.pack(side="left", padx=10)
        
        self.next_btn = ctk.CTkButton(pag_frame, text="Next >>", width=80, command=self.next_page)
        self.next_btn.pack(side="left", padx=5)
        
        # Export button
        export_btn = ctk.CTkButton(
            left_panel,
            text="📄 Export Filtered to CSV",
            fg_color="#27ae60",
            height=35,
            command=self.export_to_csv
        )
        export_btn.pack(fill="x", padx=10, pady=(5, 10))

        # RIGHT side: Edit/Add Form
        right_panel = ctk.CTkScrollableFrame(pane, width=320)
        right_panel.pack(side="right", fill="y", padx=(10, 0))

        # Mapping to store ID vs Path for the database (used by popup CRUD form)
        self.cat_map = {}
        self.refresh_category_list()

        # Categories helper (kept visible, but without inline product fields)
        ctk.CTkButton(
            right_panel,
            text="+ Manage Categories",
            height=20,
            fg_color="#34495e",
            command=self.open_category_window,
        ).pack(padx=25, pady=(0, 10))

        # Buttons area (CRUD is popup-only now)
        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10, padx=25)

        ctk.CTkButton(
            btn_frame, text="Add Product", fg_color="#27ae60", command=self.add_product
        ).pack(fill="x", pady=5)

        ctk.CTkButton(
            btn_frame,
            text="View History",
            fg_color="#8e44ad",
            hover_color="#9b59b6",
            command=self.show_stock_history,
        ).pack(fill="x", pady=(10, 20))

        # NOTE: Inline product inputs are intentionally removed (popup-only CRUD).

        # Bulk Price Adjustments
        ctk.CTkLabel(
            right_panel,
            text="Bulk Price Adjustments",
            font=("Arial", 14, "bold"),
            text_color="#f1c40f",
        ).pack(pady=(25, 5))

        self.bulk_pct_entry = ctk.CTkEntry(
            right_panel, placeholder_text="Enter % (e.g. 10)"
        )
        self.bulk_pct_entry.pack(fill="x", padx=25, pady=5)

        bulk_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        bulk_btn_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(
            bulk_btn_frame,
            text="Increase All",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            width=100,
            command=lambda: self.apply_bulk_adjustment("UP"),
        ).pack(side="left", padx=5, expand=True)

        ctk.CTkButton(
            bulk_btn_frame,
            text="Decrease All",
            fg_color="#e67e22",
            hover_color="#d35400",
            width=100,
            command=lambda: self.apply_bulk_adjustment("DOWN"),
        ).pack(side="left", padx=5, expand=True)

        # Context menu
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="View Product History", command=self.show_product_history_direct
        )
        self.context_menu.add_command(
            label="View Category History", command=self.show_category_history_direct
        )
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Initial load
        self.update_alert_label()
        self.refresh_data()

    # ==========================================
    # Helper Methods
    # ==========================================

    def create_input(self, parent, label):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=25)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=25, pady=(0, 10))
        return entry

    def get_stock_tags(self, qty, min_th):
        """Return tags for stock level coloring"""
        if qty <= 0:
            return ("critical",)
        elif qty <= min_th:
            return ("low_stock",)
        elif qty <= min_th * 2:
            return ("warning",)
        return ()

    def update_alert_label(self):
        """Update low stock alert label"""
        try:
            products = self.app.inventory_service.get_products()
            low_count = len([p for p in products if p["quantity"] <= p["min_threshold"]])
            if low_count > 0:
                self.alert_label.configure(text=f"⚠️ {low_count} LOW STOCK", text_color="orange")
            else:
                self.alert_label.configure(text="✅ All stock healthy", text_color="green")
        except Exception as e:
            logging.error(f"Error updating alert label: {e}")

    # ==========================================
    # Category Management
    # ==========================================

    def open_category_window(self):
        """Open category management window"""
        from ui.category_module import CategoryManagementWindow
        
        CategoryManagementWindow(
            parent=self,
            category_service=self.app.category_service,
            inventory_service=self.app.inventory_service,
            refresh_callback=self.refresh_category_list
        )

    def refresh_category_list(self):
        """Updates the dropdown with the latest category paths."""
        try:
            logging.debug("Refreshing category list...")
            cats = self.app.inventory_service.get_categories()
            logging.debug(f"Received {len(cats)} categories from service")
            
            if not cats:
                logging.warning("No categories found! Check database.")
                self.cat_map = {}
                if hasattr(self, "cat_dropdown"):
                    self.cat_dropdown.configure(values=["No Categories"])
                if hasattr(self, "category_filter_dropdown"):
                    self.category_filter_dropdown.configure(values=["All"])
                return
            
            self.cat_map = {}
            for c in cats:
                path = c.get("path", c.get("name", "بدون اسم"))
                cat_id = c.get("id")
                self.cat_map[path] = cat_id
                logging.debug(f"Mapped: {path} -> ID: {cat_id}")
            
            paths = list(self.cat_map.keys())
            filter_paths = ["All"] + paths
            logging.debug(f"Dropdown values: {paths}")
            if hasattr(self, "cat_dropdown"):
                self.cat_dropdown.configure(values=paths if paths else ["No Categories"])
            if hasattr(self, "category_filter_dropdown"):
                self.category_filter_dropdown.configure(values=filter_paths)
            
        except Exception as e:
            logging.error(f"Error in refresh_category_list: {e}", exc_info=True)
            if hasattr(self, "cat_dropdown"):
                self.cat_dropdown.configure(values=["Error loading categories"])
            if hasattr(self, "category_filter_dropdown"):
                self.category_filter_dropdown.configure(values=["All"])

    # ==========================================
    # Filtering, Sorting & Pagination
    # ==========================================

    def refresh_data(self):
        """Refresh product list with filters and pagination"""
        search = self.search_var.get().lower()
        cat_filter = self.category_filter_var.get()
        stock_filter = self.stock_filter_var.get()

        # Pull dynamic rate from app
        self.current_rate = getattr(self.app, "exchange_rate", 15000)
        products = self.app.inventory_service.get_products()
        
        # Apply filters
        self.filtered_products = []
        for p in products:
            # Search filter
            if search and search not in p["name"].lower() and search not in p["category"].lower():
                continue
            
            # Category filter
            if cat_filter != "All" and p["category"] != cat_filter:
                continue

            # Stock filter
            qty = p["quantity"]
            min_th = p["min_threshold"] or 0
            if stock_filter == "Low" and qty > min_th:
                continue
            if stock_filter == "Critical" and qty > 0 and qty < (min_th * 0.3):
                continue

            self.filtered_products.append(p)
        
        # Sort if sort column set
        if self.sort_col:
            self.filtered_products.sort(key=lambda p: self.get_sort_key(p, self.sort_col), reverse=self.sort_reverse)
        
        self.current_page = 0
        self.populate_tree()
        self.update_page_label()
        self.update_pagination_buttons()

    def get_sort_key(self, p, col):
        """Get sort key for product"""
        val = p.get(col, 0)
        if col in ["Stock", "Min", "id"]:
            try:
                return float(val)
            except:
                return 0
        return str(val).lower()

    def sort_by_column(self, col):
        """Sort tree by column"""
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
        self.refresh_data()

    def populate_tree(self):
        """Populate tree with current page products"""
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_products = self.filtered_products[start:end]
        
        # Configure tags for coloring
        self.tree.tag_configure("low_stock", background="#C54141")
        self.tree.tag_configure("critical", background="#E64F6F")
        self.tree.tag_configure("warning", background="#3D85D8")
        
        for p in page_products:
            live_syp = p["price"] * self.current_rate
            qty = p["quantity"]
            min_th = p["min_threshold"]
            
            # Determine row color based on stock status
            if qty <= 0:
                tags = ("critical",)
            elif qty <= min_th:
                tags = ("low_stock",)
            elif qty <= min_th * 2:
                tags = ("warning",)
            else:
                tags = ()
            
            self.tree.insert(
                "",
                "end",
                iid=str(p["id"]),
                values=(
                    p["id"],
                    p["name"],
                    p["category"],
                    f"${p['cost']:.2f}",
                    f"${p['price']:.2f}",
                    f"{live_syp:,.0f} SYP",
                    p["quantity"],
                    p["min_threshold"],
                ),
                tags=tags,
            )

    def update_page_label(self):
        """Update page label text"""
        total_pages = (len(self.filtered_products) + self.page_size - 1) // self.page_size
        self.page_label.configure(text=f"Page {self.current_page + 1} / {total_pages or 1} ({len(self.filtered_products)} items)")
    
    def update_pagination_buttons(self):
        """Update pagination button states"""
        total_pages = (len(self.filtered_products) + self.page_size - 1) // self.page_size
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.populate_tree()
            self.update_page_label()
            self.update_pagination_buttons()
    
    def next_page(self):
        """Go to next page"""
        total_pages = (len(self.filtered_products) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.populate_tree()
            self.update_page_label()
            self.update_pagination_buttons()

    # ==========================================
    # Product CRUD Operations
    # ==========================================

    def on_product_select(self, event):
        """Handle product selection from tree (popup-only mode)."""
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_product_id = sel[0]

    def on_product_double_click(self, _event):
        """Double-click opens popup with Update + Delete."""
        sel = self.tree.selection()
        if sel:
            self.selected_product_id = sel[0]

        if self.selected_product_id is None:
            return

        # Defensive: always pass correct mode first.
        self.open_product_edit_popup("EDIT", self.selected_product_id)

    # ==========================================
    # Popup CRUD (Add/Update/Delete)
    # ==========================================

    def open_product_edit_popup(self, mode: str, product_id=None):
        """
        mode:
          - "ADD": popup for creating a product (Add button only)
          - "EDIT": popup for updating/deleting an existing product
        """
        # Defensive: sometimes Tkinter callbacks end up passing wrong args (e.g. mode=1).
        if not isinstance(mode, str):
            mode = "EDIT"

        if mode not in {"ADD", "EDIT"}:
            mode = "EDIT"

        product = None
        if mode == "EDIT":
            if product_id is None:
                messagebox.showwarning("Selection Required", "Please select a product first.", parent=self)
                return
            product = self.app.inventory_service.get_product_by_id(product_id)
            if not product:
                messagebox.showerror("Error", "Product not found.", parent=self)
                return

        win = ctk.CTkToplevel(self)
        win.title("Add Product" if mode == "ADD" else "Edit Product")
        win.geometry("460x640")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        # win.grab_set()  # removing focus grab to ensure CTk buttons are clickable

        title_txt = "Add Product" if mode == "ADD" else f"Edit: {product.get('name', '')}"
        ctk.CTkLabel(win, text=title_txt, font=("Arial", 16, "bold")).pack(pady=(16, 8))

        # variables
        name_var = ctk.StringVar(value=(product.get("name", "") if product else ""))
        price_var = ctk.StringVar(value=str(product.get("price", 0) if product else 0))
        cost_var = ctk.StringVar(value=str(product.get("cost", 0) if product else 0))
        qty_var = ctk.StringVar(value=str(product.get("quantity", 0) if product else 0))
        min_var = ctk.StringVar(value=str(product.get("min_threshold", 5) if product else 5))
        category_var = ctk.StringVar(
            value=(product.get("category_path") if product and product.get("category_path") else "Select Category")
        )

        # category dropdown values from current map keys
        category_values = list(self.cat_map.keys()) if self.cat_map else ["Select Category"]

        def labeled(parent, label: str, var: ctk.StringVar):
            ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=20, pady=(8, 3))
            e = ctk.CTkEntry(parent, textvariable=var)
            e.pack(fill="x", padx=20)
            return e

        if not category_values:
            category_values = ["Select Category"]

        # category
        ctk.CTkLabel(win, text="Category").pack(anchor="w", padx=20, pady=(10, 3))
        cat_dd = ctk.CTkOptionMenu(win, variable=category_var, values=category_values, width=330)
        cat_dd.pack(fill="x", padx=20)

        ctk.CTkButton(
            win,
            text="+ Manage Categories",
            height=28,
            fg_color="#34495e",
            command=self.open_category_window,
        ).pack(padx=20, pady=(6, 10), fill="x")

        # fields
        labeled(win, "Product Name", name_var)
        labeled(win, "Retail Price ($)", price_var)
        labeled(win, "Unit Cost ($)", cost_var)
        labeled(win, "Current Stock", qty_var)
        labeled(win, "Min Threshold (Alert)", min_var)

        actions = ctk.CTkFrame(win, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(16, 6))

        def read_validate():
            name = name_var.get().strip()
            if not name:
                raise ValueError("Product name is required")

            selected_path = category_var.get()
            cat_id = self.cat_map.get(selected_path, None)

            price = float(price_var.get() or 0)
            cost = float(cost_var.get() or 0)
            qty = int(float(qty_var.get() or 0))
            min_threshold = int(float(min_var.get() or 5))

            if qty < 0:
                raise ValueError("Quantity cannot be negative")
            if min_threshold < 0:
                raise ValueError("Min threshold cannot be negative")

            return name, cat_id, price, cost, qty, min_threshold

        def on_add():
            try:
                name, cat_id, price, cost, qty, min_threshold = read_validate()
                self.app.inventory_service.add_product(name, cat_id, price, cost, qty, min_threshold)
                self.refresh_data()
                self.update_alert_label()
                win.destroy()
                messagebox.showinfo("Success", "Product added successfully.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        def on_update():
            try:
                name, cat_id, price, cost, qty, min_threshold = read_validate()
                self.app.inventory_service.update_product(product["id"], name, cat_id, price, cost, qty, min_threshold)
                self.refresh_data()
                self.update_alert_label()
                win.destroy()
                messagebox.showinfo("Success", "Product updated successfully.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        def on_delete():
            if not messagebox.askyesno(
                "Confirm Delete",
                f"Delete '{product.get('name', '')}'?",
                parent=win,
            ):
                return
            try:
                self.app.inventory_service.delete_product(product["id"])
                self.refresh_data()
                self.update_alert_label()
                win.destroy()
                messagebox.showinfo("Success", "Product deleted successfully.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        if mode == "ADD":
            ctk.CTkButton(actions, text="Add", fg_color="#27ae60", command=on_add).pack(fill="x", pady=6)
        else:
            ctk.CTkButton(actions, text="Update", fg_color="#2980b9", command=on_update).pack(fill="x", pady=6)
            ctk.CTkButton(actions, text="Delete", fg_color="#e74c3c", command=on_delete).pack(fill="x", pady=6)

        ctk.CTkButton(actions, text="Cancel", fg_color="#7f8c8d", command=win.destroy).pack(fill="x", pady=(6, 0))

        # focus helper
        try:
            win.after(50, lambda: win.focus_force())
        except Exception:
            pass

    def add_product(self):
        """Add product via popup (same form)."""
        self.open_product_edit_popup("ADD")

    # ==========================================
    # Bulk Operations
    # ==========================================

    def apply_bulk_adjustment(self, direction):
        """Process bulk price adjustment"""
        val = self.bulk_pct_entry.get().strip()

        if not val:
            messagebox.showwarning(
                "Input Missing", "Please enter a percentage value first."
            )
            return

        try:
            pct = float(val)
            final_pct = pct if direction == "UP" else -pct
            action_text = "increase" if direction == "UP" else "decrease"
            
            confirm = messagebox.askyesno(
                "Confirm Bulk Action",
                f"This will {action_text} the retail price of ALL products by {pct}%.\n\nAre you sure?",
            )

            if confirm:
                self.app.inventory_service.bulk_update_prices(final_pct)
                self.refresh_data()
                self.bulk_pct_entry.delete(0, "end")
                messagebox.showinfo("Success", f"All prices {action_text}d by {pct}%.")

        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number (e.g. 15).")

    # ==========================================
    # Low Stock Alert
    # ==========================================

    def show_low_stock_alert(self):
        """Show low stock items in a popup"""
        try:
            products = self.app.inventory_service.get_products()
            low_stock = [p for p in products if p["quantity"] <= p["min_threshold"]]
            
            if not low_stock:
                messagebox.showinfo("Good News", "No low stock items!")
                return
            
            alert_win = ctk.CTkToplevel(self)
            alert_win.title("Low Stock Alert")
            alert_win.geometry("600x400")
            alert_win.attributes("-topmost", True)
            
            ctk.CTkLabel(
                alert_win, 
                text=f"⚠️ {len(low_stock)} items need restock!", 
                font=("Arial", 16, "bold"), 
                text_color="#e74c3c"
            ).pack(pady=10)
            
            cols = ("Name", "Category", "Stock", "Min")
            tree = ttk.Treeview(alert_win, columns=cols, show="headings", height=12)
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=120)
            tree.pack(fill="both", expand=True, padx=20, pady=10)
            
            for p in low_stock[:20]:
                tree.insert("", "end", values=(p["name"], p["category"], p["quantity"], p["min_threshold"]))
            
            ctk.CTkButton(
                alert_win, 
                text="Restock All (Double)", 
                fg_color="#e67e22", 
                command=lambda: self.bulk_restock(low_stock)
            ).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def bulk_restock(self, low_stock):
        """Bulk restock low stock items"""
        try:
            for p in low_stock:
                new_qty = p["quantity"] * 2
                self.app.inventory_service.update_product(
                    p["id"], p["name"], p.get("category_id"), 
                    p["price"], p["cost"], new_qty, p["min_threshold"]
                )
            self.refresh_data()
            self.update_alert_label()
            messagebox.showinfo("Restocked", f"Restocked {len(low_stock)} items!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ==========================================
    # Export Functionality
    # ==========================================

    def export_to_csv(self):
        """Export filtered products to CSV"""
        if not self.filtered_products:
            messagebox.showwarning("No Data", "No filtered products to export.")
            return
        
        filename = f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(os.getcwd(), filename)
        
        cols = ["id", "name", "category", "cost", "price", "quantity", "min_threshold"]
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                for p in self.filtered_products:
                    row = {k: p.get(k, '') for k in cols}
                    writer.writerow(row)
            
            messagebox.showinfo("Export Complete", f"Exported {len(self.filtered_products)} items to '{filename}'")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ==========================================
    # Stock History
    # ==========================================

    def show_stock_history(self):
        """Open stock history window with chart and table"""
        if not self.selected_product_id:
            messagebox.showwarning(
                "Selection Required", "Please select a product from the list first."
            )
            return

        product = self.app.inventory_service.get_product_by_id(self.selected_product_id) or {}
        product_name = product.get("name", "Product")
        history_data = self.app.inventory_service.get_product_history(self.selected_product_id)

        history_win = ctk.CTkToplevel(self)
        history_win.title(f"Stock History: {product_name}")
        history_win.geometry("900x600")
        history_win.attributes("-topmost", True)

        tabview = ctk.CTkTabview(history_win)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Table Tab
        table_frame = tabview.add("Movements")
        cols = ("Date", "Type", "Qty", "Reason")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
        tree.heading("Date", text="Date & Time")
        tree.column("Date", width=140)
        tree.heading("Type", text="Type")
        tree.column("Type", width=80)
        tree.heading("Qty", text="Qty")
        tree.column("Qty", width=80)
        tree.heading("Reason", text="Reason")
        tree.column("Reason", width=300)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Chart Tab
        chart_frame = tabview.add("Visual Chart")
        self._create_history_chart(chart_frame, history_data, product_name)

        # Populate table
        if not history_data:
            tree.insert("", "end", values=("-", "NONE", "-", "No history recorded"))
        else:
            for row in history_data:
                if isinstance(row, (list, tuple)):
                    raw_date = row[0]
                    m_type = row[1]
                    qty = row[2]
                    reason = row[3]
                else:
                    raw_date = row.get("date", "")
                    m_type = row.get("movement_type", "")
                    qty = row.get("quantity", 0)
                    reason = row.get("reason", "")

                if m_type in ["IN", "PURCHASE", "INITIAL"]:
                    qty_display = f"+{qty}"
                elif m_type == "ADJUST":
                    qty_display = f"Set to {qty}"
                else:
                    qty_display = f"-{qty}"

                tree.insert("", "end", values=(raw_date, m_type, qty_display, reason))

    def _create_history_chart(self, chart_frame, history_data, product_name):
        """Create matplotlib chart for stock history"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_title(f"Stock Movements: {product_name}")
            
            if history_data:
                dates = []
                net_qty = []
                running_stock = 0
                types = defaultdict(int)
                
                for row in reversed(history_data):
                    if isinstance(row, (list, tuple)):
                        date_str = row[0]
                        qty = row[2]
                        m_type = row[1]
                    else:
                        date_str = row.get("date", "")
                        qty = row.get("quantity", 0)
                        m_type = row.get("movement_type", "")
                    
                    types[m_type] += qty
                    running_stock += qty
                    dates.append(date_str)
                    net_qty.append(running_stock)
                
                ax.plot(dates, net_qty, marker='o', linewidth=2)
                ax.set_ylabel('Running Stock Level')
                ax.set_xlabel('Date')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, alpha=0.3)
                
                legend_text = '\n'.join([f'{k}: {v}' for k, v in types.items()])
                ax.text(0.02, 0.98, legend_text, transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except ImportError:
            ctk.CTkLabel(chart_frame, text="Install matplotlib: pip install matplotlib", font=("Arial", 14)).pack(expand=True)
        except Exception as e:
            ctk.CTkLabel(chart_frame, text=f"Chart error: {str(e)}").pack(expand=True)

    # ==========================================
    # Context Menu Handlers
    # ==========================================

    def show_context_menu(self, event):
        """Show context menu on right-click"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def show_product_history_direct(self):
        """Show product history from context menu"""
        sel = self.tree.selection()
        if sel:
            self.selected_product_id = sel[0]
            self.show_stock_history()

    def show_category_history_direct(self):
        """Show category history from context menu"""
        sel = self.tree.selection()
        if sel:
            cat_path = self.tree.item(sel[0])["values"][2]
            self.open_history_popup("CATEGORY", cat_path, cat_path)

    def open_history_popup(self, mode, target_id, title_name):
        """Open history popup for product or category"""
        is_prod = mode == "PRODUCT"
        history_data = (
            self.app.inventory_service.get_product_history(target_id)
            if is_prod
            else self.app.inventory_service.get_category_history(target_id)
        )

        win = ctk.CTkToplevel(self)
        win.title(f"{'Product' if is_prod else 'Category'} History")
        win.geometry("800x500")
        win.attributes("-topmost", True)

        cols = (
            ("Date", "Type", "Qty", "Reason")
            if is_prod
            else ("Date", "Product", "Type", "Qty", "Reason")
        )
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120 if col != "Reason" else 250)
        tree.pack(fill="both", expand=True, padx=20, pady=20)

        for row in history_data:
            if isinstance(row, dict):
                d = row
            else:
                d = {"date": row[0], "type": row[1], "qty": row[2], "reason": row[3]}
                if not is_prod and len(row) > 4:
                    d["product"] = row[4]
            
            m_type = d.get("type") or d.get("movement_type", "")
            qty = d.get("qty") or d.get("quantity", 0)
            
            if m_type in ["IN", "PURCHASE", "INITIAL"]:
                qty_disp = f"+{qty}"
            elif m_type == "ADJUST":
                qty_disp = f"Set to {qty}"
            else:
                qty_disp = f"-{qty}"

            if is_prod:
                vals = (d.get("date"), m_type, qty_disp, d.get("reason"))
            else:
                vals = (d.get("date"), d.get("product"), m_type, qty_disp, d.get("reason"))
            
            tree.insert("", "end", values=vals)

    def open_print_dialog(self):
        """Open print dialog"""
        PrintDialog(self, self.app)

# inventory_module.py

import customtkinter as ctk
import logging
from tkinter import ttk, messagebox, Menu


class InventoryFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.selected_product_id = None

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

# Low Stock Alerts - Step 4
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

        # Filter toolbar
        filter_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        filter_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Category filter
        ctk.CTkLabel(filter_frame, text="Category:").pack(side="left", padx=(0,5))
        self.category_filter_var = ctk.StringVar(value="All")
        self.category_filter_var.trace_add("write", lambda *args: self.refresh_data())
        self.category_filter_dropdown = ctk.CTkOptionMenu(
            filter_frame, 
            variable=self.category_filter_var, 
            values=["All"]
        )
        self.category_filter_dropdown.pack(side="left", padx=5)

        # Stock filter
        ctk.CTkLabel(filter_frame, text="Stock:").pack(side="left", padx=(10,5))
        self.stock_filter_var = ctk.StringVar(value="All")
        self.stock_filter_var.trace_add("write", lambda *args: self.refresh_data())
        stock_options = ["All", "Low", "Critical"]
        ctk.CTkOptionMenu(
            filter_frame, 
            variable=self.stock_filter_var, 
            values=stock_options
        ).pack(side="left", padx=5)

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
        self.tree = ttk.Treeview(left_panel, columns=cols, show="headings", height=15)
        self.sort_col = None
        self.sort_reverse = False
        
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=80 if col != "Name" else 150)
            
        # Pagination
        self.page_size = 25
        self.current_page = 0
        self.filtered_products = []
        
        tree_frame = ctk.CTkFrame(left_panel)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0,5))
        self.tree.pack(side="left", fill="both", expand=True)
        
        pag_frame = ctk.CTkFrame(tree_frame, fg_color="transparent")
        pag_frame.pack(side="right", fill="y", padx=(5,0))
        
        self.prev_btn = ctk.CTkButton(pag_frame, text="<< Prev", width=60, command=self.prev_page)
        self.prev_btn.pack(pady=2)
        self.page_label = ctk.CTkLabel(pag_frame, text="Page 1")
        self.page_label.pack(pady=2)
        self.next_btn = ctk.CTkButton(pag_frame, text="Next >>", width=60, command=self.next_page)
        self.next_btn.pack(pady=2)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)

        # RIGHT side: Edit/Add Form
        right_panel = ctk.CTkScrollableFrame(pane, width=320)
        right_panel.pack(side="right", fill="y", padx=(10, 0))

        ctk.CTkLabel(
            right_panel, text="Product Details", font=("Arial", 18, "bold")
        ).pack(pady=20)

        self.name_entry = self.create_input(right_panel, "Product Name")
        # --- Category Text Entry Dropdown ---
        ctk.CTkLabel(right_panel, text="Category").pack(anchor="w", padx=25)
        self.category_var = ctk.StringVar(value="Select Category")
        self.cat_dropdown = ctk.CTkOptionMenu(
            right_panel, variable=self.category_var, values=[]
        )
        self.cat_dropdown.pack(fill="x", padx=25, pady=(0, 5))
        # Helper button to add new categories on the fly
        ctk.CTkButton(
            right_panel,
            text="+ Manage Categories",
            height=20,
            fg_color="#34495e",
            command=self.open_category_window,
        ).pack(padx=25, pady=(0, 10))
        self.cost_entry = self.create_input(right_panel, "Unit Cost ($)")
        self.price_entry = self.create_input(right_panel, "Retail Price ($)")
        self.qty_entry = self.create_input(right_panel, "Current Stock")
        self.min_entry = self.create_input(right_panel, "Min Threshold (Alert)")

        # Mapping to store ID vs Path for the database
        self.cat_map = {}
        self.refresh_category_list()

        # Buttons
        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=25)

        ctk.CTkButton(
            btn_frame, text="Add Product", fg_color="#27ae60", command=self.add_product
        ).pack(fill="x", pady=5)
        ctk.CTkButton(
            btn_frame,
            text="Update Selected",
            fg_color="#2980b9",
            command=self.update_product,
        ).pack(fill="x", pady=5)
        ctk.CTkButton(
            btn_frame,
            text="Delete Product",
            fg_color="#e74c3c",
            command=self.delete_product,
        ).pack(fill="x", pady=20)
        ctk.CTkButton(
            btn_frame, text="Clear", fg_color="#7f8c8d", command=self.clear_form
        ).pack(fill="x")

        ctk.CTkButton(
            btn_frame,
            text="View History",
            fg_color="#8e44ad",
            hover_color="#9b59b6",
            command=self.show_stock_history,
        ).pack(fill="x", pady=(5, 20))


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

        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="View Product History", command=self.show_product_history_direct
        )
        self.context_menu.add_command(
            label="View Category History", command=self.show_category_history_direct
        )
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Export button
        export_btn = ctk.CTkButton(
            left_panel,
            text="Export Filtered to CSV",
            fg_color="#27ae60",
            command=self.export_to_csv
        )
        export_btn.pack(fill="x", padx=10, pady=(5,0))

        # Update alert label on refresh
        self.update_alert_label()

        self.refresh_data()
    
    def update_alert_label(self):
        low_count = len([p for p in self.app.inventory_service.get_products() if p["quantity"] <= p["min_threshold"]])
        if low_count > 0:
            self.alert_label.configure(text=f"⚠️ {low_count} LOW STOCK", text_color="orange")
        else:
            self.alert_label.configure(text="✅ All stock healthy", text_color="green")
    
    def show_low_stock_alert(self):
        low_stock = [p for p in self.app.inventory_service.get_products() if p["quantity"] <= p["min_threshold"]]
        if not low_stock:
            messagebox.showinfo("Good News", "No low stock items!")
            return
        
        alert_win = ctk.CTkToplevel(self)
        alert_win.title("Low Stock Alert")
        alert_win.geometry("600x400")
        
        ctk.CTkLabel(alert_win, text=f"{len(low_stock)} items need restock!", font=("Arial", 16, "bold"), text_color="#e74c3c").pack(pady=10)
        
        cols = ("Name", "Category", "Stock", "Min")
        tree = ttk.Treeview(alert_win, columns=cols, show="headings", height=12)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        for p in low_stock[:20]:  # Top 20
            tree.insert("", "end", values=(p["name"], p["category"], p["quantity"], p["min_threshold"]))
        
        ctk.CTkButton(alert_win, text="Restock All", fg_color="#e67e22", command=lambda: self.bulk_restock(low_stock)).pack(pady=10)
    
    def bulk_restock(self, low_stock):
        # Simple bulk restock - double current stock
        for p in low_stock:
            new_qty = p["quantity"] * 2
            self.app.inventory_service.update_product(p["id"], p["name"], p["category_id"], p["price"], p["cost"], new_qty, p["min_threshold"])
        self.refresh_data()
        messagebox.showinfo("Restocked", f"Restocked {len(low_stock)} items!")
    
    import csv
    import os
    from datetime import datetime
    
    def export_to_csv(self):
        if not self.filtered_products:
            messagebox.showwarning("No Data", "No filtered products to export.")
            return
        
        from datetime import datetime
        import os
        
        filename = f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(os.getcwd(), filename)
        
        cols = ["id", "name", "category", "cost", "price", "quantity", "min_threshold"]
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=cols)
            writer.writeheader()
            for p in self.filtered_products:
                writer.writerow({k: p.get(k, '') for k in cols})
        
        messagebox.showinfo("Export Complete", f"Exported {len(self.filtered_products)} items to {filename}")

    def create_input(self, parent, label):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=25)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=25, pady=(0, 10))
        return entry

    def open_category_window(self):
        from category_module import CategoryManagementWindow
        
        CategoryManagementWindow(
            parent=self,
            category_service=self.app.category_service,
            inventory_service=self.app.inventory_service,
            refresh_callback=self.refresh_category_list
        )

    def refresh_data(self):
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
            if stock_filter == "Critical" and qty >= (min_th * 0.5):
                continue

            self.filtered_products.append(p)
        
        # Sort if sort column set
        if self.sort_col:
            self.filtered_products.sort(key=lambda p: self.get_sort_key(p, self.sort_col), reverse=self.sort_reverse)
        
        self.current_page = 0
        self.update_page_label()
        self.populate_tree()
        self.update_pagination_buttons()
    
    def sort_by_column(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
        self.refresh_data()
    
    def get_sort_key(self, p, col):
        val = p.get(col, 0)
        if col in ["Stock", "Min", "id"]:
            try:
                return float(val)
            except:
                return 0
        return str(val).lower()
    
    def populate_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_products = self.filtered_products[start:end]
        
        for p in page_products:
            live_syp = p["price"] * self.current_rate
            tags = self.get_stock_tags(p["quantity"], p["min_threshold"])
            
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
    
    def get_stock_tags(self, qty, min_th):
        if qty <= 0:
            return ("critical",)
        elif qty <= min_th:
            return ("low_stock",)
        elif qty <= min_th * 2:
            return ("warning",)
        return ()
    
    def update_page_label(self):
        total_pages = (len(self.filtered_products) + self.page_size - 1) // self.page_size
        self.page_label.configure(text=f"Page {self.current_page + 1} / {total_pages or 1} ({len(self.filtered_products)} items)")
    
    def update_pagination_buttons(self):
        total_pages = (len(self.filtered_products) + self.page_size - 1) // self.page_size
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.populate_tree()
            self.update_page_label()
            self.update_pagination_buttons()
    
    def next_page(self):
        total_pages = (len(self.filtered_products) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.populate_tree()
            self.update_page_label()
            self.update_pagination_buttons()


    def refresh_category_list(self):
        """Updates the dropdown with the latest category paths."""
        try:
            logging.debug("Refreshing category list...")
            cats = self.app.inventory_service.get_categories()
            logging.debug(f"Received {len(cats)} categories from service")
            
            if not cats:
                logging.warning("No categories found! Check database.")
                self.cat_map = {}
                self.cat_dropdown.configure(values=["No Categories"])
                if hasattr(self, 'category_filter_dropdown'):
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
            self.cat_dropdown.configure(values=paths if paths else ["No Categories"])
            if hasattr(self, 'category_filter_dropdown'):
                self.category_filter_dropdown.configure(values=filter_paths)
            
        except Exception as e:
            logging.error(f"Error in refresh_category_list: {e}", exc_info=True)
            self.cat_dropdown.configure(values=["Error loading categories"])
            if hasattr(self, 'category_filter_dropdown'):
                self.category_filter_dropdown.configure(values=["All"])

    def on_product_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_product_id = sel[0]
        p = self.app.inventory_service.get_product_by_id(self.selected_product_id)
        if p:
            self.clear_form(keep_id=True)
            self.name_entry.insert(0, p["name"])
            # Find the path for this product's category_id and set the dropdown
            full_path = self.app.inventory_service.get_category_path(p["category_id"])
            self.category_var.set(full_path)
            self.cost_entry.insert(0, str(p["cost"]))
            self.price_entry.insert(0, str(p["price"]))
            self.qty_entry.insert(0, str(p["quantity"]))
            self.min_entry.insert(0, str(p["min_threshold"]))

    def clear_form(self, keep_id=False):
        if not keep_id:
            self.selected_product_id = None

        # 1. Clear the text entries
        entries = [
            self.name_entry,
            self.cost_entry,
            self.price_entry,
            self.qty_entry,
            self.min_entry,
        ]
        for e in entries:
            e.delete(0, "end")

        # 2. Reset the category dropdown to default
        self.category_var.set("Select Category")

    def add_product(self):
        try:
            data = self.get_form_data()
            self.app.inventory_service.add_product(*data)
            self.refresh_data()
            self.clear_form()
            messagebox.showinfo("Success", "Product added.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_product(self):
        if not self.selected_product_id:
            messagebox.showwarning(
                "Selection Required", "Please select a product from the list first."
            )
            return
            
        try:
            data = self.get_form_data()
            self.app.inventory_service.update_product(self.selected_product_id, *data)
            self.refresh_data()
            messagebox.showinfo("Success", "Product updated.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_product(self):
        if not self.selected_product_id:
            messagebox.showwarning(
                "Selection Required", "Please select a product from the list first."
            )
            return

        if messagebox.askyesno("Confirm", "Delete this product?"):
            self.app.inventory_service.delete_product(self.selected_product_id)
            self.refresh_data()
            self.clear_form()

    def get_form_data(self):
        selected_path = self.category_var.get()
        cat_id = self.cat_map.get(selected_path, None)

        return (
            self.name_entry.get(),
            cat_id,
            float(self.price_entry.get()),
            float(self.cost_entry.get()),
            int(self.qty_entry.get()),
            int(self.min_entry.get() or 5),
        )

    def show_stock_history(self):
        """Opens a window showing stock history with matplotlib chart."""
        if not self.selected_product_id:
            messagebox.showwarning(
                "Selection Required", "Please select a product from the list first."
            )
            return

        product_name = self.name_entry.get()
        history_data = self.app.inventory_service.get_product_history(self.selected_product_id)

        # Create popup with tabs for table + chart
        history_win = ctk.CTkToplevel(self)
        history_win.title(f"Stock History: {product_name}")
        history_win.geometry("900x600")
        history_win.attributes("-topmost", True)

        # Tabview for Table and Chart
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
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.dates as mdates
            from collections import defaultdict

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_title(f"Stock Movements: {product_name}")

            if history_data:
                dates = []
                net_qty = []
                running_stock = 0
                types = defaultdict(int)

                for row in reversed(history_data):  # Oldest first
                    date_str = row[0] if isinstance(row, (list, tuple)) else row["date"]
                    qty = row[2] if isinstance(row, (list, tuple)) else row["quantity"]
                    m_type = row[1] if isinstance(row, (list, tuple)) else row["movement_type"]
                    
                    types[m_type] += qty
                    running_stock += qty
                    dates.append(date_str)
                    net_qty.append(running_stock)

                ax.plot(dates, net_qty, marker='o', linewidth=2)
                ax.set_ylabel('Running Stock Level')
                ax.set_xlabel('Date')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, alpha=0.3)

                # Legend with totals
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

        # Populate table
        if not history_data:
            tree.insert("", "end", values=("-", "NONE", "-", "No history"))
        else:
            for row in history_data:
                raw_date = row[0] if isinstance(row, (list, tuple)) else row["date"]
                m_type = row[1] if isinstance(row, (list, tuple)) else row["movement_type"]
                qty = row[2] if isinstance(row, (list, tuple)) else row["quantity"]
                reason = row[3] if isinstance(row, (list, tuple)) else row["reason"]

                qty_display = f"+{qty}" if m_type in ["IN", "PURCHASE"] else f"-{qty}"
                if m_type == "ADJUST":
                    qty_display = f"Set to {qty}"

                tree.insert("", "end", values=(raw_date, m_type, qty_display, reason))

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def show_product_history_direct(self):
        sel = self.tree.selection()
        if sel:
            p_name = self.tree.item(sel[0])["values"][1]
            self.open_history_popup("PRODUCT", sel[0], p_name)

    def show_category_history_direct(self):
        sel = self.tree.selection()
        if sel:
            cat_path = self.tree.item(sel[0])["values"][2]
            self.open_history_popup("CATEGORY", cat_path, cat_path)

    def open_history_popup(self, mode, target_id, title_name):
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
            d = row if isinstance(row, dict) else row
            m_type = d[1]
            qty_disp = f"+{d[2]}" if m_type in ["IN", "PURCHASE"] else f"-{d[2]}"
            if m_type == "ADJUST":
                qty_disp = f"Set to {d[2]}"

            vals = (
                (d[0], m_type, qty_disp, d[3])
                if is_prod
                else (d[0], d[4], m_type, qty_disp, d[3])
            )
            tree.insert("", "end", values=vals)

    def apply_bulk_adjustment(self, direction):
        """Processes the bulk update based on which button was clicked."""
        val = self.bulk_pct_entry.get().strip()

        if not val:
            messagebox.showwarning(
                "Input Missing", "Please enter a percentage value first."
            )
            return

        try:
            pct = float(val)
            # Flip to negative if the 'Decrease' button was pressed
            final_pct = pct if direction == "UP" else -pct

            action_text = "increase" if direction == "UP" else "decrease"
            confirm = messagebox.askyesno(
                "Confirm Bulk Action",
                f"This will {action_text} the retail price of ALL products by {pct}%.\n\nAre you sure?",
            )

            if confirm:
                self.app.inventory_service.bulk_update_prices(final_pct)
                self.refresh_data()  # Refresh the table to show new prices
                self.bulk_pct_entry.delete(0, "end")
                messagebox.showinfo("Success", f"All prices {action_text}d by {pct}%.")

        except ValueError:
            messagebox.showerror(
                "Input Error", "Please enter a valid number (e.g. 15)."
            )

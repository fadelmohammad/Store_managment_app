# inventory_module.py

import customtkinter as ctk
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
        self.tree = ttk.Treeview(left_panel, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80 if col != "Name" else 150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
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

        # --- NEW: BULK OPERATIONS SECTION ---
        # Separator Label
        ctk.CTkLabel(
            right_panel,
            text="Bulk Price Adjustments",
            font=("Arial", 14, "bold"),
            text_color="#f1c40f",
        ).pack(pady=(25, 5))

        # Percentage Entry
        self.bulk_pct_entry = ctk.CTkEntry(
            right_panel, placeholder_text="Enter % (e.g. 10)"
        )
        self.bulk_pct_entry.pack(fill="x", padx=25, pady=5)

        # Container for the two side-by-side buttons
        bulk_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        bulk_btn_frame.pack(fill="x", padx=20, pady=5)

        # Increase Button
        ctk.CTkButton(
            bulk_btn_frame,
            text="Increase All",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            width=100,
            command=lambda: self.apply_bulk_adjustment("UP"),
        ).pack(side="left", padx=5, expand=True)

        # Decrease Button
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

        self.refresh_data()

    def create_input(self, parent, label):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=25)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=25, pady=(0, 10))
        return entry

    def open_category_window(self):
        """Popup to add a new sub-category."""
        pop = ctk.CTkToplevel(self)
        pop.title("Add Category")
        pop.geometry("300x250")
        pop.attributes("-topmost", True)

        ctk.CTkLabel(pop, text="Category Name:").pack(pady=5)
        name_ent = ctk.CTkEntry(pop)
        name_ent.pack(pady=5)

        ctk.CTkLabel(pop, text="Parent Category (Optional):").pack(pady=5)
        parent_var = ctk.StringVar(value="None")
        parent_opts = ["None"] + list(self.cat_map.keys())
        ctk.CTkOptionMenu(pop, variable=parent_var, values=parent_opts).pack(pady=5)

        def save():
            p_id = self.cat_map.get(parent_var.get())  # None if "None"
            self.app.inventory_service.add_category(name_ent.get(), p_id)
            self.refresh_category_list()
            pop.destroy()

        ctk.CTkButton(pop, text="Save", command=save).pack(pady=20)

        def delete_selected_cat():
            # Get the ID of the category currently selected in the 'parent' dropdown
            # or add a separate selection for deletion.
            target_path = parent_var.get()
            cat_id = self.cat_map.get(target_path)

            if not cat_id:
                messagebox.showwarning("Error", "Select a valid category to delete.")
                return

            if messagebox.askyesno(
                "Confirm",
                f"Delete '{target_path}'?\nProducts will move to the parent level.",
            ):
                self.app.inventory_service.delete_category(cat_id)
                self.refresh_category_list()
                # Update the popup dropdown values too
                parent_opts = ["None"] + list(self.cat_map.keys())
                # (You'd need to re-configure the popup menu here or just close it)
                pop.destroy()
                self.refresh_data()  # Refresh main inventory table

        ctk.CTkButton(
            pop, text="Delete Selected", fg_color="#e74c3c", command=delete_selected_cat
        ).pack(pady=5)

    def refresh_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        search = self.search_var.get().lower()

        # Pull dynamic rate from app
        current_rate = getattr(self.app, "exchange_rate", 15000)
        products = self.app.inventory_service.get_products()

        for p in products:
            if search in p["name"].lower() or search in p["category"].lower():
                # LIVE CALCULATION for SYP
                live_syp = p["price"] * current_rate

                # Check for low stock
                tags = ("low_stock",) if p["quantity"] <= p["min_threshold"] else ()

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
                        f"{live_syp:,.0f} SYP",  # Formatted with commas
                        p["quantity"],
                        p["min_threshold"],
                    ),
                    tags=tags,
                )

    def refresh_category_list(self):
        """Updates the dropdown with the latest Electrical > Lights > Bulbs paths."""
        cats = self.app.inventory_service.get_categories()
        self.cat_map = {c["path"]: c["id"] for c in cats}
        paths = list(self.cat_map.keys())
        self.cat_dropdown.configure(values=paths if paths else ["No Categories"])

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
        """Opens a window showing the timeline of stock changes for the selected product."""
        if not self.selected_product_id:
            messagebox.showwarning(
                "Selection Required", "Please select a product from the list first."
            )
            return

        product_name = self.name_entry.get()
        history_data = self.app.inventory_service.get_product_history(self.selected_product_id)

        # Create the popup window
        history_win = ctk.CTkToplevel(self)
        history_win.title(f"Stock History: {product_name}")
        history_win.geometry("600x400")
        history_win.attributes("-topmost", True)

        # Header
        ctk.CTkLabel(
            history_win,
            text=f"Movement Timeline: {product_name}",
            font=("Arial", 18, "bold"),
        ).pack(pady=15)

        # Create the Table (Treeview)
        cols = ("Date", "Type", "Qty", "Reason / Reference")
        tree = ttk.Treeview(history_win, columns=cols, show="headings")

        # Configure columns
        tree.heading("Date", text="Date & Time")
        tree.column("Date", width=140, anchor="center")

        tree.heading("Type", text="Type")
        tree.column("Type", width=80, anchor="center")

        tree.heading("Qty", text="Qty")
        tree.column("Qty", width=60, anchor="center")

        tree.heading("Reason / Reference", text="Reason / Reference")
        tree.column("Reason / Reference", width=250, anchor="w")

        tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Populate the table
        if not history_data:
            tree.insert(
                "",
                "end",
                values=("-", "NONE", "-", "No history recorded for this item."),
            )
        else:
            for row in history_data:
                # Format the date nicely if it's a standard SQLite datetime string
                raw_date = row["date"] if isinstance(row, dict) else row[0]
                m_type = row["movement_type"] if isinstance(row, dict) else row[1]
                qty = row["quantity"] if isinstance(row, dict) else row[2]
                reason = row["reason"] if isinstance(row, dict) else row[3]

                # Add a + or - sign to make it easier to read
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

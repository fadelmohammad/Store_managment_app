# File: purchase_module.py

import customtkinter as ctk
from tkinter import ttk, messagebox


class PurchaseFrame(ctk.CTkFrame):
    def __init__(self, parent, app, db, purchase_service, account_service, inventory_service):
        super().__init__(parent)
        self.app = app
        self.db = db
        self.purchase_service = purchase_service
        self.account_service = account_service
        self.inventory_service = inventory_service
        self.cart = []

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

        ctk.CTkButton(
            nav_bar,
            text="Home",
            width=100,
            command=self.app.go_home,
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            nav_bar,
            text=self.__class__.__name__.replace("Frame", "").replace("UI", ""),
            font=("Arial", 16, "bold"),
        ).pack(side="right", padx=20)

        # Left Side: Product Selection & Supplier
        self.left_panel = ctk.CTkFrame(self, width=400)
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.left_panel, text="1. Select Supplier", font=("Arial", 16, "bold")).pack(pady=10)
        self.supplier_var = ctk.StringVar()
        self.supplier_dropdown = ctk.CTkOptionMenu(self.left_panel, variable=self.supplier_var, values=[])
        self.supplier_dropdown.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.left_panel, text="2. Add Products", font=("Arial", 16, "bold")).pack(pady=20)

        # Product Search/Selection
        self.prod_var = ctk.StringVar()
        self.prod_dropdown = ctk.CTkOptionMenu(self.left_panel, variable=self.prod_var, values=[])
        self.prod_dropdown.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.left_panel, text="Unit Cost (€)").pack(pady=(10, 0))
        self.cost_entry = ctk.CTkEntry(self.left_panel)
        self.cost_entry.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.left_panel, text="Quantity").pack(pady=(10, 0))
        self.qty_entry = ctk.CTkEntry(self.left_panel)
        self.qty_entry.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(self.left_panel, text="Add to Cart", command=self.add_to_cart, fg_color="green").pack(pady=20)

        # Right Side: Purchase Cart
        self.right_panel = ctk.CTkFrame(self)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.right_panel, text="Purchase Cart", font=("Arial", 18, "bold")).pack(pady=10)

        self.cart_tree = ttk.Treeview(
            self.right_panel,
            columns=("ID", "Name", "Cost (USD)", "Qty", "Total (USD)", "Total (SYP)"),
            show="headings",
        )
        for col in ("ID", "Name", "Cost (USD)", "Qty", "Total (USD)", "Total (SYP)"):
            self.cart_tree.heading(col, text=col)
        self.cart_tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.total_label = ctk.CTkLabel(self.right_panel, text="Total: €0.00", font=("Arial", 20, "bold"))
        self.total_label.pack(pady=10)

        ctk.CTkButton(self.right_panel, text="Complete Purchase", command=self.process_purchase, height=50).pack(pady=10)

        self.refresh_data()

    def refresh_data(self):
        """Refresh suppliers and products lists (via services)."""
        suppliers = self.account_service.get_by_role("Supplier") or []
        self.supplier_map = {s["name"]: s["id"] for s in suppliers if s.get("name") is not None}

        if self.supplier_map:
            self.supplier_dropdown.configure(values=list(self.supplier_map.keys()))
        else:
            self.supplier_dropdown.configure(values=["No Suppliers Found"])

        products = self.inventory_service.get_products() or []
        self.product_map = {}
        for p in products:
            name = p.get("name")
            if not name:
                continue
            self.product_map[name] = {
                "id": p.get("id"),
                "name": name,
                "cost": p.get("cost", 0),
                "price": p.get("price", 0),
            }

        self.prod_dropdown.configure(values=list(self.product_map.keys()))

    def add_to_cart(self):
        p_name = self.prod_var.get()
        if not p_name or p_name not in self.product_map:
            messagebox.showwarning("Select", "Please select a product first.")
            return

        rate = float(self.app.exchange_rate)

        try:
            cost = float(self.cost_entry.get())
            qty = float(self.qty_entry.get())
            if qty <= 0:
                raise ValueError("Quantity must be > 0")
            if cost < 0:
                raise ValueError("Cost must be >= 0")

            product = self.product_map[p_name]
            item_total_usd = cost * qty
            item_total_syp = item_total_usd * rate

            self.cart.append(
                {
                    "id": product["id"],
                    "name": p_name,
                    "price": cost,  # PurchaseService expects item["price"]
                    "qty": qty,     # PurchaseService expects item["qty"]
                }
            )

            self.cart_tree.insert(
                "",
                "end",
                values=(
                    product["id"],
                    p_name,
                    f"${cost:.2f}",
                    qty,
                    f"${item_total_usd:.2f}",
                    f"{item_total_syp:,.0f} SYP",
                ),
            )
            self.update_total()
        except Exception:
            messagebox.showerror("Error", "Check cost and quantity inputs")

    def update_total(self):
        total = sum(item["price"] * item["qty"] for item in self.cart)
        self.total_label.configure(text=f"Total: €{total:.2f}")

    def process_purchase(self):
        s_name = self.supplier_var.get()
        if not s_name or not self.cart:
            messagebox.showwarning("Warning", "Select a supplier and add items")
            return

        try:
            supplier_id = self.supplier_map[s_name]
            self.purchase_service.process_purchase(self.cart, supplier_id, self.app.exchange_rate)

            messagebox.showinfo("Success", "Purchase recorded and stock updated!")
            self.cart = []
            for i in self.cart_tree.get_children():
                self.cart_tree.delete(i)
            self.update_total()
        except Exception as e:
            messagebox.showerror("Error", str(e))

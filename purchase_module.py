# File: purchase_module.py

import customtkinter as ctk
from tkinter import ttk, messagebox


class PurchaseFrame(ctk.CTkFrame):
    def __init__(self, parent, app, db, purchase_service):
        super().__init__(parent)
        self.app = app
        self.db = db
        self.purchase_service = purchase_service
        self.cart = []

        nav_bar = ctk.CTkFrame(self, fg_color="transparent")
        nav_bar.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkButton(
            nav_bar,
            text="Back",
            width=100,
            fg_color="#444444",
            hover_color="#555555",
            command=self.app.go_back
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            nav_bar,
            text="Home",
            width=100,
            command=self.app.go_home
        ).pack(side="left", padx=5)

        # Optional: Add a title label in the middle of the nav bar
        ctk.CTkLabel(
            nav_bar,
            text=self.__class__.__name__.replace("Frame", "").replace("UI", ""),
            font=("Arial", 16, "bold")
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

        self.cart_tree = ttk.Treeview(self.right_panel, 
            columns=("ID", "Name", "Cost (USD)", "Qty", "Total (USD)", "Total (SYP)"), show="headings")
        for col in ("ID", "Name", "Cost (USD)", "Qty", "Total (USD)", "Total (SYP)"):
            self.cart_tree.heading(col, text=col)
        self.cart_tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.total_label = ctk.CTkLabel(self.right_panel, text="Total: €0.00", font=("Arial", 20, "bold"))
        self.total_label.pack(pady=10)

        ctk.CTkButton(self.right_panel, text="Complete Purchase", command=self.process_purchase, height=50).pack(
            pady=10)

        self.refresh_data()


    def refresh_data(self):
        """Refresh suppliers and products lists"""
        try:
            print("Refreshing purchase data...")
            
            print("  - Fetching suppliers...")
            suppliers = self.app.account_repo.get_by_role("Supplier")
            print(f"  - Found {len(suppliers) if suppliers else 0} suppliers")
            
            self.supplier_map = {}
            if suppliers:
                for s in suppliers:
                    if hasattr(s, 'keys'):
                        supplier_name = s["name"] if "name" in s.keys() else s[1]
                        supplier_id = s["id"] if "id" in s.keys() else s[0]
                        self.supplier_map[supplier_name] = supplier_id
                        print(f"    - Supplier: {supplier_name} (ID: {supplier_id})")
                    else:
                        self.supplier_map[s[1]] = s[0]  
                        print(f"    - Supplier: {s[1]} (ID: {s[0]})")
            
            if self.supplier_map:
                self.supplier_dropdown.configure(values=list(self.supplier_map.keys()))
            else:
                self.supplier_dropdown.configure(values=["No Suppliers Found"])
            
            print("  - Fetching products...")
            products = self.app.product_repo.get_all()
            print(f"  - Found {len(products) if products else 0} products")
            
            self.product_map = {}
            if products:
                for p in products:
                    if hasattr(p, 'keys'):
                        product_id = p["id"] if "id" in p.keys() else p[0]
                        product_name = p["name"] if "name" in p.keys() else p[1]
                        product_cost = p["cost"] if "cost" in p.keys() else (p[4] if len(p) > 4 else 0)
                        product_price = p["price"] if "price" in p.keys() else (p[3] if len(p) > 3 else 0)
                        
                        self.product_map[product_name] = {
                            "id": product_id,
                            "name": product_name,
                            "cost": product_cost,
                            "price": product_price
                        }
                        print(f"    - Product: {product_name} (ID: {product_id})")
                    else:
                        self.product_map[p[1]] = {
                            "id": p[0],
                            "name": p[1],
                            "cost": p[4] if len(p) > 4 else 0,
                            "price": p[3] if len(p) > 3 else 0
                        }
                        print(f"    - Product: {p[1]} (ID: {p[0]})")
            
            self.prod_dropdown.configure(values=list(self.product_map.keys()))
            print(f"Refresh complete. Products: {len(self.product_map)}, Suppliers: {len(self.supplier_map)}")
            
        except Exception as e:
            print(f"Error in refresh_data: {e}")
            import traceback
            traceback.print_exc()


    def add_to_cart(self):
        p_name = self.prod_var.get()
        rate = self.app.exchange_rate
        try:
            cost = float(self.cost_entry.get())
            qty = float(self.qty_entry.get())
            product = self.product_map[p_name]

            item_total_usd = cost * qty
            item_total_syp = item_total_usd * rate # SYP Calculation

            self.cart.append({
                "id": product["id"],
                "name": p_name,
                "price": cost,
                "qty": qty
            })

            self.cart_tree.insert("", "end", values=(
                product["id"], p_name, f"${cost:.2f}", qty, 
                f"${item_total_usd:.2f}", f"{item_total_syp:,.0f} SYP"
            ))
            self.update_total()
        except Exception as e:
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
            for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
            self.update_total()
        except Exception as e:
            messagebox.showerror("Error", str(e))
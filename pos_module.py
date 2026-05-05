# pos_module.py

import customtkinter as ctk
from tkinter import ttk
from tkinter import messagebox

def format_compact_path(path):
    if not path or path == "Uncategorized":
        return "General"
    
    parts = path.split(" > ")
    if len(parts) <= 2:
        return path
    
    # Format: First (3 letters).. > Last Category
    # Result example: "Ele.. > 9 Watts LED"
    return f"{parts[0][:3]}.. > {parts[-1]}"

class POSFrame(ctk.CTkFrame):
    def __init__(self, parent, app,  sales_service, account_service, inventory_service):
        super().__init__(parent)
        self.app = app
        self.cart = []
        self.sales_service = sales_service
        self.account_service = account_service
        self.inventory_service = inventory_service
        self.customer_map = {}
        self.selected_customer_id = None

        # --- NAVIGATION BAR ---
        nav_bar = ctk.CTkFrame(self, fg_color="transparent")
        nav_bar.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkButton(nav_bar, text="Back", width=100, fg_color="#444444", 
                  command=self.safe_exit).pack(side="left", padx=5)
        ctk.CTkButton(nav_bar, text="Home", width=100, command=self.app.go_home).pack(side="left", padx=5)

        ctk.CTkLabel(nav_bar, text="Point of Sale (POS)", font=("Arial", 16, "bold")).pack(side="right", padx=20)
        ctk.CTkLabel(self, text="Sales Terminal", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

        pane = ctk.CTkFrame(self)
        pane.pack(fill="both", expand=True, padx=15, pady=10)

        # ==========================================
        # LEFT - Product Selection
        # ==========================================
        left = ctk.CTkFrame(pane)
        left.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(left, text="Search & Add Product", font=("Arial", 14, "bold")).pack(pady=10)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(left, textvariable=self.search_var, width=250, placeholder_text="Click to see products...")
        self.search_entry.pack(pady=(5, 0), padx=10)
        
        self.search_entry.bind("<KeyRelease>", lambda _: self.filter_search())
        self.search_entry.bind("<FocusIn>", lambda _: self.show_results())
        self.search_entry.bind("<FocusOut>", lambda _: self.hide_results_delayed())

        self.results_list = ctk.CTkScrollableFrame(left, width=230, height=300)
        # Pack/Unpack handled by visibility logic

        ctk.CTkButton(left, text="Clear Search", width=100, command=self.clear_search).pack(pady=5)

        # ==========================================
        # MIDDLE - Active Cart
        # ==========================================
        middle = ctk.CTkFrame(pane)
        middle.pack(side="left", fill="both", expand=True, padx=10)

        ctk.CTkLabel(middle, text="Current Cart").pack(pady=5)
        cols_cart = ("Name", "Qty", "Price", "Subtotal (USD)", "Subtotal (SYP)")
        self.cart_tree = ttk.Treeview(middle, columns=cols_cart, show="headings", height=18)
        for c in cols_cart:
            self.cart_tree.heading(c, text=c)
            self.cart_tree.column(c, width=110)
        self.cart_tree.pack(fill="both", expand=True)

        cart_btn_frame = ctk.CTkFrame(middle)
        cart_btn_frame.pack(pady=8)
        
        ctk.CTkButton(cart_btn_frame, text="Remove", fg_color="#e74c3c", hover_color="#c0392b",
                      command=self.remove_from_cart).pack(side="left", padx=5)
        
        ctk.CTkLabel(cart_btn_frame, text="Qty:").pack(side="left", padx=5)
        self.cart_qty_entry = ctk.CTkEntry(cart_btn_frame, width=60)
        self.cart_qty_entry.insert(0, "1")
        self.cart_qty_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(cart_btn_frame, text="Update", width=80, 
                      command=self.update_cart_qty).pack(side="left", padx=5)

        # ==========================================
        # RIGHT - Summary & Customer Search
        # ==========================================
        right = ctk.CTkFrame(pane, width=280)
        right.pack(side="right", fill="y")

        self.subtotal_lbl = ctk.CTkLabel(right, text="Subtotal: $0.00", font=ctk.CTkFont(size=20, weight="bold"),
                                         text_color="#f39c12")
        self.subtotal_lbl.pack(pady=15)

        # Customer Search
        ctk.CTkLabel(right, text="Select Customer", font=("Arial", 12, "bold")).pack(anchor="w", padx=15)
        self.cust_search_var = ctk.StringVar()
        self.cust_search_entry = ctk.CTkEntry(right, textvariable=self.cust_search_var, placeholder_text="Search...")
        self.cust_search_entry.pack(padx=15, pady=5, fill="x")
        
        self.cust_results_list = ctk.CTkScrollableFrame(right, height=120)
        
        self.cust_search_entry.bind("<KeyRelease>", lambda _: self.filter_customers())
        self.cust_search_entry.bind("<FocusIn>", lambda _: self.show_cust_results())
        self.cust_search_entry.bind("<FocusOut>", lambda _: self.hide_cust_results_delayed())

        # Checkout Fields
        self.discount_entry = self.add_labeled_entry(right, "Discount %", "0")
        self.tax_entry = self.add_labeled_entry(right, "Tax % (VAT)", "0")

        ctk.CTkLabel(right, text="Payment Method").pack(anchor="w", padx=15, pady=(15, 5))
        self.pay_method = ctk.StringVar(value="Cash")
        ctk.CTkOptionMenu(right, values=["Cash", "Credit"], variable=self.pay_method).pack(padx=15, fill="x")

        # Mixed Transaction Info Label
        ctk.CTkLabel(right, text="Mode: Mixed (Sale/Return)", font=("Arial", 11, "italic")).pack(pady=5)

        ctk.CTkButton(right, text="COMPLETE TRANSACTION", height=60, fg_color="#27ae60", hover_color="#2ecc71",
                      font=ctk.CTkFont(size=16, weight="bold"), command=self.complete_transaction).pack(pady=30, padx=15, fill="x")

        self.load_customers()

    # ==========================================
    # HELPERS & VISIBILITY
    # ==========================================
    def add_labeled_entry(self, parent, label, default):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=15, pady=(10, 0))
        entry = ctk.CTkEntry(parent, width=180)
        entry.insert(0, default)
        entry.pack(pady=5, padx=15, fill="x")
        return entry

    def show_results(self):
        self.filter_search()
        self.results_list.pack(pady=5, padx=10, fill="both", expand=True)

    def hide_results_delayed(self):
        self.after(200, lambda: self.results_list.pack_forget())

    def show_cust_results(self):
        self.filter_customers()
        self.cust_results_list.pack(padx=15, pady=0, fill="x")

    def hide_cust_results_delayed(self):
        self.after(200, lambda: self.cust_results_list.pack_forget())

    # ==========================================
    # SEARCH LOGIC (PRODUCTS & CUSTOMERS)
    # ==========================================
    def filter_search(self):
        term = self.search_var.get().lower().strip()
        for widget in self.results_list.winfo_children():
            widget.destroy()

        matches = self.inventory_service.search_products(term) if term else []

        for p in matches:
            # UI Feedback: Change color if stock is low
            quantity = p.get("quantity", 0) or 0
            min_threshold = p.get("min_threshold", 0) or 0

            if quantity <= min_threshold:
                color = "#e67e22"
                if quantity == 0:
                    color = "#FF0000"
            else:
                color = ("black", "white")

            formatted_cat = format_compact_path(p.get("path"))
            sub_text = f"{formatted_cat}\nStock: {quantity}"

            btn = ctk.CTkButton(
                self.results_list,
                text=f"{p.get('name','')}\n{sub_text}",
                height=60,
                font=("Arial", 13),
                fg_color="transparent",
                text_color=color,
                anchor="center",
                hover_color=("#DBDBDB", "#2B2B2B"),
                command=lambda prod=p: self.open_quantity_popup(prod),
            )
            btn.pack(fill="x", pady=2, padx=5)

    def filter_customers(self):
        term = self.cust_search_var.get().lower().strip()
        for widget in self.cust_results_list.winfo_children():
            widget.destroy()

        matches = [n for n in self.customer_map.keys() if term in n.lower()] if term else list(self.customer_map.keys())

        for name in matches:
            btn = ctk.CTkButton(
                self.cust_results_list, text=name,
                fg_color="transparent", text_color=("black", "white"), anchor="w",
                hover_color=("#DBDBDB", "#2B2B2B"),
                command=lambda n=name: self.select_customer(n)
            )
            btn.pack(fill="x", pady=1)

    def select_customer(self, name):
        self.cust_search_var.set(name)
        self.selected_customer_id = self.customer_map.get(name)
        self.cust_results_list.pack_forget()

    def load_customers(self):
        all_customers = self.account_service.get_by_role("Customer") or []
        self.customer_map = {c["name"]: c["id"] for c in all_customers if c.get("name") is not None}

        default_name = "Cash Customer"
        for name in self.customer_map.keys():
            if "cash" in name.lower():
                default_name = name
                break

        self.cust_search_var.set(default_name)
        self.selected_customer_id = self.customer_map.get(default_name)

    def clear_search(self):
        self.search_var.set("")
        self.filter_search()

    # ==========================================
    # CART & QUANTITY
    # ==========================================
    def open_quantity_popup(self, product):
        self.results_list.pack_forget()
        pop = ctk.CTkToplevel(self)
        pop.title("Transaction Detail")
        pop.geometry("300x450")
        pop.attributes("-topmost", True)
        pop.grab_set()

        ctk.CTkLabel(pop, text=f"Product: {product['name']}\nAvailable: {product['quantity']}", 
                     font=("Arial", 14)).pack(pady=10)
        
        mode_var = ctk.StringVar(value="Sale")
        mode_btn = ctk.CTkSegmentedButton(pop, values=["Sale", "Return"], variable=mode_var)
        mode_btn.pack(pady=10, padx=20, fill="x")

        price_entry = self.add_labeled_entry(pop, "Price Override ($):", f"{product['price']:.2f}")
        qty_entry = self.add_labeled_entry(pop, "Quantity:", "1")

        def add_and_close():
            try:
                p = float(price_entry.get())
                q = int(qty_entry.get())
                mode = mode_var.get()
                
                # STOCK VALIDATION
                if mode == "Sale" and q > product['quantity']:
                    messagebox.showerror("Stock Error", "Not enough stock available!")
                    return
                
                final_qty = q if mode == "Sale" else -q
                self.add_to_cart_custom(product["id"], product["name"], p, final_qty)
                pop.destroy()
            except ValueError:
                messagebox.showerror("Error", "Check your numbers.")

        ctk.CTkButton(pop, text="Add to Cart", command=add_and_close, fg_color="#27ae60").pack(pady=20)

    def add_to_cart_custom(self, pid, name, price, qty):
        for item in self.cart:
            if item["id"] == pid and item["price"] == price:
                item["qty"] += qty
                if item["qty"] == 0: self.cart.remove(item)
                self.refresh_cart()
                return
        self.cart.append({"id": pid, "name": name, "price": price, "qty": qty})
        self.refresh_cart()

    def refresh_cart(self):
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        rate = getattr(self.app, 'exchange_rate', 1.0)
        subtotal_usd = 0.0
        for idx, item in enumerate(self.cart):
            sub_usd = item["price"] * item["qty"]
            subtotal_usd += sub_usd
            display_name = item["name"] if item["qty"] > 0 else f"[RETURN] {item['name']}"
            self.cart_tree.insert("", "end", iid=str(idx),
                values=(display_name, item["qty"], f"${item['price']:.2f}", 
                        f"${sub_usd:.2f}", f"{sub_usd * rate:,.0f} SYP"))
        self.subtotal_lbl.configure(text=f"Total: ${subtotal_usd:.2f}\n({subtotal_usd * rate:,.0f} SYP)")

    def remove_from_cart(self):
        sel = self.cart_tree.selection()
        if sel:
            del self.cart[int(sel[0])]
            self.refresh_cart()

    def update_cart_qty(self):
        sel = self.cart_tree.selection()
        if not sel: return
        try:
            new_qty = int(self.cart_qty_entry.get())
            if new_qty != 0:
                self.cart[int(sel[0])]["qty"] = new_qty
                self.refresh_cart()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid quantity.")

    # ==========================================
    # FINALIZATION
    # ==========================================
    def complete_transaction(self):
        if not self.cart:
            messagebox.showwarning("Empty", "Cart is empty.")
            return
            
        if not self.selected_customer_id:
            messagebox.showerror("Error", "Please select a customer.")
            return

        # --- DYNAMIC TYPE RESOLVER ---
        has_positive = any(item['qty'] > 0 for item in self.cart)
        has_negative = any(item['qty'] < 0 for item in self.cart)

        if has_positive and has_negative:
            final_type = "MIXED_SALE"
        elif has_negative:
            final_type = "RETURN"
        else:
            final_type = "SALE"

        try:
            # Convert percentage strings to floats
            discount = float(self.discount_entry.get() or 0) / 100
            tax = float(self.tax_entry.get() or 0) / 100
            
            # Send the resolved 'final_type' to your sales_service
            inv_id, total = self.sales_service.process_sale(
                self.cart, 
                final_type,             # <--- Dynamic Type
                self.selected_customer_id, 
                discount, 
                tax, 
                self.pay_method.get(), 
                getattr(self.app, 'exchange_rate', 1.0)
            )

            messagebox.showinfo("Success", f"Invoice #{inv_id} [{final_type}] created.\nTotal: ${total:.2f}")
            
            # Reset UI
            self.cart.clear()
            self.refresh_cart()
            self.load_customers() 
            
        except Exception as e:
            messagebox.showerror("Error", f"Database Error: {str(e)}")

    def safe_exit(self):
        if self.cart:
            if not messagebox.askyesno("Exit POS", "Cart is not empty. Discard items and leave?"):
                return
        self.app.go_back()

# File: ui/purchase_module.py

import customtkinter as ctk
from tkinter import ttk, messagebox
from ui.print_dialog import PrintDialog  # Import the print dialog

_GREEN  = ("#27ae60", "#2ecc71")
_RED    = ("#c0392b", "#e74c3c")
_ORANGE = ("#e67e22", "#f39c12")
_DARK   = ("#2c2c2c", "#1a1a1a")
_MUTED  = ("gray55", "gray45")


class PurchaseFrame(ctk.CTkFrame):
    def __init__(self, parent, app, db, purchase_service, account_service, inventory_service):
        super().__init__(parent)
        self.app = app
        self.purchase_service   = purchase_service
        self.account_service    = account_service
        self.inventory_service  = inventory_service
        self.cart = []
        self.supplier_map = {}
        self.selected_supplier_id = None

        self._build_nav()
        self._build_body()
        self.refresh_data()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_nav(self):
        nav = self.app.ui_service.create_back_home_nav(
            self,
            back_command=self.app.go_back,
            home_command=self.app.go_home,
        )
        
        # Add Print button
        ctk.CTkButton(
            nav,
            text="Print",
            width=100,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.open_print_dialog
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(nav, text="Purchase", font=ctk.CTkFont(size=15, weight="bold")).pack(side="right", padx=20)

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=0)
        body.rowconfigure(0, weight=1)

        self._build_product_panel(body)
        self._build_cart_panel(body)
        self._build_summary_panel(body)

    # ── left: product search + supplier ──────────────────────────────────────

    def _build_product_panel(self, parent):
        panel = ctk.CTkFrame(parent, width=260)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_propagate(False)

        # Product search
        ctk.CTkLabel(panel, text="Products", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(0, 4), padx=12, anchor="w")
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(panel, textvariable=self.search_var, placeholder_text="🔍  Search products…", height=34)
        self.search_entry.pack(fill="x", padx=10, pady=(0, 4))
        self.search_entry.bind("<KeyRelease>", lambda _: self._filter_products())
        self.search_entry.bind("<FocusIn>",    lambda _: self._show_product_results())
        self.search_entry.bind("<FocusOut>",   lambda _: self.after(200, self._hide_product_results))

        self.product_results = ctk.CTkScrollableFrame(panel, height=0)

        ctk.CTkButton(
            panel, text="Clear", height=28, width=80,
            fg_color="transparent", border_width=1,
            command=self._clear_search,
        ).pack(pady=(2, 8))

    def _show_product_results(self):
        self._filter_products()
        self.product_results.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _hide_product_results(self):
        self.product_results.pack_forget()

    def _filter_products(self):
        term = self.search_var.get().strip()
        for w in self.product_results.winfo_children():
            w.destroy()

        results = self.inventory_service.search_products(term) if term else (self.inventory_service.get_products() or [])

        for p in results[:30]:
            qty = p.get("quantity", 0) or 0
            thresh = p.get("min_threshold", 0) or 0
            if qty == 0:
                stock_color = "#e74c3c"
            elif qty <= thresh:
                stock_color = "#e67e22"
            else:
                stock_color = ("#2ecc71", "#27ae60")

            row = ctk.CTkFrame(self.product_results, fg_color=("gray88", "gray22"), corner_radius=6)
            row.pack(fill="x", pady=3, padx=2)

            ctk.CTkLabel(row, text=p.get("name", ""), font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", padx=8, pady=(6, 0))

            info_row = ctk.CTkFrame(row, fg_color="transparent")
            info_row.pack(fill="x", padx=8, pady=(0, 6))

            ctk.CTkLabel(info_row, text=f"Cost: ${p.get('cost', 0):.2f}", font=ctk.CTkFont(size=10), text_color=_MUTED, anchor="w").pack(side="left")
            ctk.CTkLabel(info_row, text=f"Stock: {qty}", font=ctk.CTkFont(size=10, weight="bold"), text_color=stock_color, anchor="e").pack(side="right")

            row.bind("<Button-1>", lambda _, prod=p: self._open_add_popup(prod))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda _, prod=p: self._open_add_popup(prod))
            for child in info_row.winfo_children():
                child.bind("<Button-1>", lambda _, prod=p: self._open_add_popup(prod))

    def _clear_search(self):
        self.search_var.set("")
        self._filter_products()

    # ── middle: cart ──────────────────────────────────────────────────────────

    def _build_cart_panel(self, parent):
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=4)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        ctk.CTkLabel(hdr, text="Cart", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(
            hdr, text="🗑  Clear All", height=28, width=100,
            fg_color=_RED[0], hover_color=_RED[1],
            command=self._clear_cart,
        ).pack(side="right")

        tree_frame = ctk.CTkFrame(panel, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "PUR.Treeview",
            background="#1e1e1e", foreground="white",
            fieldbackground="#1e1e1e", rowheight=32,
            font=("Roboto", 11),
        )
        style.configure("PUR.Treeview.Heading", background="#2c2c2c", foreground="#aaaaaa", font=("Roboto", 10, "bold"))
        style.map("PUR.Treeview", background=[("selected", "#2d6a4f")])

        cols = ("Item", "Qty", "Unit Cost $", "Unit Cost SYP", "Subtotal SYP")
        self.cart_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="PUR.Treeview")
        widths = {"Item": 220, "Qty": 60, "Unit Cost $": 100, "Unit Cost SYP": 120, "Subtotal SYP": 130}
        for c in cols:
            self.cart_tree.heading(c, text=c)
            self.cart_tree.column(c, width=widths[c], anchor="center" if c != "Item" else "w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=vsb.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.cart_tree.bind("<<TreeviewSelect>>", self._on_cart_select)

        action = ctk.CTkFrame(panel, fg_color="transparent")
        action.grid(row=2, column=0, sticky="ew", padx=10, pady=8)

        ctk.CTkButton(
            action, text="Remove Selected", height=32,
            fg_color=_RED[0], hover_color=_RED[1],
            command=self._remove_selected,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(action, text="Unit Cost ($):").pack(side="left", padx=(10, 4))
        self.cost_entry = ctk.CTkEntry(action, width=95, height=32)
        self.cost_entry.insert(0, "0.00")
        self.cost_entry.pack(side="left", padx=4)

        ctk.CTkLabel(action, text="Qty:").pack(side="left", padx=(10, 4))
        self.qty_entry = ctk.CTkEntry(action, width=60, height=32)
        self.qty_entry.insert(0, "1")
        self.qty_entry.pack(side="left", padx=4)

        ctk.CTkButton(
            action, text="Update Selected", height=32, width=160,
            command=self._update_selected_cart_item,
        ).pack(side="left", padx=8)

    def _clear_cart(self):
        if self.cart and messagebox.askyesno("Clear Cart", "Remove all items from cart?"):
            self.cart.clear()
            self._refresh_cart()

    def _remove_selected(self):
        sel = self.cart_tree.selection()
        if sel:
            del self.cart[int(sel[0])]
            self._refresh_cart()

    def _on_cart_select(self, _event=None):
        sel = self.cart_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except (TypeError, ValueError):
            return
        if idx < 0 or idx >= len(self.cart):
            return
        item = self.cart[idx]
        self.cost_entry.delete(0, "end")
        self.cost_entry.insert(0, f"{float(item['price']):.2f}")
        self.qty_entry.delete(0, "end")
        self.qty_entry.insert(0, str(int(item["qty"])))

    def _update_selected_cart_item(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except (TypeError, ValueError):
            return
        if idx < 0 or idx >= len(self.cart):
            return
        try:
            cost = float(self.cost_entry.get())
            qty  = int(self.qty_entry.get())
            if cost < 0 or qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter valid Unit Cost ($) and Qty (qty > 0).")
            return
        self.cart[idx]["price"] = cost
        self.cart[idx]["qty"]   = qty
        self._refresh_cart()

    def _refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)

        rate = float(getattr(self.app, "exchange_rate", 1.0))
        subtotal_usd = 0.0

        for idx, item in enumerate(self.cart):
            sub = item["price"] * item["qty"]
            subtotal_usd += sub
            self.cart_tree.insert(
                "", "end", iid=str(idx),
                values=(
                    item["name"],
                    item["qty"],
                    f"${item['price']:.2f}",
                    f"{item['price'] * rate:,.0f}",
                    f"{sub * rate:,.0f}",
                ),
            )

        self._update_totals(subtotal_usd, rate)

    # ── right: summary ────────────────────────────────────────────────────────

    def _build_summary_panel(self, parent):
        panel = ctk.CTkFrame(parent, width=280)
        panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        panel.grid_propagate(False)

        totals_card = ctk.CTkFrame(panel, fg_color=_DARK[0], corner_radius=10)
        totals_card.pack(fill="x", padx=10, pady=(12, 8))

        ctk.CTkLabel(totals_card, text="Total (SYP)", font=ctk.CTkFont(size=11), text_color=_MUTED[0]).pack(pady=(10, 0))
        self.total_syp_lbl = ctk.CTkLabel(
            totals_card, text="0 SYP",
            font=ctk.CTkFont(size=28, weight="bold"), text_color=_ORANGE[1],
        )
        self.total_syp_lbl.pack()

        ctk.CTkLabel(totals_card, text="Total (USD)", font=ctk.CTkFont(size=11), text_color=_MUTED[0]).pack(pady=(4, 0))
        self.total_usd_lbl = ctk.CTkLabel(
            totals_card, text="$0.00",
            font=ctk.CTkFont(size=14), text_color=_ORANGE[0],
        )
        self.total_usd_lbl.pack(pady=(0, 10))

        self.item_count_lbl = ctk.CTkLabel(panel, text="0 items", font=ctk.CTkFont(size=11), text_color=_MUTED[0])
        self.item_count_lbl.pack()

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=8)

        # Supplier search
        ctk.CTkLabel(panel, text="Supplier", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12)
        self.supplier_var = ctk.StringVar()
        self.supplier_entry = ctk.CTkEntry(panel, textvariable=self.supplier_var, placeholder_text="Search supplier…", height=32)
        self.supplier_entry.pack(fill="x", padx=10, pady=(4, 0))
        self.supplier_entry.bind("<KeyRelease>", lambda _: self._filter_suppliers())
        self.supplier_entry.bind("<FocusIn>",    lambda _: self._show_supplier_results())
        self.supplier_entry.bind("<FocusOut>",   lambda _: self.after(200, self._hide_supplier_results))
        self.supplier_results = ctk.CTkScrollableFrame(panel, height=100)

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=8)

        self.discount_entry = self._labeled_entry(panel, "Discount %", "0")

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(panel, text="Payment Method", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(8, 2))
        self.pay_method = ctk.StringVar(value="Cash")
        ctk.CTkSegmentedButton(panel, values=["Cash", "Credit"], variable=self.pay_method).pack(fill="x", padx=10)

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=8)

        ctk.CTkButton(
            panel, text="✔  COMPLETE PURCHASE",
            height=52, corner_radius=8,
            fg_color=_GREEN[0], hover_color=_GREEN[1],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._process_purchase,
        ).pack(fill="x", padx=10, pady=(0, 12))

    def _update_totals(self, subtotal_usd, rate):
        try:
            discount = float(getattr(self, "discount_entry", None) and self.discount_entry.get() or 0) / 100
        except ValueError:
            discount = 0.0
        final_usd = subtotal_usd * (1 - discount)
        self.total_usd_lbl.configure(text=f"${final_usd:.2f}")
        self.total_syp_lbl.configure(text=f"{final_usd * rate:,.0f} SYP")
        self.item_count_lbl.configure(text=f"{len(self.cart)} item{'s' if len(self.cart) != 1 else ''}")

    # ── add-to-cart popup ─────────────────────────────────────────────────────

    def _open_add_popup(self, product):
        self._hide_product_results()
        pop = ctk.CTkToplevel(self)
        pop.title("Add to Cart")
        pop.geometry("300x280")
        pop.resizable(False, False)
        pop.attributes("-topmost", True)
        pop.grab_set()

        ctk.CTkLabel(pop, text=product.get("name", ""), font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(16, 2))
        ctk.CTkLabel(pop, text=f"Current stock: {product.get('quantity', 0)}", font=ctk.CTkFont(size=11), text_color=_MUTED[0]).pack()

        ctk.CTkFrame(pop, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=16, pady=10)

        cost_entry = self._labeled_entry(pop, "Unit Cost ($)", f"{product.get('cost', 0):.2f}")
        qty_entry  = self._labeled_entry(pop, "Quantity", "1")
        qty_entry.focus()

        def _confirm():
            try:
                cost = float(cost_entry.get())
                qty  = int(qty_entry.get())
                if cost < 0 or qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Enter a valid cost (≥0) and quantity (>0).", parent=pop)
                return
            self._add_to_cart(product.get("id"), product.get("name", ""), cost, qty)
            pop.destroy()

        pop.bind("<Return>", lambda _: _confirm())
        ctk.CTkButton(
            pop, text="Add to Cart", height=40,
            fg_color=_GREEN[0], hover_color=_GREEN[1],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=_confirm,
        ).pack(fill="x", padx=20, pady=16)

    def _labeled_entry(self, parent, label, default):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(6, 0))
        e = ctk.CTkEntry(parent, height=30)
        e.insert(0, default)
        e.pack(fill="x", padx=10, pady=(2, 0))
        return e

    def _add_to_cart(self, pid, name, cost, qty):
        for item in self.cart:
            if item["id"] == pid and item["price"] == cost:
                item["qty"] += qty
                self._refresh_cart()
                return
        self.cart.append({"id": pid, "name": name, "price": cost, "qty": qty})
        self._refresh_cart()

    # ── complete purchase ─────────────────────────────────────────────────────

    def _process_purchase(self):
        if not self.selected_supplier_id:
            messagebox.showerror("No Supplier", "Please select a supplier.")
            return
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add at least one item before completing.")
            return
        try:
            discount = float(self.discount_entry.get() or 0) / 100
        except ValueError:
            messagebox.showerror("Invalid Input", "Discount must be a number.")
            return
        try:
            self.purchase_service.process_purchase(
                self.cart, self.selected_supplier_id, self.app.exchange_rate,
                payment_method=self.pay_method.get(),
                discount_pct=discount,
            )
            messagebox.showinfo("Success", "Purchase recorded and stock updated!")
            self.cart.clear()
            self.discount_entry.delete(0, "end")
            self.discount_entry.insert(0, "0")
            self._refresh_cart()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── data ──────────────────────────────────────────────────────────────────

    def refresh_data(self):
        suppliers = self.account_service.get_by_role("Supplier") or []
        self.supplier_map = {s["name"]: s["id"] for s in suppliers if s.get("name")}
        default = next(iter(self.supplier_map), None)
        if default:
            self.supplier_var.set(default)
            self.selected_supplier_id = self.supplier_map[default]
        self._filter_products()

    def _show_supplier_results(self):
        self._filter_suppliers()
        self.supplier_results.pack(fill="x", padx=10, pady=(0, 4))

    def _hide_supplier_results(self):
        self.supplier_results.pack_forget()

    def _filter_suppliers(self):
        term = self.supplier_var.get().lower().strip()
        for w in self.supplier_results.winfo_children():
            w.destroy()
        names = [n for n in self.supplier_map if term in n.lower()] if term else list(self.supplier_map)
        for name in names:
            ctk.CTkButton(
                self.supplier_results, text=name, height=28,
                fg_color="transparent", text_color=("gray10", "gray90"),
                anchor="w", hover_color=("gray80", "gray30"),
                command=lambda n=name: self._select_supplier(n),
            ).pack(fill="x", pady=1)

    def _select_supplier(self, name):
        self.supplier_var.set(name)
        self.selected_supplier_id = self.supplier_map.get(name)
        self._hide_supplier_results()

    def open_print_dialog(self):
        """Open print dialog"""
        PrintDialog(self, self.app)

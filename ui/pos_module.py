# ui/pos_module_new.py  (TEMP — review before replacing pos_module.py)

import customtkinter as ctk
from tkinter import ttk, messagebox
from ui.print_dialog import PrintDialog  # Import the print dialog


# ── helpers ──────────────────────────────────────────────────────────────────

def _compact_path(path):
    if not path or path == "Uncategorized":
        return "General"
    parts = path.split(" > ")
    return path if len(parts) <= 2 else f"{parts[0][:3]}.. > {parts[-1]}"


# ── colour / style tokens ─────────────────────────────────────────────────────
_GREEN   = ("#27ae60", "#2ecc71")
_RED     = ("#c0392b", "#e74c3c")
_ORANGE  = ("#e67e22", "#f39c12")
_DARK    = ("#2c2c2c", "#1a1a1a")
_MUTED   = ("gray55", "gray45")


class POSFrame(ctk.CTkFrame):
    def __init__(self, parent, app, sales_service, account_service, inventory_service):
        super().__init__(parent)
        self.app = app
        self.cart = []
        self.sales_service      = sales_service
        self.account_service    = account_service
        self.inventory_service  = inventory_service
        self.customer_map       = {}
        self.selected_customer_id = None

        self._build_nav()
        self._build_body()
        self.load_customers()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_nav(self):
        nav = self.app.ui_service.create_back_home_nav(
            self,
            back_command=self.safe_exit,
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
        
        ctk.CTkLabel(nav, text="Point of Sale", font=ctk.CTkFont(size=15, weight="bold")).pack(side="right", padx=20)

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        body.columnconfigure(0, weight=0)   # product panel  – fixed
        body.columnconfigure(1, weight=1)   # cart           – stretches
        body.columnconfigure(2, weight=0)   # checkout panel – fixed
        body.rowconfigure(0, weight=1)

        self._build_product_panel(body)
        self._build_cart_panel(body)
        self._build_checkout_panel(body)
        
    def open_print_dialog(self):
        """Open print dialog"""
        PrintDialog(self, self.app)

    # ── left: product search ──────────────────────────────────────────────────

    def _build_product_panel(self, parent):
        panel = ctk.CTkFrame(parent, width=260)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_propagate(False)

        ctk.CTkLabel(panel, text="Products", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4), padx=12, anchor="w")

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            panel, textvariable=self.search_var,
            placeholder_text="🔍  Search products…", height=34,
        )
        self.search_entry.pack(fill="x", padx=10, pady=(0, 4))
        self.search_entry.bind("<KeyRelease>", lambda _: self._filter_products())
        self.search_entry.bind("<FocusIn>",    lambda _: self._show_product_results())
        self.search_entry.bind("<FocusOut>",   lambda _: self.after(200, self._hide_product_results))

        self.product_results = ctk.CTkScrollableFrame(panel, height=0)
        # height managed dynamically

        ctk.CTkButton(
            panel, text="Clear", height=28, width=80,
            fg_color="transparent", border_width=1,
            command=self._clear_search,
        ).pack(pady=(2, 8))

    def _show_product_results(self):
        self._render_product_results()
        self.product_results.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _hide_product_results(self):
        self.product_results.pack_forget()

    def _filter_products(self):
        # Called on each keypress; keep it as the same entry-point,
        # but delegate to the unified renderer.
        self._render_product_results()

    def _render_product_results(self):
        term = self.search_var.get().strip()

        for w in self.product_results.winfo_children():
            w.destroy()

        # When search is empty (focus/empty state), show top sold products.
        if not term:
            top_rows = self.app.report_service.get_top_products(limit=10) or []
            results = []
            for r in top_rows:
                # report_repo returns either sqlite3.Row (keys) or tuple-like rows
                if hasattr(r, "keys"):
                    results.append(
                        {
                            "id": r["id"],
                            "name": r["name"],
                            # For POS UI we also want stock info; try to enrich from inventory search by name
                            # (fallback to 0 if not found).
                            "quantity": 0,
                            "min_threshold": 0,
                            "path": None,
                            "price": 0,
                            "_top_sold_qty": r["total_sold"] if "total_sold" in r.keys() else None,
                        }
                    )
                else:
                    # Expected tuple: (id, name, total_sold, total_revenue)
                    pid, name, total_sold, _total_revenue = r
                    results.append(
                        {
                            "id": pid,
                            "name": name,
                            "quantity": 0,
                            "min_threshold": 0,
                            "path": None,
                            "price": 0,
                            "_top_sold_qty": total_sold,
                        }
                    )

            # Enrich with real product details (price/stock/category path) if possible.
            # This keeps DB access inside service/repo layers.
            # - If inventory_service.search_products("") returns [], we’ll keep fallback values.

            # Best-effort enrichment: search by each product name (service handles DB access).
            # (Avoids new repo methods; stays within existing services.)
            enriched_map = {}
            for item in results:
                matches = self.inventory_service.search_products(item["name"]) if item["name"] else []
                if matches:
                    enriched_map[item["id"]] = matches[0]
            for item in results:
                e = enriched_map.get(item["id"])
                if e:
                    item.update(
                        {
                            "quantity": e.get("quantity", 0) or 0,
                            "min_threshold": e.get("min_threshold", 0) or 0,
                            "path": e.get("path"),
                            "price": e.get("price", 0) or 0,
                        }
                    )

            results_to_render = results
        else:
            results_to_render = self.inventory_service.search_products(term)

        for p in results_to_render:
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

            top_badge = ""
            if not term and p.get("_top_sold_qty") is not None:
                top_badge = f"  • Sold: {p.get('_top_sold_qty')}"

            ctk.CTkLabel(
                row,
                text=f"{p.get('name', '')}{top_badge}",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).pack(fill="x", padx=8, pady=(6, 0))

            info_row = ctk.CTkFrame(row, fg_color="transparent")
            info_row.pack(fill="x", padx=8, pady=(0, 6))

            ctk.CTkLabel(
                info_row,
                text=_compact_path(p.get("path")),
                font=ctk.CTkFont(size=10),
                text_color=_MUTED,
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                info_row,
                text=f"Stock: {qty}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=stock_color,
                anchor="e",
            ).pack(side="right")

            row.bind("<Button-1>", lambda _, prod=p: self._open_add_popup(prod))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda _, prod=p: self._open_add_popup(prod))
            for child in info_row.winfo_children():
                child.bind("<Button-1>", lambda _, prod=p: self._open_add_popup(prod))

    def _clear_search(self):
        self.search_var.set("")
        self._render_product_results()

    # ── middle: cart ──────────────────────────────────────────────────────────

    def _build_cart_panel(self, parent):
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=4)
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        # header row
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        ctk.CTkLabel(hdr, text="Cart", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(
            hdr, text="🗑  Clear All", height=28, width=100,
            fg_color=_RED[0], hover_color=_RED[1],
            command=self._clear_cart,
        ).pack(side="right")

        # treeview
        tree_frame = ctk.CTkFrame(panel, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "POS.Treeview",
            background="#1e1e1e", foreground="white",
            fieldbackground="#1e1e1e", rowheight=32,
            font=("Roboto", 11),
        )
        style.configure("POS.Treeview.Heading", background="#2c2c2c", foreground="#aaaaaa", font=("Roboto", 10, "bold"))
        style.map("POS.Treeview", background=[("selected", "#2d6a4f")])

        cols = ("Item", "Mode", "Qty", "Unit $", "Unit SYP", "Subtotal SYP")
        self.cart_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="POS.Treeview")
        widths = {"Item": 200, "Mode": 70, "Qty": 55, "Unit $": 80, "Unit SYP": 90, "Subtotal SYP": 120}
        for c in cols:
            self.cart_tree.heading(c, text=c)
            self.cart_tree.column(c, width=widths[c], anchor="center" if c != "Item" else "w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=vsb.set)
        self.cart_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.cart_tree.bind("<<TreeviewSelect>>", self._on_cart_select)

        # cart action bar
        action = ctk.CTkFrame(panel, fg_color="transparent")
        action.grid(row=2, column=0, sticky="ew", padx=10, pady=8)

        ctk.CTkButton(
            action, text="Remove Selected", height=32,
            fg_color=_RED[0], hover_color=_RED[1],
            command=self._remove_selected,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(action, text="Mode:").pack(side="left", padx=6)
        self.mode_var = ctk.StringVar(value="Sale")
        ctk.CTkSegmentedButton(action, values=["Sale", "Return"], variable=self.mode_var).pack(side="left", padx=6)

        ctk.CTkLabel(action, text="Unit Price ($):").pack(side="left", padx=(10, 4))
        self.unit_price_entry = ctk.CTkEntry(action, width=95, height=32)
        self.unit_price_entry.insert(0, "0.00")
        self.unit_price_entry.pack(side="left", padx=4)

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
        qty_signed = int(item["qty"])
        mode = "Sale" if qty_signed >= 0 else "Return"
        self.mode_var.set(mode)

        self.unit_price_entry.delete(0, "end")
        self.unit_price_entry.insert(0, f"{float(item['price']):.2f}")

        self.qty_entry.delete(0, "end")
        self.qty_entry.insert(0, str(abs(qty_signed)))

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
            unit_price = float(self.unit_price_entry.get())
            qty_abs = int(self.qty_entry.get())
            if unit_price < 0:
                raise ValueError("unit_price must be >= 0")
            if qty_abs <= 0:
                raise ValueError("qty must be > 0")
        except ValueError:
            messagebox.showerror("Error", "Enter valid Unit Price ($) and Qty (qty > 0).")
            return

        mode = self.mode_var.get()
        signed_qty = qty_abs if mode == "Sale" else -qty_abs

        self.cart[idx]["price"] = unit_price
        self.cart[idx]["qty"] = signed_qty
        self._refresh_cart()

    def _refresh_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)

        rate = getattr(self.app, "exchange_rate", 1.0)
        subtotal_usd = 0.0

        for idx, item in enumerate(self.cart):
            sub = item["price"] * item["qty"]
            subtotal_usd += sub
            mode = "RETURN" if item["qty"] < 0 else "SALE"
            tag  = "return" if item["qty"] < 0 else "sale"
            unit_syp = item["price"] * rate
            subtotal_syp = sub * rate

            self.cart_tree.insert(
                "", "end", iid=str(idx), tags=(tag,),
                values=(
                    item["name"], mode, item["qty"],
                    f"${item['price']:.2f}",
                    f"{unit_syp:,.0f}",
                    f"{subtotal_syp:,.0f}",
                ),
            )

        self.cart_tree.tag_configure("return", foreground="#e74c3c")
        self.cart_tree.tag_configure("sale",   foreground="white")
        self._update_totals(subtotal_usd, rate)

    # ── right: checkout ───────────────────────────────────────────────────────

    def _build_checkout_panel(self, parent):
        panel = ctk.CTkFrame(parent, width=280)
        panel.grid(row=0, column=2, sticky="nsew", padx=(8, 0))
        panel.grid_propagate(False)

        # totals display
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

        # item count badge
        self.item_count_lbl = ctk.CTkLabel(panel, text="0 items", font=ctk.CTkFont(size=11), text_color=_MUTED[0])
        self.item_count_lbl.pack()

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=8)

        # customer
        ctk.CTkLabel(panel, text="Customer", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12)
        self.cust_var = ctk.StringVar()
        self.cust_entry = ctk.CTkEntry(panel, textvariable=self.cust_var, placeholder_text="Search customer…", height=32)
        self.cust_entry.pack(fill="x", padx=10, pady=(4, 0))
        self.cust_entry.bind("<KeyRelease>", lambda _: self._filter_customers())
        self.cust_entry.bind("<FocusIn>",    lambda _: self._show_cust_results())
        self.cust_entry.bind("<FocusOut>",   lambda _: self.after(200, self._hide_cust_results))

        self.cust_results = ctk.CTkScrollableFrame(panel, height=100)

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=8)

        # discount / tax
        self.discount_entry = self._labeled_entry(panel, "Discount %", "0")
        self.tax_entry      = self._labeled_entry(panel, "Tax % (VAT)", "0")

        # payment method
        ctk.CTkLabel(panel, text="Payment Method", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(8, 2))
        self.pay_method = ctk.StringVar(value="Cash")
        ctk.CTkSegmentedButton(panel, values=["Cash", "Credit"], variable=self.pay_method).pack(fill="x", padx=10)

        # transaction type badge (auto-resolved)
        self.type_lbl = ctk.CTkLabel(
            panel, text="Type: SALE",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=_GREEN[0],
        )
        self.type_lbl.pack(pady=(8, 0))

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=8)

        # complete button
        ctk.CTkButton(
            panel, text="✔  COMPLETE TRANSACTION",
            height=52, corner_radius=8,
            fg_color=_GREEN[0], hover_color=_GREEN[1],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._complete_transaction,
        ).pack(fill="x", padx=10, pady=(0, 12))

    def _labeled_entry(self, parent, label, default):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(6, 0))
        e = ctk.CTkEntry(parent, height=30)
        e.insert(0, default)
        e.pack(fill="x", padx=10, pady=(2, 0))
        return e

    def _update_totals(self, subtotal_usd, rate):
        try:
            discount = float(self.discount_entry.get() or 0) / 100
            tax      = float(self.tax_entry.get() or 0) / 100
        except ValueError:
            discount = tax = 0.0
        final_usd = (subtotal_usd * (1 - discount)) * (1 + tax)
        self.total_usd_lbl.configure(text=f"${final_usd:.2f}")
        self.total_syp_lbl.configure(text=f"{final_usd * rate:,.0f} SYP")
        self.item_count_lbl.configure(text=f"{len(self.cart)} item{'s' if len(self.cart) != 1 else ''}")

        has_pos = any(i["qty"] > 0 for i in self.cart)
        has_neg = any(i["qty"] < 0 for i in self.cart)
        if has_pos and has_neg:
            label, color = "Type: MIXED", _ORANGE[1]
        elif has_neg:
            label, color = "Type: RETURN", _RED[0]
        else:
            label, color = "Type: SALE", _GREEN[0]
        self.type_lbl.configure(text=label, text_color=color)

    # ── customer search ───────────────────────────────────────────────────────

    def _show_cust_results(self):
        self._filter_customers()
        self.cust_results.pack(fill="x", padx=10, pady=(0, 4))

    def _hide_cust_results(self):
        self.cust_results.pack_forget()

    def _filter_customers(self):
        term = self.cust_var.get().lower().strip()
        for w in self.cust_results.winfo_children():
            w.destroy()
        names = [n for n in self.customer_map if term in n.lower()] if term else list(self.customer_map)
        for name in names:
            ctk.CTkButton(
                self.cust_results, text=name, height=28,
                fg_color="transparent", text_color=("gray10", "gray90"),
                anchor="w", hover_color=("gray80", "gray30"),
                command=lambda n=name: self._select_customer(n),
            ).pack(fill="x", pady=1)

    def _select_customer(self, name):
        self.cust_var.set(name)
        self.selected_customer_id = self.customer_map.get(name)
        self._hide_cust_results()

    def load_customers(self):
        customers = self.account_service.get_by_role("Customer") or []
        self.customer_map = {c["name"]: c["id"] for c in customers if c.get("name")}
        default = next((n for n in self.customer_map if "cash" in n.lower()), None) or (
            next(iter(self.customer_map), None)
        )
        if default:
            self.cust_var.set(default)
            self.selected_customer_id = self.customer_map[default]

    # ── add-to-cart popup ─────────────────────────────────────────────────────

    def _open_add_popup(self, product):
        self._hide_product_results()
        pop = ctk.CTkToplevel(self)
        pop.title("Add to Cart")
        pop.geometry("320x360")
        pop.resizable(False, False)
        pop.attributes("-topmost", True)
        pop.grab_set()

        ctk.CTkLabel(pop, text=product["name"], font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(16, 2))
        ctk.CTkLabel(
            pop, text=f"Available stock: {product['quantity']}",
            font=ctk.CTkFont(size=11), text_color=_MUTED[0],
        ).pack()

        ctk.CTkFrame(pop, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=16, pady=10)

        mode_var = ctk.StringVar(value="Sale")
        ctk.CTkSegmentedButton(pop, values=["Sale", "Return"], variable=mode_var).pack(padx=20, fill="x")

        price_entry = self._labeled_entry(pop, "Unit Price ($)", f"{product['price']:.2f}")
        qty_entry   = self._labeled_entry(pop, "Quantity", "1")
        qty_entry.focus()

        def _confirm():
            try:
                price = float(price_entry.get())
                qty   = int(qty_entry.get())
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Enter a positive number for quantity.", parent=pop)
                return

            if mode_var.get() == "Sale" and qty > product["quantity"]:
                messagebox.showerror("Stock Error", f"Only {product['quantity']} units available.", parent=pop)
                return

            final_qty = qty if mode_var.get() == "Sale" else -qty
            self._add_to_cart(product["id"], product["name"], price, final_qty)
            pop.destroy()

        pop.bind("<Return>", lambda _: _confirm())
        ctk.CTkButton(
            pop, text="Add to Cart", height=40,
            fg_color=_GREEN[0], hover_color=_GREEN[1],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=_confirm,
        ).pack(fill="x", padx=20, pady=16)

    def _add_to_cart(self, pid, name, price, qty):
        for item in self.cart:
            if item["id"] == pid and item["price"] == price:
                item["qty"] += qty
                if item["qty"] == 0:
                    self.cart.remove(item)
                self._refresh_cart()
                return
        self.cart.append({"id": pid, "name": name, "price": price, "qty": qty})
        self._refresh_cart()

    # ── transaction ───────────────────────────────────────────────────────────

    def _complete_transaction(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add at least one item before completing.")
            return
        if not self.selected_customer_id:
            messagebox.showerror("No Customer", "Please select a customer.")
            return

        has_pos = any(i["qty"] > 0 for i in self.cart)
        has_neg = any(i["qty"] < 0 for i in self.cart)
        inv_type = "MIXED_SALE" if (has_pos and has_neg) else ("RETURN" if has_neg else "SALE")

        try:
            discount = float(self.discount_entry.get() or 0) / 100
            tax      = float(self.tax_entry.get() or 0) / 100
        except ValueError:
            messagebox.showerror("Invalid Input", "Discount and Tax must be numbers.")
            return

        try:
            inv_id, total = self.sales_service.process_sale(
                self.cart, inv_type,
                self.selected_customer_id,
                discount, tax,
                self.pay_method.get(),
                getattr(self.app, "exchange_rate", 1.0),
            )
            messagebox.showinfo(
                "Transaction Complete",
                f"Invoice #{inv_id}  [{inv_type}]\nTotal: ${total:.2f}",
            )
            self.cart.clear()
            self._refresh_cart()
            self.load_customers()
        except Exception as e:
            messagebox.showerror("Transaction Failed", str(e))

    # ── navigation ────────────────────────────────────────────────────────────

    def safe_exit(self):
        if self.cart and not messagebox.askyesno("Leave POS", "Cart has items. Discard and leave?"):
            return
        self.app.go_back()

    def refresh_data(self):
        self.load_customers()

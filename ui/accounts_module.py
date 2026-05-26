# accounts_module.py

import csv
import os
from datetime import datetime
from tkinter import Menu, messagebox, ttk

import customtkinter as ctk

from ui.print_dialog import PrintDialog


class AccountsFrame(ctk.CTkFrame):
    def __init__(self, parent, app, account_service):
        super().__init__(parent)
        self.app = app
        self.account_service = account_service
        self.payment_service = getattr(app, "payment_service", None)

        self.selected_account_id = None
        self.current_rate = 1.0
        self.page_size = 25
        self.current_page = 0
        self.filtered_accounts = []
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

        ctk.CTkButton(
            nav_bar,
            text="Home",
            width=100,
            command=self.app.go_home,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            nav_bar,
            text="Print",
            width=100,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.open_print_dialog,
        ).pack(side="left", padx=5)

        ctk.CTkLabel(
            nav_bar,
            text="Partner Management",
            font=("Arial", 16, "bold"),
        ).pack(side="right", padx=20)

        # --- MAIN CONTENT PANE ---
        pane = ctk.CTkFrame(self)
        pane.pack(fill="both", expand=True, padx=15, pady=10)

        # LEFT side: Account List
        left_panel = ctk.CTkFrame(pane)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Search Bar
        search_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=10)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_data())

        ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by name or phone...",
            textvariable=self.search_var,
        ).pack(fill="x", padx=5)

        # Filter toolbar
        filter_frame = ctk.CTkFrame(left_panel, fg_color="#2b2b2b", corner_radius=8)
        filter_frame.pack(fill="x", padx=10, pady=(0, 10))

        filter_frame.grid_columnconfigure(0, weight=0)
        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(2, weight=0)
        filter_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(filter_frame, text="Role:", font=("Arial", 12)).grid(
            row=0, column=0, padx=(10, 5), pady=8, sticky="w"
        )
        self.role_filter_var = ctk.StringVar(value="All")
        self.role_filter_var.trace_add("write", lambda *args: self.refresh_data())
        self.role_filter_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.role_filter_var,
            values=["All", "Customer", "Supplier"],
            width=150,
        )
        self.role_filter_dropdown.grid(row=0, column=1, padx=(0, 15), pady=8, sticky="w")

        ctk.CTkLabel(filter_frame, text="Balance:", font=("Arial", 12)).grid(
            row=0, column=2, padx=(5, 5), pady=8, sticky="w"
        )
        self.balance_filter_var = ctk.StringVar(value="All")
        self.balance_filter_var.trace_add("write", lambda *args: self.refresh_data())
        self.balance_filter_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            variable=self.balance_filter_var,
            values=["All", "Positive", "Zero", "Negative"],
            width=150,
        )
        self.balance_filter_dropdown.grid(row=0, column=3, padx=(0, 10), pady=8, sticky="w")

        # Treeview
        cols = ("ID", "Name", "Role", "Phone", "Balance ($)", "Balance (SYP)")

        main_tree_frame = ctk.CTkFrame(left_panel)
        main_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(main_tree_frame, columns=cols, show="headings", height=15)

        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=90 if col != "Name" else 180)

        v_scrollbar = ttk.Scrollbar(main_tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="left", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_account_select)
        self.tree.bind("<Double-1>", self.on_account_double_click)

        # Pagination
        pag_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        pag_frame.pack(fill="x", padx=10, pady=(0, 5))

        self.prev_btn = ctk.CTkButton(pag_frame, text="<< Prev", width=80, command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)

        self.page_label = ctk.CTkLabel(pag_frame, text="Page 1", font=("Arial", 12))
        self.page_label.pack(side="left", padx=10)

        self.next_btn = ctk.CTkButton(pag_frame, text="Next >>", width=80, command=self.next_page)
        self.next_btn.pack(side="left", padx=5)

        export_btn = ctk.CTkButton(
            left_panel,
            text="📄 Export Filtered to CSV",
            fg_color="#27ae60",
            height=35,
            command=self.export_to_csv,
        )
        export_btn.pack(fill="x", padx=10, pady=(5, 10))

        # RIGHT side: Action Panel
        right_panel = ctk.CTkScrollableFrame(pane, width=320)
        right_panel.pack(side="right", fill="y", padx=(10, 0))

        ctk.CTkLabel(
            right_panel,
            text="Account Actions",
            font=("Arial", 18, "bold"),
        ).pack(pady=(10, 10))

        self.selection_lbl = ctk.CTkLabel(
            right_panel,
            text="Selected: None",
            font=("Arial", 13, "bold"),
            wraplength=260,
        )
        self.selection_lbl.pack(fill="x", padx=25, pady=(0, 8))

        self.balance_lbl = ctk.CTkLabel(
            right_panel,
            text="Balance: $0.00",
            font=("Arial", 13, "bold"),
        )
        self.balance_lbl.pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkButton(
            right_panel,
            text="+ Add Account",
            fg_color="#27ae60",
            command=self.add_account,
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(
            right_panel,
            text="Edit Selected",
            fg_color="#2980b9",
            command=self.edit_selected_account,
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(
            right_panel,
            text="Delete Selected",
            fg_color="#e74c3c",
            command=self.delete_account,
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkLabel(
            right_panel,
            text="Payments & History",
            font=("Arial", 14, "bold"),
            text_color="#f1c40f",
        ).pack(pady=(20, 8))

        ctk.CTkButton(
            right_panel,
            text="Record Payment",
            fg_color="#9b59b6",
            command=self.record_payment,
        ).pack(fill="x", padx=25, pady=5)

        ctk.CTkButton(
            right_panel,
            text="View History",
            fg_color="#f39c12",
            command=self.view_payment_history,
        ).pack(fill="x", padx=25, pady=5)

        # Context menu
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit Account", command=self.edit_selected_account)
        self.context_menu.add_command(label="Record Payment", command=self.record_payment)
        self.context_menu.add_command(label="View History", command=self.view_payment_history)
        self.context_menu.add_command(label="Delete Account", command=self.delete_account)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.refresh_data()

    # ==========================================
    # Helper Methods
    # ==========================================

    def create_input(self, parent, label):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=25)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=25, pady=(0, 10))
        return entry

    def get_sort_key(self, account, col):
        if col == "ID":
            try:
                return float(account.get("id") or 0)
            except Exception:
                return 0
        if col in {"Balance ($)", "Balance (SYP)"}:
            try:
                return float(account.get("_balance_sort", 0))
            except Exception:
                return 0
        mapping = {
            "Name": "name",
            "Role": "role",
            "Phone": "phone",
        }
        key = mapping.get(col, col.lower())
        return str(account.get(key, "")).lower()

    def update_selected_summary(self, account=None):
        if not account:
            self.selection_lbl.configure(text="Selected: None")
            self.balance_lbl.configure(text="Balance: $0.00")
            return

        name = account.get("name", "Unknown")
        role = account.get("role", "")
        self.selection_lbl.configure(text=f"Selected: {name} ({role})")
        balance = float(account.get("balance", 0.0) or 0.0)
        self.balance_lbl.configure(text=f"Balance: ${balance:,.2f}")

    # ==========================================
    # Data Loading / Filtering / Sorting
    # ==========================================

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.current_rate = getattr(self.app, "exchange_rate", 1.0)
        search = self.search_var.get().strip()
        role = self.role_filter_var.get()
        balance_filter = self.balance_filter_var.get()

        accounts = self.account_service.get_accounts(role=role, search=search)

        self.filtered_accounts = []
        for acc in accounts:
            usd_bal = float(acc.get("balance", 0.0) or 0.0)
            acc["_balance_sort"] = usd_bal

            if balance_filter == "Positive" and usd_bal <= 0:
                continue
            if balance_filter == "Zero" and abs(usd_bal) > 0.01:
                continue
            if balance_filter == "Negative" and usd_bal >= 0:
                continue

            self.filtered_accounts.append(acc)

        if self.sort_col:
            self.filtered_accounts.sort(
                key=lambda a: self.get_sort_key(a, self.sort_col),
                reverse=self.sort_reverse,
            )

        self.current_page = 0
        self.populate_tree()
        self.update_page_label()
        self.update_pagination_buttons()
        self.update_selected_summary()

    def sort_by_column(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
        self.refresh_data()

    def populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        start = self.current_page * self.page_size
        end = start + self.page_size
        page_accounts = self.filtered_accounts[start:end]

        self.tree.tag_configure("positive", background="#2d5a2d")
        self.tree.tag_configure("negative", background="#6a2f2f")
        self.tree.tag_configure("zero", background="#3a3a3a")

        for acc in page_accounts:
            account_id = acc.get("id")
            usd_bal = float(acc.get("balance", 0.0) or 0.0)
            syp_bal = usd_bal * float(self.current_rate)

            if usd_bal > 0:
                tags = ("positive",)
            elif usd_bal < 0:
                tags = ("negative",)
            else:
                tags = ("zero",)

            self.tree.insert(
                "",
                "end",
                iid=str(account_id),
                values=(
                    account_id,
                    acc.get("name", ""),
                    acc.get("role", ""),
                    acc.get("phone", ""),
                    f"${usd_bal:,.2f}",
                    f"{syp_bal:,.0f} SYP",
                ),
                tags=tags,
            )

    def update_page_label(self):
        total_pages = (len(self.filtered_accounts) + self.page_size - 1) // self.page_size
        self.page_label.configure(
            text=f"Page {self.current_page + 1} / {total_pages or 1} ({len(self.filtered_accounts)} items)"
        )

    def update_pagination_buttons(self):
        total_pages = (len(self.filtered_accounts) + self.page_size - 1) // self.page_size
        self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.populate_tree()
            self.update_page_label()
            self.update_pagination_buttons()

    def next_page(self):
        total_pages = (len(self.filtered_accounts) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.populate_tree()
            self.update_page_label()
            self.update_pagination_buttons()

    # ==========================================
    # Selection / Popup Launchers
    # ==========================================

    def on_account_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            self.selected_account_id = None
            self.update_selected_summary()
            return

        self.selected_account_id = sel[0]
        try:
            self.selected_account_id = int(self.selected_account_id)
        except (TypeError, ValueError):
            pass

        acc = self.account_service.get_by_id(self.selected_account_id)
        self.update_selected_summary(acc)

    def on_account_double_click(self, _event):
        sel = self.tree.selection()
        if sel:
            self.selected_account_id = sel[0]
            try:
                self.selected_account_id = int(self.selected_account_id)
            except (TypeError, ValueError):
                pass

        if self.selected_account_id is None:
            return

        self.open_account_popup("EDIT", self.selected_account_id)

    def add_account(self):
        self.open_account_popup("ADD")

    def edit_selected_account(self):
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return
        self.open_account_popup("EDIT", self.selected_account_id)

    def clear_selection(self):
        self.selected_account_id = None
        self.tree.selection_remove(self.tree.selection())
        self.update_selected_summary()

    # ==========================================
    # Popup CRUD
    # ==========================================

    def open_account_popup(self, mode: str, account_id=None):
        if not isinstance(mode, str):
            mode = "EDIT"

        if mode not in {"ADD", "EDIT"}:
            mode = "EDIT"

        account = None
        if mode == "EDIT":
            if account_id is None:
                messagebox.showwarning("Selection Required", "Please select an account first.", parent=self)
                return
            account = self.account_service.get_by_id(account_id)
            if not account:
                messagebox.showerror("Error", "Account not found.", parent=self)
                return

        win = ctk.CTkToplevel(self)
        win.title("Add Account" if mode == "ADD" else "Edit Account")
        win.geometry("460x560")
        win.resizable(False, False)
        win.attributes("-topmost", True)

        title_txt = "Add Account" if mode == "ADD" else f"Edit: {account.get('name', '')}"
        ctk.CTkLabel(win, text=title_txt, font=("Arial", 16, "bold")).pack(pady=(16, 8))

        name_var = ctk.StringVar(value=(account.get("name", "") if account else ""))
        role_var = ctk.StringVar(value=(account.get("role", "Customer") if account else "Customer"))
        phone_var = ctk.StringVar(value=(account.get("phone", "") if account else ""))
        email_var = ctk.StringVar(value=(account.get("email", "") if account else ""))
        address_var = ctk.StringVar(value=(account.get("address", "") if account else ""))

        def labeled(parent, label: str, var: ctk.StringVar):
            ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=20, pady=(8, 3))
            entry = ctk.CTkEntry(parent, textvariable=var)
            entry.pack(fill="x", padx=20)
            return entry

        labeled(win, "Full Name / Company", name_var)

        ctk.CTkLabel(win, text="Role").pack(anchor="w", padx=20, pady=(8, 3))
        role_dd = ctk.CTkOptionMenu(win, variable=role_var, values=["Customer", "Supplier"], width=330)
        role_dd.pack(fill="x", padx=20)

        labeled(win, "Phone Number", phone_var)
        labeled(win, "Email Address", email_var)
        labeled(win, "Physical Address", address_var)

        actions = ctk.CTkFrame(win, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(16, 6))

        def read_validate():
            name = name_var.get().strip()
            if not name:
                raise ValueError("Name is required.")

            role = role_var.get().strip()
            if role not in ("Customer", "Supplier"):
                raise ValueError("Invalid role.")

            phone = phone_var.get().strip()
            email = email_var.get().strip()
            address = address_var.get().strip()

            return name, role, phone, email, address

        def on_add():
            try:
                name, role, phone, email, address = read_validate()
                self.account_service.add_account(
                    name=name,
                    role=role,
                    phone=phone,
                    email=email,
                    address=address,
                )
                self.refresh_data()
                win.destroy()
                messagebox.showinfo("Success", "Account created successfully.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        def on_update():
            try:
                name, role, phone, email, address = read_validate()
                self.account_service.update_account(
                    account["id"],
                    {
                        "name": name,
                        "role": role,
                        "phone": phone,
                        "email": email,
                        "address": address,
                    },
                )
                self.refresh_data()
                win.destroy()
                messagebox.showinfo("Success", "Account updated successfully.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        def on_delete():
            if not messagebox.askyesno(
                "Confirm Delete",
                f"Delete '{account.get('name', '')}'?",
                parent=win,
            ):
                return

            try:
                self.account_service.delete_account(account["id"])
                self.refresh_data()
                self.clear_selection()
                win.destroy()
                messagebox.showinfo("Success", "Account deleted successfully.", parent=self)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win)

        if mode == "ADD":
            ctk.CTkButton(actions, text="Save", fg_color="#27ae60", command=on_add).pack(fill="x", pady=6)
        else:
            ctk.CTkButton(actions, text="Update", fg_color="#2980b9", command=on_update).pack(fill="x", pady=6)
            ctk.CTkButton(actions, text="Delete", fg_color="#e74c3c", command=on_delete).pack(fill="x", pady=6)

        ctk.CTkButton(actions, text="Cancel", fg_color="#7f8c8d", command=win.destroy).pack(fill="x", pady=(6, 0))

        try:
            win.after(50, lambda: win.focus_force())
        except Exception:
            pass

    # ==========================================
    # CRUD Actions
    # ==========================================

    def delete_account(self):
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        account = self.account_service.get_by_id(self.selected_account_id)
        if not account:
            messagebox.showerror("Error", "Account not found.")
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{account.get('name', '')}'?",
            parent=self,
        ):
            return

        try:
            self.account_service.delete_account(account["id"])
            self.refresh_data()
            self.clear_selection()
            messagebox.showinfo("Success", "Account deleted successfully.")
        except PermissionError as e:
            messagebox.showerror("Blocked", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete account: {str(e)}")

    def save_account(self):
        self.add_account()

    def update_account(self):
        self.edit_selected_account()

    # ==========================================
    # Payments / History
    # ==========================================

    def record_payment(self):
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        if not self.payment_service:
            messagebox.showerror("Error", "Payment service not available.")
            return

        payment_dialog = PaymentDialog(self, self.app, self.selected_account_id, self.payment_service)
        payment_dialog.grab_set()
        self.wait_window(payment_dialog)
        self.refresh_data()

    def view_payment_history(self):
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        if not self.payment_service:
            messagebox.showerror("Error", "Payment service not available.")
            return

        history_dialog = PaymentHistoryDialog(
            self,
            self.app,
            self.selected_account_id,
            self.payment_service,
        )
        history_dialog.grab_set()
        self.wait_window(history_dialog)

    # ==========================================
    # Context / Export / Print
    # ==========================================

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.selected_account_id = item
            try:
                self.selected_account_id = int(self.selected_account_id)
            except (TypeError, ValueError):
                pass
            self.context_menu.post(event.x_root, event.y_root)

    def export_to_csv(self):
        if not self.filtered_accounts:
            messagebox.showwarning("No Data", "No filtered accounts to export.")
            return

        filename = f"accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(os.getcwd(), filename)

        cols = ["id", "name", "role", "phone", "email", "address", "balance"]

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=cols)
                writer.writeheader()
                for acc in self.filtered_accounts:
                    row = {k: acc.get(k, "") for k in cols}
                    writer.writerow(row)

            messagebox.showinfo(
                "Export Complete",
                f"Exported {len(self.filtered_accounts)} items to '{filename}'",
            )
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def open_print_dialog(self):
        PrintDialog(self, self.app)


class PaymentDialog(ctk.CTkToplevel):
    """Modal dialog for recording payments."""

    def __init__(self, parent, app, account_id, payment_service):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.account_id = account_id
        self.payment_service = payment_service

        self.title("Record Payment")
        self.geometry("420x640")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()
        self.focus_set()

        account = self.app.account_service.get_by_id(account_id)
        self.account_name = account.get("name", "Unknown")

        ctk.CTkLabel(
            self,
            text=f"Record Payment for {self.account_name}",
            font=("Arial", 16, "bold"),
        ).pack(pady=20)

        ctk.CTkLabel(self, text="Amount ($)").pack(anchor="w", padx=25)
        self.amount_entry = ctk.CTkEntry(self)
        self.amount_entry.pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(self, text="Payment Type").pack(anchor="w", padx=25)
        self.payment_type_var = ctk.StringVar(value="Payment In")
        self.payment_type_dropdown = ctk.CTkOptionMenu(
            self,
            values=["Payment In", "Payment Out"],
            variable=self.payment_type_var,
        )
        self.payment_type_dropdown.pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(self, text="Payment Method").pack(anchor="w", padx=25)
        self.payment_method_var = ctk.StringVar(value="Cash")
        self.payment_method_dropdown = ctk.CTkOptionMenu(
            self,
            values=["Cash", "Bank Transfer", "Check", "Credit Card", "Other"],
            variable=self.payment_method_var,
        )
        self.payment_method_dropdown.pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(self, text="Reference Number (Optional)").pack(anchor="w", padx=25)
        self.ref_entry = ctk.CTkEntry(self)
        self.ref_entry.pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkLabel(self, text="Notes (Optional)").pack(anchor="w", padx=25)
        self.notes_text = ctk.CTkTextbox(self, height=50)
        self.notes_text.pack(fill="x", padx=25, pady=(0, 15))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=(10, 18))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#7f8c8d",
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Record Payment",
            fg_color="#27ae60",
            command=self.record_payment,
        ).pack(side="left", fill="x", expand=True, padx=5)

    def record_payment(self):
        try:
            amount_str = self.amount_entry.get().strip()
            if not amount_str:
                messagebox.showwarning("Required", "Amount is required.")
                return

            try:
                amount = float(amount_str)
                if amount <= 0:
                    messagebox.showwarning("Invalid", "Amount must be greater than zero.")
                    return
            except ValueError:
                messagebox.showerror("Invalid", "Amount must be a valid number.")
                return

            payment_type = self.payment_type_var.get()
            payment_method = self.payment_method_var.get()
            reference_number = self.ref_entry.get().strip() or None
            notes = self.notes_text.get("1.0", "end-1c").strip() or None
            user_id = getattr(self.app, "current_user_id", None)

            self.payment_service.add_payment(
                account_id=self.account_id,
                amount=amount,
                payment_type=payment_type,
                payment_method=payment_method,
                reference_number=reference_number,
                notes=notes,
                created_by=user_id,
            )

            messagebox.showinfo("Success", "Payment recorded successfully.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record payment: {str(e)}")


class PaymentHistoryDialog(ctk.CTkToplevel):
    """Modal dialog for viewing payment history."""

    def __init__(self, parent, app, account_id, payment_service):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.account_id = account_id
        self.payment_service = payment_service

        self.title("Payment History")
        self.geometry("760x520")
        self.resizable(True, True)

        self.transient(parent)
        self.grab_set()
        self.focus_set()

        account = self.app.account_service.get_by_id(account_id)
        self.account_name = account.get("name", "Unknown")

        ctk.CTkLabel(
            self,
            text=f"Payment History for {self.account_name}",
            font=("Arial", 16, "bold"),
        ).pack(pady=10)

        cols = ("Date", "Type", "Method", "Amount", "Reference", "Notes", "Created By")
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.history_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
        for col in cols:
            self.history_tree.heading(col, text=col)
            if col == "Notes":
                self.history_tree.column(col, width=180)
            elif col in ["Date", "Amount"]:
                self.history_tree.column(col, width=110)
            elif col == "Created By":
                self.history_tree.column(col, width=100)
            else:
                self.history_tree.column(col, width=90)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        self.refresh_history()

        ctk.CTkButton(
            self,
            text="Close",
            fg_color="#7f8c8d",
            command=self.destroy,
        ).pack(pady=10)

    def refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        try:
            payments = self.payment_service.get_payment_history(self.account_id, limit=100)

            for payment in payments:
                date_str = str(payment.get("date", ""))[:19]
                amount = payment.get("amount", 0)
                direction = payment.get("direction", "+")
                formatted_amount = f"{direction}${abs(amount):,.2f}"

                notes_val = payment.get("notes", "") or ""
                if len(str(notes_val)) > 30:
                    notes_val = str(notes_val)[:30] + "..."

                self.history_tree.insert(
                    "",
                    "end",
                    values=(
                        date_str,
                        payment.get("payment_type", ""),
                        payment.get("payment_method", ""),
                        formatted_amount,
                        payment.get("reference_number", ""),
                        notes_val,
                        payment.get("created_by_username", "System"),
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load payment history: {str(e)}")

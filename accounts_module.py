# accounts_module.py

import customtkinter as ctk
from tkinter import ttk, messagebox


class AccountsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.selected_account_id = None

        # --- NAVIGATION BAR ---
        nav_bar = ctk.CTkFrame(self, fg_color="transparent")
        nav_bar.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkButton(nav_bar, text="Back", width=100, fg_color="#444444", hover_color="#555555",
                      command=self.app.go_back).pack(side="left", padx=5)
        ctk.CTkButton(nav_bar, text="Home", width=100, command=self.app.go_home).pack(side="left", padx=5)

        ctk.CTkLabel(nav_bar, text="Partner Management", font=("Arial", 16, "bold")).pack(side="right", padx=20)

        # --- MAIN LAYOUT ---
        pane = ctk.CTkFrame(self)
        pane.pack(fill="both", expand=True, padx=15, pady=10)

        # LEFT side: Account List & Search
        left_panel = ctk.CTkFrame(pane)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        search_bar = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_bar.pack(fill="x", padx=10, pady=10)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_list())
        ctk.CTkEntry(search_bar, placeholder_text="Search by name or phone...",
                     textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=5)

        self.role_filter = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(search_bar, values=["All", "Customer", "Supplier"],
                          variable=self.role_filter, command=lambda e: self.refresh_list(), width=120).pack(side="left",
                                                                                                            padx=5)

        # Treeview for Accounts
        cols = ("ID", "Name", "Role", "Phone", "Balance (USD)", "Balance (SYP)")
        self.tree = ttk.Treeview(left_panel, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col != "Name" else 200)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_account_select)

        # RIGHT side: Edit/Add Form
        right_panel = ctk.CTkFrame(pane, width=350)
        right_panel.pack(side="right", fill="y")

        ctk.CTkLabel(right_panel, text="Account Details", font=("Arial", 18, "bold")).pack(pady=20)

        self.name_entry = self.create_input(right_panel, "Full Name / Company")

        ctk.CTkLabel(right_panel, text="Role").pack(anchor="w", padx=25)
        self.role_var = ctk.StringVar(value="Customer")
        self.role_dropdown = ctk.CTkOptionMenu(right_panel, values=["Customer", "Supplier"], variable=self.role_var)
        self.role_dropdown.pack(fill="x", padx=25, pady=(0, 15))

        self.phone_entry = self.create_input(right_panel, "Phone Number")
        self.email_entry = self.create_input(right_panel, "Email Address")
        self.address_entry = self.create_input(right_panel, "Physical Address")

        # Balance Display (Read-Only)
        self.balance_lbl = ctk.CTkLabel(right_panel, text="Current Balance: €0.00", font=("Arial", 14, "bold"))
        self.balance_lbl.pack(pady=10)

        # Buttons
        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=25)

        ctk.CTkButton(btn_frame, text="Save New", fg_color="#27ae60", command=self.save_account).pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame, text="Update Selected", fg_color="#2980b9", command=self.update_account).pack(fill="x",
                                                                                                               pady=5)
        ctk.CTkButton(btn_frame, text="Clear Form", fg_color="#7f8c8d", command=self.clear_form).pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame, text="Delete Account", fg_color="#e74c3c", command=self.delete_account).pack(fill="x",
                                                                                                              pady=20)

        self.refresh_list()

    # ==========================================
    # UI HELPERS
    # ==========================================
    def create_input(self, parent, label):
        ctk.CTkLabel(parent, text=label).pack(anchor="w", padx=25)
        entry = ctk.CTkEntry(parent)
        entry.pack(fill="x", padx=25, pady=(0, 15))
        return entry

    # ==========================================
    # LOGIC
    # ==========================================
    def refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        rate = getattr(self.app, 'exchange_rate', 1.0)

        search = self.search_var.get().lower()
        role = self.role_filter.get()

        rows = self.account_service.get_accounts(search, role)

        for r in rows:
            usd_bal = r["balance"]
            syp_bal = usd_bal * rate

            self.tree.insert("", "end", iid=str(r["id"]), values=(
                r["id"],
                r["name"],
                r["role"],
                r["phone"],
                f"${usd_bal:,.2f}",
                f"{syp_bal:,.0f} SYP"
            ))

    def on_account_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        self.selected_account_id = sel[0]

        acc = self.account_service.get_account_by_id(self.selected_account_id)

        if acc:
            self.clear_form(keep_id=True)

            self.name_entry.insert(0, acc["name"])
            self.role_var.set(acc["role"])
            self.phone_entry.insert(0, acc["phone"] or "")
            self.email_entry.insert(0, acc["email"] or "")
            self.address_entry.insert(0, acc["address"] or "")
            self.balance_lbl.configure(
                text=f"Current Balance: €{acc['balance']:,.2f}"
            )

    def clear_form(self, keep_id=False):
        if not keep_id:
            self.selected_account_id = None
        for entry in [self.name_entry, self.phone_entry, self.email_entry, self.address_entry]:
            entry.delete(0, 'end')
        self.balance_lbl.configure(text="Current Balance: €0.00")

    def save_account(self):
        name = self.name_entry.get().strip()

        try:
            self.account_service.create_account(
                name=name,
                role=self.role_var.get(),
                phone=self.phone_entry.get(),
                email=self.email_entry.get(),
                address=self.address_entry.get()
            )

            self.refresh_list()
            self.clear_form()
            messagebox.showinfo("Success", "Account created successfully.")

        except ValueError as e:
            messagebox.showwarning("Validation Error", str(e))

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_account(self):
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        account_data = {
            "name": self.name_entry.get(),
            "role": self.role_var.get(),
            "phone": self.phone_entry.get(),
            "email": self.email_entry.get(),
            "address": self.address_entry.get()
        }

        try:
            self.account_service.update_account(self.selected_account_id, account_data)

            self.refresh_list()
            messagebox.showinfo("Success", "Account updated successfully.")

        except ValueError as e:
            messagebox.showwarning("Validation Error", str(e))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update account: {str(e)}")

    def delete_account(self):
        # 1. UI State Validation
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        # 2. UI Confirmation
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this partner?"):
            return

        # 3. Execution via Service
        try:
            self.account_service.delete_account(self.selected_account_id)
            
            # 4. Success Feedback & Cleanup
            self.refresh_list()
            self.clear_form()
            messagebox.showinfo("Success", "Account deleted successfully.")
            
        except PermissionError as e:
            # Specific catch for our business rule violation
            messagebox.showerror("Blocked", str(e))
        except Exception as e:
            # General catch for database or unexpected errors
            messagebox.showerror("Error", f"Failed to delete account: {str(e)}")

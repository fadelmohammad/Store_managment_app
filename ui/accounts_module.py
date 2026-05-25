# accounts_module.py

import customtkinter as ctk
from tkinter import ttk, messagebox
from ui.print_dialog import PrintDialog  # Import the print dialog
import tkinter as tk  # Need this for the new dialogs


class AccountsFrame(ctk.CTkFrame):
    def __init__(self, parent, app, account_service):
        super().__init__(parent)
        self.app = app
        self.account_service = account_service
        self.selected_account_id = None
        self.payment_service = getattr(app, 'payment_service', None)  # Get payment service from app

        # --- NAVIGATION BAR ---
        nav_bar = self.app.ui_service.create_back_home_nav(self, back_text="Back", home_text="Home")
        
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
            nav_bar,
            text="Partner Management",
            font=("Arial", 16, "bold"),
        ).pack(side="right", padx=20)

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

        ctk.CTkEntry(
            search_bar,
            placeholder_text="Search by name or phone...",
            textvariable=self.search_var,
        ).pack(side="left", fill="x", expand=True, padx=5)

        self.role_filter = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(
            search_bar,
            values=["All", "Customer", "Supplier"],
            variable=self.role_filter,
            command=lambda e: self.refresh_list(),
            width=120,
        ).pack(side="left", padx=5)

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

        ctk.CTkLabel(right_panel, text="Account Details", font=("Arial", 18, "bold")).pack(
            pady=20
        )

        self.name_entry = self.create_input(right_panel, "Full Name / Company")

        ctk.CTkLabel(right_panel, text="Role").pack(anchor="w", padx=25)
        self.role_var = ctk.StringVar(value="Customer")
        self.role_dropdown = ctk.CTkOptionMenu(
            right_panel,
            values=["Customer", "Supplier"],
            variable=self.role_var,
        )
        self.role_dropdown.pack(fill="x", padx=25, pady=(0, 15))

        self.phone_entry = self.create_input(right_panel, "Phone Number")
        self.email_entry = self.create_input(right_panel, "Email Address")
        self.address_entry = self.create_input(right_panel, "Physical Address")

        # Balance Display (Read-Only)
        self.balance_lbl = ctk.CTkLabel(
            right_panel, text="Current Balance: €0.00", font=("Arial", 14, "bold")
        )
        self.balance_lbl.pack(pady=10)

        # Buttons
        btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=25)

        ctk.CTkButton(
            btn_frame,
            text="Save New",
            fg_color="#27ae60",
            command=self.save_account,
        ).pack(fill="x", pady=5)

        ctk.CTkButton(
            btn_frame,
            text="Update Selected",
            fg_color="#2980b9",
            command=self.update_account,
        ).pack(fill="x", pady=5)

        ctk.CTkButton(
            btn_frame,
            text="Clear Form",
            fg_color="#7f8c8d",
            command=self.clear_form,
        ).pack(fill="x", pady=5)

        ctk.CTkButton(
            btn_frame,
            text="Delete Account",
            fg_color="#e74c3c",
            command=self.delete_account,
        ).pack(fill="x", pady=5)

        # Payment and History buttons
        payment_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        payment_btn_frame.pack(fill="x", pady=10, padx=25)

        ctk.CTkButton(
            payment_btn_frame,
            text="Record Payment",
            fg_color="#9b59b6",
            command=self.record_payment,
        ).pack(fill="x", pady=5)

        ctk.CTkButton(
            payment_btn_frame,
            text="View History",
            fg_color="#f39c12",
            command=self.view_payment_history,
        ).pack(fill="x", pady=5)

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
    # PAYMENT FUNCTIONALITY
    # ==========================================
    def record_payment(self):
        """Open a dialog to record a payment for the selected account."""
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        if not self.payment_service:
            messagebox.showerror("Error", "Payment service not available.")
            return

        # Create a modal dialog for recording payment
        payment_dialog = PaymentDialog(self, self.app, self.selected_account_id, self.payment_service)
        payment_dialog.grab_set()  # Make dialog modal
        self.wait_window(payment_dialog)  # Wait for dialog to close
        self.refresh_list()  # Refresh the account list after payment is recorded

    def view_payment_history(self):
        """Open a dialog to view payment history for the selected account."""
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        if not self.payment_service:
            messagebox.showerror("Error", "Payment service not available.")
            return

        # Create a modal dialog to view payment history
        history_dialog = PaymentHistoryDialog(self, self.app, self.selected_account_id, self.payment_service)
        history_dialog.grab_set()  # Make dialog modal
        self.wait_window(history_dialog)  # Wait for dialog to close

    # ==========================================
    # LOGIC
    # ==========================================
    def refresh_list(self):
        """Fetches accounts based on search and role filters."""
        for i in self.tree.get_children():
            self.tree.delete(i)

        rate = getattr(self.app, "exchange_rate", 1.0)

        search = self.search_var.get()
        role = self.role_filter.get()

        accounts = self.account_service.get_accounts(role=role, search=search)

        for acc in accounts:
            account_id = acc.get("id")
            usd_bal = acc.get("balance", 0.0) or 0.0
            syp_bal = float(usd_bal) * float(rate)

            self.tree.insert(
                "",
                "end",
                iid=str(account_id),
                values=(
                    account_id,
                    acc.get("name", ""),
                    acc.get("role", ""),
                    acc.get("phone", ""),
                    f"${float(usd_bal):,.2f}",
                    f"{syp_bal:,.0f} SYP",
                ),
            )

    def on_account_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        self.selected_account_id = sel[0]
        try:
            self.selected_account_id = int(self.selected_account_id)
        except (TypeError, ValueError):
            # Keep as-is if conversion fails
            pass

        acc = self.account_service.get_by_id(self.selected_account_id)
        if not acc:
            return

        self.clear_form(keep_id=True)

        self.name_entry.insert(0, acc.get("name") or "")
        self.role_var.set(acc.get("role") or "Customer")
        self.phone_entry.insert(0, acc.get("phone") or "")
        self.email_entry.insert(0, acc.get("email") or "")
        self.address_entry.insert(0, acc.get("address") or "")

        balance = float(acc.get("balance") or 0.0)
        self.balance_lbl.configure(text=f"Current Balance: €{balance:,.2f}")

    def clear_form(self, keep_id=False):
        if not keep_id:
            self.selected_account_id = None
        for entry in [self.name_entry, self.phone_entry, self.email_entry, self.address_entry]:
            entry.delete(0, "end")
        self.balance_lbl.configure(text="Current Balance: €0.00")

    def save_account(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Required", "Name is required.")
            return

        try:
            self.account_service.add_account(
                name=name,
                role=self.role_var.get(),
                phone=self.phone_entry.get(),
                email=self.email_entry.get(),
                address=self.address_entry.get(),
            )

            self.refresh_list()
            self.clear_form()
            messagebox.showinfo("Success", "Account created successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_account(self):
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        account_data = {
            "name": self.name_entry.get().strip(),
            "role": self.role_var.get(),
            "phone": self.phone_entry.get().strip(),
            "email": self.email_entry.get().strip(),
            "address": self.address_entry.get().strip(),
        }

        try:
            self.account_service.update_account(self.selected_account_id, account_data)
            self.refresh_list()
            messagebox.showinfo("Success", "Account updated successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update account: {str(e)}")

    def delete_account(self):
        if not self.selected_account_id:
            messagebox.showwarning("Select", "Please select an account from the list first.")
            return

        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this partner?"):
            return

        try:
            self.account_service.delete_account(self.selected_account_id)
            self.refresh_list()
            self.clear_form()
            messagebox.showinfo("Success", "Account deleted successfully.")
        except PermissionError as e:
            messagebox.showerror("Blocked", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete account: {str(e)}")

    def open_print_dialog(self):
        """Open print dialog"""
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
        self.geometry("400x450")
        self.resizable(False, False)

        # Center the window
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        # Get account info
        account = self.app.account_service.get_by_id(account_id)
        self.account_name = account.get("name", "Unknown")

        # Title
        ctk.CTkLabel(self, text=f"Record Payment for {self.account_name}", font=("Arial", 16, "bold")).pack(pady=20)

        # Amount input
        ctk.CTkLabel(self, text="Amount ($)").pack(anchor="w", padx=25)
        self.amount_entry = ctk.CTkEntry(self)
        self.amount_entry.pack(fill="x", padx=25, pady=(0, 15))

        # Payment Type
        ctk.CTkLabel(self, text="Payment Type").pack(anchor="w", padx=25)
        self.payment_type_var = ctk.StringVar(value="Payment In")
        self.payment_type_dropdown = ctk.CTkOptionMenu(
            self,
            values=["Payment In", "Payment Out"],
            variable=self.payment_type_var,
        )
        self.payment_type_dropdown.pack(fill="x", padx=25, pady=(0, 15))

        # Payment Method
        ctk.CTkLabel(self, text="Payment Method").pack(anchor="w", padx=25)
        self.payment_method_var = ctk.StringVar(value="Cash")
        self.payment_method_dropdown = ctk.CTkOptionMenu(
            self,
            values=["Cash", "Bank Transfer", "Check", "Credit Card", "Other"],
            variable=self.payment_method_var,
        )
        self.payment_method_dropdown.pack(fill="x", padx=25, pady=(0, 15))

        # Reference Number
        ctk.CTkLabel(self, text="Reference Number (Optional)").pack(anchor="w", padx=25)
        self.ref_entry = ctk.CTkEntry(self)
        self.ref_entry.pack(fill="x", padx=25, pady=(0, 15))

        # Notes
        ctk.CTkLabel(self, text="Notes (Optional)").pack(anchor="w", padx=25)
        self.notes_text = ctk.CTkTextbox(self, height=60)
        self.notes_text.pack(fill="x", padx=25, pady=(0, 15))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=25, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="#7f8c8d",
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Record Payment",
            fg_color="#27ae60",
            command=self.record_payment
        ).pack(side="left", fill="x", expand=True, padx=5)

    def record_payment(self):
        """Record the payment in the database."""
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

            # Record the payment using the service
            user_id = getattr(self.app, 'current_user_id', None)  # Get current user ID from app
            self.payment_service.add_payment(
                account_id=self.account_id,
                amount=amount,
                payment_type=payment_type,
                payment_method=payment_method,
                reference_number=reference_number,
                notes=notes,
                created_by=user_id
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
        self.geometry("700x500")
        self.resizable(True, True)

        # Center the window
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        # Get account info
        account = self.app.account_service.get_by_id(account_id)
        self.account_name = account.get("name", "Unknown")

        # Title
        ctk.CTkLabel(self, text=f"Payment History for {self.account_name}", font=("Arial", 16, "bold")).pack(pady=10)

        # Create treeview for payment history
        cols = ("Date", "Type", "Method", "Amount", "Reference", "Notes", "Created By")
        self.history_tree = ttk.Treeview(self, columns=cols, show="headings", height=15)
        for col in cols:
            self.history_tree.heading(col, text=col)
            if col == "Notes":
                self.history_tree.column(col, width=150)
            elif col in ["Date", "Amount"]:
                self.history_tree.column(col, width=100)
            else:
                self.history_tree.column(col, width=80)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Refresh payment history
        self.refresh_history()

        # Close button
        ctk.CTkButton(
            self,
            text="Close",
            fg_color="#7f8c8d",
            command=self.destroy
        ).pack(pady=10)

    def refresh_history(self):
        """Refresh the payment history display."""
        # Clear existing items
        for i in self.history_tree.get_children():
            self.history_tree.delete(i)

        try:
            # Get payment history from service
            payments = self.payment_service.get_payment_history(self.account_id, limit=100)

            for payment in payments:
                # Format the date to be more readable
                date_str = str(payment.get('date', ''))[:19]  # Remove milliseconds if present
                
                # Format the amount with sign based on type
                amount = payment.get('amount', 0)
                direction = payment.get('direction', '+')
                formatted_amount = f"{direction}${abs(amount):,.2f}"

                self.history_tree.insert(
                    "",
                    "end",
                    values=(
                        date_str,
                        payment.get('payment_type', ''),
                        payment.get('payment_method', ''),
                        formatted_amount,
                        payment.get('reference_number', ''),
                        payment.get('notes', '')[:30] + "..." if len(str(payment.get('notes', ''))) > 30 else payment.get('notes', ''),  # Truncate long notes
                        payment.get('created_by_username', 'System')
                    )
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load payment history: {str(e)}")
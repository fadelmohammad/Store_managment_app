# cashbox_module.py

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime


class CashboxFrame(ctk.CTkFrame):
    def __init__(self, parent, app, db, ledger_service):
        super().__init__(parent)
        self.app = app
        self.db = db
        self.ledger = ledger_service
        self.expected_cash = 0.0

        # --- NAVIGATION BAR ---
        nav_bar = ctk.CTkFrame(self, fg_color="transparent")
        nav_bar.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkButton(nav_bar, text="Back", width=100, fg_color="#444444", hover_color="#555555",
                      command=self.app.go_back).pack(side="left", padx=5)
        ctk.CTkButton(nav_bar, text="Home", width=100, command=self.app.go_home).pack(side="left", padx=5)

        ctk.CTkLabel(nav_bar, text="Cash Management", font=("Arial", 16, "bold")).pack(side="right", padx=20)
        ctk.CTkLabel(self, text="Register & Cashbox", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)

        # --- TOP SUMMARY CARD ---
        self.summary_card = ctk.CTkFrame(self, fg_color="#2f3640", corner_radius=15)
        self.summary_card.pack(fill="x", padx=25, pady=10)

        ctk.CTkLabel(self.summary_card, text="CURRENT REGISTER BALANCE", font=("Arial", 14), text_color="#00a8ff").pack(
            pady=(15, 0))
        self.exp_label = ctk.CTkLabel(self.summary_card, text="€0.00", font=("Arial", 42, "bold"), text_color="#4cd137")
        self.exp_label.pack(pady=(0, 15))

        # --- ACTIONS SECTION (Left: Movement, Right: Reconciliation) ---
        self.action_area = ctk.CTkFrame(self, fg_color="transparent")
        self.action_area.pack(fill="x", padx=20, pady=10)
        self.action_area.grid_columnconfigure((0, 1), weight=1)

        # Left: Manual Cash Movement
        self.entry_frame = self.create_container(self.action_area, 0, 0, "Manual Cash Movement")

        self.desc_entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Description (e.g., Office Supplies, Tea)")
        self.desc_entry.pack(fill="x", padx=15, pady=5)

        self.amt_entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Amount (€)")
        self.amt_entry.pack(fill="x", padx=15, pady=5)

        btn_row = ctk.CTkFrame(self.entry_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=10, padx=10)
        ctk.CTkButton(btn_row, text="Cash IN (+)", fg_color="#27ae60", command=lambda: self.handle_movement("IN")).pack(
            side="left", expand=True, padx=5)
        ctk.CTkButton(btn_row, text="Cash OUT (-)", fg_color="#e67e22",
                      command=lambda: self.handle_movement("OUT")).pack(side="left", expand=True, padx=5)

        # Right: Reconciliation Tool
        self.recon_frame = self.create_container(self.action_area, 0, 1, "Physical Count Check")

        self.actual_entry = ctk.CTkEntry(self.recon_frame, placeholder_text="Actual Cash in Drawer...")
        self.actual_entry.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(self.recon_frame, text="Verify & Reconcile", fg_color="#3498db",
                      command=self.verify_balance).pack(pady=5)
        self.diff_label = ctk.CTkLabel(self.recon_frame, text="Difference: €0.00", font=("Arial", 14, "italic"))
        self.diff_label.pack(pady=5)

        # --- BOTTOM: AUDIT TRAIL ---
        ctk.CTkLabel(self, text="Recent Cash Transactions", font=("Arial", 14, "bold")).pack(pady=(15, 5))

        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        cols = ("Time", "Description", "Debit (In)", "Credit (Out)")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.refresh_data()

    # ==========================================
    # UI HELPERS
    # ==========================================
    def create_container(self, parent, r, c, title):
        frame = ctk.CTkFrame(parent, fg_color="#34495e", corner_radius=10)
        frame.grid(row=r, column=c, sticky="nsew", padx=10, pady=5)
        ctk.CTkLabel(frame, text=title, font=("Arial", 14, "bold"), text_color="#f1c40f").pack(pady=10)
        return frame

    # ==========================================
    # LOGIC & DATA
    # ==========================================
    def refresh_data(self):
        """Calculates expected cash from the Ledger and updates the audit log."""
        try:
            # 1. Fetch Expected Cash Balance from Ledger
            query = """
                SELECT SUM(debit) - SUM(credit) as balance 
                FROM journal_lines l
                JOIN accounts_ledger a ON l.account_id = a.id
                WHERE a.name = 'Cash'
            """
            result = self.db.cursor.execute(query).fetchone()
            self.expected_cash = result["balance"] if result["balance"] else 0.0
            self.exp_label.configure(text=f"€{self.expected_cash:,.2f}")

            # 2. Update Treeview (Audit Log)
            for i in self.tree.get_children():
                self.tree.delete(i)

            log_query = """
                SELECT e.date, e.description, l.debit, l.credit
                FROM journal_entries e
                JOIN journal_lines l ON e.id = l.entry_id
                JOIN accounts_ledger a ON l.account_id = a.id
                WHERE a.name = 'Cash'
                ORDER BY e.id DESC LIMIT 20
            """
            logs = self.db.cursor.execute(log_query).fetchall()
            for log in logs:
                self.tree.insert("", "end", values=(
                    log["date"],
                    log["description"],
                    f"€{log['debit']:.2f}",
                    f"€{log['credit']:.2f}"
                ))
        except Exception as e:
            print(f"Cashbox Refresh Error: {e}")

    def handle_movement(self, direction):
        """Records manual cash injection or expense into the ledger."""
        try:
            # Ensure we have a valid number
            val = self.amt_entry.get().strip()
            if not val:
                return

            amt = float(val)
            desc = self.desc_entry.get().strip() or "Manual Adjustment"

            if direction == "IN":
                # Capital Injection (Owner puts money in)
                lines = [
                    {"account": "Cash", "debit": amt, "credit": 0},
                    {"account": "Owner Equity", "debit": 0, "credit": amt}
                ]
            else:
                # Small Expense (Petrol, Coffee, etc.)
                lines = [
                    {"account": "General Expense", "debit": amt, "credit": 0},
                    {"account": "Cash", "debit": 0, "credit": amt}
                ]

            # --- FIX: Added 'MANUAL' as the reference_id ---
            self.ledger.create_entry(
                description=f"Cashbox: {desc}",
                reference_id="MANUAL",
                lines=lines
            )

            self.db.conn.commit()

            # Reset UI
            self.amt_entry.delete(0, 'end')
            self.desc_entry.delete(0, 'end')
            self.refresh_data()
            messagebox.showinfo("Success", f"Cash {direction} recorded successfully.")

        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid numeric amount.")
        except Exception as e:
            messagebox.showerror("System Error", str(e))

    def verify_balance(self):
        """Compares the ledger's 'Cash' balance with a physical drawer count."""
        try:
            actual = float(self.actual_entry.get())
            diff = actual - self.expected_cash

            if diff == 0:
                self.diff_label.configure(text="Balance Perfect!", text_color="#2ecc71")
                messagebox.showinfo("Reconciliation", "Physical cash matches the system exactly.")
            else:
                status = "OVER" if diff > 0 else "SHORT"
                self.diff_label.configure(text=f"Difference: €{diff:,.2f} ({status})", text_color="#e74c3c")
                messagebox.showwarning("Discrepancy Detected",
                                       f"The drawer is {status} by €{abs(diff):,.2f}.\n\n"
                                       "Please check if a transaction was missed.")
        except ValueError:
            messagebox.showerror("Input Error", "Enter a numeric value for the physical count.")

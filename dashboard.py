# dashboard.py

import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db = app.conn

        # Local state for exchange rate
        self.current_exchange_rate = getattr(self.app, 'exchange_rate', 15000)

        # --- MAIN LAYOUT ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Content

        self.setup_sidebar()
        self.setup_main_area()

    # ==========================================
    # 1. SIDEBAR (NAVIGATION)
    # ==========================================
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1e272e")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(self.sidebar, text="STORE MGT", font=("Arial", 22, "bold"), text_color="#00a8ff").pack(
            pady=(30, 40))

        # Updated Navigation to match the new Unified Accounts structure
        nav_buttons = [
            ("Inventory", "inventory"),
            ("POS (Sales)", "pos"),
            ("Accounts / Partners", "accounts"),  # Now leads to the 2-button screen
            ("Purchase (Stock In)", "purchase"),
            ("Reports & Analytics", "reports"),
            ("Settings / Cashbox", "cashbox"),
        ]

        for text, frame_name in nav_buttons:
            ctk.CTkButton(
                self.sidebar,
                text=text,
                font=("Arial", 14, "bold"),
                height=45,
                anchor="w",
                fg_color="transparent",
                hover_color="#34495e",
                command=lambda name=frame_name: self.app.show_frame(name)
            ).pack(fill="x", padx=15, pady=8)

    # ==========================================
    # 2. MAIN WIDGET AREA
    # ==========================================
    def setup_main_area(self):
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)

        self.main_area.grid_rowconfigure((0, 1), weight=1)
        self.main_area.grid_columnconfigure((0, 1), weight=1)

        # Widget 1: Revenue (Real-time from Ledger)
        self.rev_card = self.create_card(0, 0, "Daily Sales Revenue", "#f1c40f")
        self.rev_label = ctk.CTkLabel(self.rev_card, text="€0.00", font=("Arial", 38, "bold"))
        self.rev_label.pack(expand=True)
        ctk.CTkButton(self.rev_card, text="Refresh", width=100, height=25, command=self.refresh_stats).pack(pady=10)

        # Widget 2: Clock
        self.time_card = self.create_card(0, 1, "Date & Time", "#3498db")
        self.date_lbl = ctk.CTkLabel(self.time_card, text="", font=("Arial", 18))
        self.date_lbl.pack(expand=True, pady=(10, 0))
        self.time_lbl = ctk.CTkLabel(self.time_card, text="", font=("Arial", 32, "bold"))
        self.time_lbl.pack(expand=True, pady=(0, 10))
        self.update_clock()

        # Widget 3: Calculator
        self.calc_card = self.create_card(1, 0, "Quick Calculator", "#2ecc71")
        self.calc_ent = ctk.CTkEntry(self.calc_card, font=("Arial", 20), justify="right")
        self.calc_ent.pack(fill="x", padx=20, pady=10)
        self.calc_ent.bind("<Return>", self.calculate)
        self.calc_res = ctk.CTkLabel(self.calc_card, text="= 0.00", font=("Arial", 24, "bold"))
        self.calc_res.pack(pady=10)

        # Widget 4: Exchange Rate
        self.ex_card = self.create_card(1, 1, "USD Exchange Rate", "#9b59b6")
        self.ex_lbl = ctk.CTkLabel(self.ex_card, text=f"1 USD = {self.current_exchange_rate:,} SYP",
                                   font=("Arial", 18, "bold"))
        self.ex_lbl.pack(expand=True)

        ex_input_f = ctk.CTkFrame(self.ex_card, fg_color="transparent")
        ex_input_f.pack(fill="x", padx=20, pady=10)
        self.ex_ent = ctk.CTkEntry(ex_input_f, placeholder_text="New Rate...", width=120)
        self.ex_ent.pack(side="left", padx=5)
        ctk.CTkButton(ex_input_f, text="Set", width=60, command=self.update_ex).pack(side="right")

    def create_card(self, r, c, title, accent_color):
        card = ctk.CTkFrame(self.main_area, fg_color="#2f3640", corner_radius=15)
        card.grid(row=r, column=c, sticky="nsew", padx=12, pady=12)
        ctk.CTkLabel(card, text=title, font=("Arial", 14, "bold"), text_color=accent_color).pack(pady=12)
        return card

    # ==========================================
    # LOGIC METHODS
    # ==========================================

    def refresh_stats(self):
        """Pulls the latest revenue from the Database using the new Ledger query."""
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            # We use the new get_financial_report method from database.py
            report = self.db.get_financial_report(today, today)
            sales = report.get("sales", 0.0)
            self.rev_label.configure(text=f"€{sales:,.2f}")
        except Exception as e:
            self.rev_label.configure(text="Error", text_color="#e74c3c")

    def update_clock(self):
        now = datetime.now()
        self.date_lbl.configure(text=now.strftime("%A, %d %B %Y"))
        self.time_lbl.configure(text=now.strftime("%I:%M:%S %p"))
        self.after(1000, self.update_clock)

    def calculate(self, event=None):
        try:
            res = eval(self.calc_ent.get())
            self.calc_res.configure(text=f"= {res:,.2f}")
            self.calc_ent.delete(0, 'end')
        except:
            self.calc_res.configure(text="Error", text_color="#e74c3c")

    def update_ex(self):
        try:
            val = float(self.ex_ent.get())
            if val <= 0: raise ValueError
            
            # 1. Update the app state
            self.app.exchange_rate = val
            self.current_exchange_rate = val
            
            # 2. SAVE TO DATABASE (Permanent)
            self.db.set_setting("exchange_rate", val)
            
            # 3. Update UI
            self.ex_lbl.configure(text=f"1 USD = {val:,.2f} SYP")
            self.ex_ent.delete(0, 'end')
            
            messagebox.showinfo("Success", f"Exchange rate saved: {val:,.0f} SYP")
            
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid positive number.")
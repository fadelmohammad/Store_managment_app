# main.py

import customtkinter as ctk
from database.connection import DatabaseConnection
from database.schema import create_tables, seed_ledger_accounts, insert_dummy_data
from database.repositories.product_repo import ProductRepository
from services.inventory_service import InventoryService
from database.core import Database
from services.ledger_service import LedgerService
from services.sales_service import SalesService
from services.purchase_service import PurchaseService

# UI Module Imports
from dashboard import DashboardFrame
from inventory_module import InventoryFrame
from pos_module import POSFrame
from purchase_module import PurchaseFrame
from accounts_module import AccountsFrame
from cashbox_module import CashboxFrame
from reports_module import ReportsFrame


class StoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- DB INIT ---
        self.db_connection = DatabaseConnection()
        self.conn = self.db_connection.get_connection()

        self.product_repo = ProductRepository(self.conn)
        self.inventory_service = InventoryService(self.product_repo)

        create_tables(self.conn)
        seed_ledger_accounts(self.conn)
        insert_dummy_data(self.conn)

        self.db = Database(self.conn)

        # --- THEME & WINDOW CONFIG ---
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("OmniPOS - Advanced Store Management")
        self.geometry("1400x900")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Service Layer (Business Logic)
        self.ledger_service = LedgerService(self.db)
        self.sales_service = SalesService(self.db, self.ledger_service)
        self.purchase_service = PurchaseService(self.db, self.ledger_service)

        # Load the rate from DB, fallback to 15000 if not found
        saved_rate = self.db.get_setting("exchange_rate", "15000")
        self.exchange_rate = float(saved_rate)

        # --- NAVIGATION STATE ---
        self.frames = {}
        self.current_frame = None
        self.current_frame_name = None
        self.history = []

        # --- UI CONTAINER ---
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        # --- FRAME REGISTRY ---
        # We instantiate all frames at startup for snappy navigation
        # Passing relevant services only to where they are needed
        self.init_frames()

        # Launch the app at the Dashboard
        self.show_frame("dashboard")

    def init_frames(self):
        """Initializes and registers all UI modules."""
        self.frames = {
            "dashboard": DashboardFrame(self.container, self),
            "inventory": InventoryFrame(self.container, self, self.db),
            "pos": POSFrame(self.container, self, self.db, self.sales_service),
            "accounts": AccountsFrame(self.container, self, self.db),
            "cashbox": CashboxFrame(self.container, self, self.db, self.ledger_service),
            "purchase": PurchaseFrame(
                self.container, self, self.db, self.purchase_service
            ),
            "reports": ReportsFrame(self.container, self, self.db),
        }

    # ==========================================
    # NAVIGATION LOGIC
    # ==========================================
    def show_frame(self, name, save_history=True):
        """Switches the visible frame and refreshes its data."""
        if self.current_frame_name == name:
            return  # Already here, do nothing

        # Update History Stack
        if self.current_frame_name and save_history:
            self.history.append(self.current_frame_name)

        # Hide current frame
        if self.current_frame:
            self.current_frame.pack_forget()

        # Show new frame
        frame = self.frames.get(name)
        if frame:
            frame.pack(fill="both", expand=True)
            self.current_frame = frame
            self.current_frame_name = name

            # Auto-Refresh: Important for ensuring Sales/Purchases
            # show up in Reports or Cashbox immediately.
            if hasattr(frame, "refresh_data"):
                frame.refresh_data()
        else:
            print(f"Error: Frame '{name}' not found.")

    def go_back(self):
        """Navigates to the previous screen in the stack."""
        if self.history:
            prev_frame = self.history.pop()
            self.show_frame(prev_frame, save_history=False)

    def go_home(self):
        """Clears history and returns to the Dashboard."""
        self.history = []
        self.show_frame("dashboard", save_history=False)

    # ==========================================
    # CLEANUP
    # ==========================================
    def on_close(self):
        """Ensures the database connection is closed gracefully."""
        try:
            self.db.close()
        except Exception as e:
            print(f"Cleanup Error: {e}")
        self.destroy()


if __name__ == "__main__":
    app = StoreApp()
    app.mainloop()

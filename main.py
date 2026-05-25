# main.py

import os
import customtkinter as ctk
import tkinter as tk
import logging
import tkinter.messagebox as messagebox

from logger import setup_logging
setup_logging()
from database.connection import DatabaseConnection
from database.schema import create_tables, seed_ledger_accounts, insert_dummy_data, seed_permissions, create_admin_user
from database.repositories.product_repo import ProductRepository
from database.repositories.stock_movement_repo import StockMovementRepository
from database.repositories.category_repo import CategoryRepository
from database.repositories.settings_repo import SettingRepository
from database.repositories.account_repo import AccountRepository
from database.repositories.report_repo import ReportRepository
from database.repositories.purchase_repo import PurchaseRepository
from services.inventory_service import InventoryService
from services.category_service import CategoryService
from services.report_service import ReportingService
from services.ledger_service import LedgerService
from services.sales_service import SalesService
from services.purchase_service import PurchaseService
from services.accounts_service import AccountService
from services.user_service import UserService
from services.login_service import LoginService
from services.invoices_service import InvoiceService
from services.print_service import PrintService  # Import the print service
from database.backup_service import BackupService
from ui.sidebar_builder import build_sidebar

from ui.dashboard import DashboardFrame
from ui.inventory_module import InventoryFrame
from ui.pos_module import POSFrame
from ui.purchase_module import PurchaseFrame
from ui.accounts_module import AccountsFrame
from ui.cashbox_module import CashboxFrame
from ui.reports_module import ReportsFrame
from ui.login_module import LoginFrame
from ui.user_profile import UserProfileFrame
from ui.user_management_module import UserManagementFrame
from services.ui.ui_service import UIService
from services.ui.frame_router import FrameRouter


class StoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db_connection = DatabaseConnection()
        self.conn = self.db_connection.get_connection()

        self.initialize_database()
        
        self.current_user = None
        self.user_service = UserService(self.conn)
        self.login_service = LoginService(self.conn)

        self.stock_repo = StockMovementRepository(self.conn)
        self.product_repo = ProductRepository(self.conn)
        self.category_repo = CategoryRepository(self.conn)
        self.report_repo = ReportRepository(self.conn)
        self.purchase_repo = PurchaseRepository(self.conn)
        self.category_service = CategoryService(self.category_repo) 
        self.inventory_service = InventoryService(self.product_repo, self.stock_repo, self.category_service, self.category_repo)

        self.setting_repo = SettingRepository(self.conn)
        self.account_repo = AccountRepository(self.conn)
        self.account_service = AccountService(self.account_repo)

        self.invoice_repo = None  # not used; invoice reads go via InvoiceService
        self.invoice_service = InvoiceService(self.conn)
        self.report_service = ReportingService(
            self.report_repo,
            self.product_repo,
            self.stock_repo,
            self.invoice_service,
        )

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("ui/themes/orange.json")

        self.title("OmniPOS - Advanced Store Management")
        self.geometry("1400x900")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Global UI helpers (shared UI actions across frames)
        self.ui_service = UIService(self)

        # Route/state manager (extracts frame routing logic out of StoreApp)
        self.frame_router = FrameRouter(self)

        self.ledger_service = LedgerService(self.conn)
        self.sales_service = SalesService(self.conn, self.ledger_service)
        self.purchase_service = PurchaseService(self.purchase_repo, self.product_repo, self.stock_repo, self.inventory_service, self.ledger_service, self.account_repo)

        # Initialize the print service
        self.print_service = PrintService(self)

        self.backup_service = BackupService()
        try:
            self.backup_service.auto_backup()
        except Exception as e:
            logging.warning(f"Auto-backup failed: {e}")

        saved_rate = self.setting_repo.get("exchange_rate", "15000")
        self.exchange_rate = float(saved_rate)

        self.sidebar_frame = None
        self.main_content_frame = None
        self.frames = {}
        self.current_frame = None
        self.current_frame_name = None
        self.history = []

        self.show_login_screen()

    def initialize_database(self):
        try:
            create_tables(self.conn)
            seed_ledger_accounts(self.conn)
            seed_permissions(self.conn)
            create_admin_user(self.conn)
            insert_dummy_data(self.conn)
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            messagebox.showerror("Error", f"Failed to initialize database:\n{str(e)}")

    def show_login_screen(self):
        self.login_frame = LoginFrame(self, self, self.login_service, self.on_login_success)
        self.login_frame.pack(fill="both", expand=True)

    def on_login_success(self):
        self.login_frame.destroy()
        self.create_main_ui()
        self.show_frame("dashboard")

    def create_main_ui(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_content_frame.pack(side="right", fill="both", expand=True)

        self.create_sidebar()
        self.init_frames()


    def create_sidebar(self):
        # Extracted from the previous inline implementation to reduce the god-object size.
        # Behavior is unchanged: it builds the same sidebar widgets and uses existing callbacks.
        build_sidebar(
            app=self,
            container=self.sidebar_frame,
            user=self.current_user,
            on_show_profile=self.show_profile,
            on_logout=self.logout,
            on_show_frame=self.show_frame,
            create_button=self.create_sidebar_button,
        )
    

    def show_profile(self):
        self.show_frame("profile")
    

    def update_user_info(self, updated_user):
        logging.info("Updating user info")
        self.current_user = updated_user

        if hasattr(self, 'sidebar_frame') and self.sidebar_frame:
            for widget in self.sidebar_frame.winfo_children():
                widget.destroy()

        self.create_sidebar()

        current_frame_name = self.current_frame_name
        if current_frame_name in self.frames:
            frame = self.frames[current_frame_name]
            if hasattr(frame, "refresh_data"):
                frame.refresh_data()

        logging.info("User info updated successfully")


    def create_sidebar_button(self, text, frame_name):
        button = ctk.CTkButton(
            self.sidebar_frame,
            text=text,
            command=lambda: self.show_frame(frame_name),
            height=45,
            corner_radius=0,
            fg_color="transparent",
            hover_color=("#2a2a2a", "#3a3a3a"),
            anchor="w",
            font=ctk.CTkFont(size=14)
        )
        button.pack(fill="x", padx=10, pady=5)

    def init_frames(self):
        self.frame_router.init_frames()

        # Sync legacy attributes for compatibility
        self.frames = self.frame_router.frames
        self.current_frame = self.frame_router.current_frame
        self.current_frame_name = self.frame_router.current_frame_name
        self.history = self.frame_router.history

    def show_frame(self, name, save_history=True):
        self.frame_router.show_frame(name, save_history=save_history)

        # Sync legacy attributes for compatibility
        self.frames = self.frame_router.frames
        self.current_frame = self.frame_router.current_frame
        self.current_frame_name = self.frame_router.current_frame_name
        self.history = self.frame_router.history

    def go_back(self):
        self.frame_router.go_back()

        # Sync legacy attributes for compatibility
        self.frames = self.frame_router.frames
        self.current_frame = self.frame_router.current_frame
        self.current_frame_name = self.frame_router.current_frame_name
        self.history = self.frame_router.history

    def go_home(self):
        self.frame_router.go_home()

        # Sync legacy attributes for compatibility
        self.frames = self.frame_router.frames
        self.current_frame = self.frame_router.current_frame
        self.current_frame_name = self.frame_router.current_frame_name
        self.history = self.frame_router.history

    def logout(self):
        if messagebox.askyesno("Confirm", "Do you want to logout?"):
            if self.current_user:
                self.user_service.log_user_action(self.current_user['id'], "logout", "User logout")

            if os.path.exists("session.json"):
                os.remove("session.json")

            self.current_user = None
            self.frames = {}
            self.history = []

            if self.sidebar_frame:
                self.sidebar_frame.destroy()
            if self.main_content_frame:
                self.main_content_frame.destroy()

            self.show_login_screen()

    def on_close(self):
        try:
            if self.current_user:
                self.user_service.log_user_action(self.current_user['id'], "app_close", "Application closed")
            self.db_connection.close()
        except Exception as e:
            logging.error(f"Cleanup Error: {e}")
        self.destroy()


if __name__ == "__main__":
    app = StoreApp()
    app.mainloop()
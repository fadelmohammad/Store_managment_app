# main.py

import customtkinter as ctk
import tkinter as tk
import logging
import tkinter.messagebox as messagebox

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

from dashboard import DashboardFrame
from inventory_module import InventoryFrame
from pos_module import POSFrame
from purchase_module import PurchaseFrame
from accounts_module import AccountsFrame
from cashbox_module import CashboxFrame
from reports_module import ReportsFrame
from login_module import LoginFrame
from user_profile import UserProfileFrame
from user_management_module import UserManagementFrame


class StoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db_connection = DatabaseConnection()
        self.conn = self.db_connection.get_connection()

        self.initialize_database()
        
        self.current_user = None
        self.user_service = UserService(self.conn)

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
        self.report_service = ReportingService(self.report_repo, self.product_repo, self.stock_repo)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("OmniPOS - Advanced Store Management")
        self.geometry("1400x900")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.ledger_service = LedgerService(self.conn)
        self.sales_service = SalesService(self.conn, self.ledger_service)
        self.purchase_service = PurchaseService(self.purchase_repo, self.product_repo, self.stock_repo, self.inventory_service, self.ledger_service, self.account_repo)

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
        self.login_frame = LoginFrame(self, self, self.on_login_success)
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
        logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="OmniPOS", 
            font=ctk.CTkFont(size=24, weight="bold"),
            pady=20
        )
        logo_label.pack()

        user_info = ctk.CTkLabel(
            self.sidebar_frame,
            text=f"{self.current_user.get('full_name', self.current_user.get('username'))}\n{self.current_user.get('role')}",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        user_info.pack(pady=(0, 20))
        
        profile_btn = ctk.CTkButton(
            self.sidebar_frame,
            text=" My Profile",
            command=self.show_profile,
            fg_color="#3498db",
            hover_color="#2980b9",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        profile_btn.pack(fill="x", padx=20, pady=(0, 15))

        permissions = self.current_user.get('permissions', {})

        self.create_sidebar_button("Dashboard", "dashboard")

        if permissions.get('can_view_products', True) or self.current_user.get('role') == 'admin':
            self.create_sidebar_button("Inventory", "inventory")

        if permissions.get('can_create_invoices', True) or self.current_user.get('role') == 'admin':
            self.create_sidebar_button("POS", "pos")

        if permissions.get('can_view_invoices', True) or self.current_user.get('role') == 'admin':
            self.create_sidebar_button("Purchases", "purchase")

        if permissions.get('can_view_accounts', True) or self.current_user.get('role') == 'admin':
            self.create_sidebar_button("Accounts", "accounts")

        if permissions.get('can_view_reports', True) or self.current_user.get('role') == 'admin':
            self.create_sidebar_button("Cashbox", "cashbox")
            self.create_sidebar_button("Reports", "reports")

        if permissions.get('can_manage_users', False) or self.current_user.get('role') == 'admin':
            self.create_sidebar_button("Manage Users", "manage_users")

        ctk.CTkButton(
            self.sidebar_frame,
            text="Logout",
            command=self.logout,
            fg_color="red",
            hover_color="darkred",
            height=40
        ).pack(side="bottom", pady=20, padx=20, fill="x")
    

    def show_profile(self):
        self.show_frame("profile")
    

    def update_user_info(self, updated_user):
        print("Updating user info in main app...")
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
        
        print("User info updated successfully")


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
        permissions = self.current_user.get('permissions', {})
        
        self.frames["dashboard"] = DashboardFrame(self.main_content_frame, self)
        self.frames["profile"] = UserProfileFrame(self.main_content_frame, self, self.user_service, self.current_user, self.update_user_info)
        
        if permissions.get('can_view_products', True) or self.current_user.get('role') == 'admin':
            self.frames["inventory"] = InventoryFrame(self.main_content_frame, self)
        
        if permissions.get('can_create_invoices', True) or self.current_user.get('role') == 'admin':
            self.frames["pos"] = POSFrame(self.main_content_frame, self, self.sales_service, self.account_service, self.inventory_service)
        
        if permissions.get('can_view_invoices', True) or self.current_user.get('role') == 'admin':
            self.frames["purchase"] = PurchaseFrame(
                self.main_content_frame,
                self,
                self.conn,
                self.purchase_service,
                self.account_service,
                self.inventory_service,
            )
        
        if permissions.get('can_view_accounts', True) or self.current_user.get('role') == 'admin':
            self.frames["accounts"] = AccountsFrame(self.main_content_frame, self, self.account_service)
        
        if permissions.get('can_view_reports', True) or self.current_user.get('role') == 'admin':
            self.frames["cashbox"] = CashboxFrame(self.main_content_frame, self, self.ledger_service)
            self.frames["reports"] = ReportsFrame(self.main_content_frame, self, self.conn)
        
        if permissions.get('can_manage_users', False) or self.current_user.get('role') == 'admin':
            self.frames["manage_users"] = UserManagementFrame(self.main_content_frame, self, self.user_service, self.current_user)

    def show_frame(self, name, save_history=True):
        if self.current_frame_name == name:
            return

        if self.current_frame and save_history:
            self.history.append(self.current_frame_name)

        if self.current_frame:
            self.current_frame.pack_forget()

        frame = self.frames.get(name)
        if frame:
            frame.pack(fill="both", expand=True)
            self.current_frame = frame
            self.current_frame_name = name

            if hasattr(frame, "refresh_data"):
                frame.refresh_data()
        else:
            logging.error(f"Error: Frame '{name}' not found.")
            if name != "manage_users":
                self.frames["dashboard"].pack(fill="both", expand=True)
                self.current_frame = self.frames["dashboard"]
                self.current_frame_name = "dashboard"

    def go_back(self):
        if self.history:
            prev_frame = self.history.pop()
            self.show_frame(prev_frame, save_history=False)

    def go_home(self):
        self.history = []
        self.show_frame("dashboard", save_history=False)

    def logout(self):
        if messagebox.askyesno("Confirm", "Do you want to logout?"):
            if self.current_user:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("""
                        INSERT INTO user_logs (user_id, action, details, ip_address)
                        VALUES (?, ?, ?, ?)
                    """, (self.current_user['id'], "logout", "User logout", "localhost"))
                    self.conn.commit()
                except:
                    pass
            
            import os
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
                cursor = self.conn.cursor()
                cursor.execute("""
                    INSERT INTO user_logs (user_id, action, details, ip_address)
                    VALUES (?, ?, ?, ?)
                """, (self.current_user['id'], "app_close", "Application closed", "localhost"))
                self.conn.commit()
            
            self.db_connection.close()
        except Exception as e:
            logging.error(f"Cleanup Error: {e}")
        self.destroy()


if __name__ == "__main__":
    app = StoreApp()
    app.mainloop()
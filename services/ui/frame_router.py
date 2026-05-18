from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ui.dashboard import DashboardFrame
from ui.inventory_module import InventoryFrame
from ui.pos_module import POSFrame
from ui.purchase_module import PurchaseFrame
from ui.accounts_module import AccountsFrame
from ui.cashbox_module import CashboxFrame
from ui.reports_module import ReportsFrame
from ui.user_profile import UserProfileFrame
from ui.user_management_module import UserManagementFrame
from ui.backup_module import BackupFrame


class FrameRouter:
    """
    Encapsulates routing/state for StoreApp frames:
    - frames registry
    - current frame + history navigation
    - show_frame + go_back/go_home
    - frame initialization (permission-gated)
    """

    def __init__(self, app: Any):
        self.app = app
        self.frames: Dict[str, Any] = {}
        self.current_frame: Optional[Any] = None
        self.current_frame_name: Optional[str] = None
        self.history: List[str] = []

    def init_frames(self) -> None:
        permissions = self.app.current_user.get("permissions", {}) if self.app.current_user else {}
        role = self.app.current_user.get("role") if self.app.current_user else None

        # Note: these constructors/args must match the ones used in the original main.py.
        self.frames["dashboard"] = DashboardFrame(self.app.main_content_frame, self.app)
        self.frames["profile"] = UserProfileFrame(
            self.app.main_content_frame,
            self.app,
            self.app.user_service,
            self.app.current_user,
            self.app.update_user_info,
        )

        if permissions.get("can_view_products", True) or role == "admin":
            self.frames["inventory"] = InventoryFrame(self.app.main_content_frame, self.app)

        if permissions.get("can_create_invoices", True) or role == "admin":
            self.frames["pos"] = POSFrame(
                self.app.main_content_frame,
                self.app,
                self.app.sales_service,
                self.app.account_service,
                self.app.inventory_service,
            )

        if permissions.get("can_view_invoices", True) or role == "admin":
            self.frames["purchase"] = PurchaseFrame(
                self.app.main_content_frame,
                self.app,
                self.app.conn,
                self.app.purchase_service,
                self.app.account_service,
                self.app.inventory_service,
            )

        if permissions.get("can_view_accounts", True) or role == "admin":
            self.frames["accounts"] = AccountsFrame(
                self.app.main_content_frame,
                self.app,
                self.app.account_service,
            )

        if permissions.get("can_view_reports", True) or role == "admin":
            self.frames["cashbox"] = CashboxFrame(
                self.app.main_content_frame,
                self.app,
                self.app.ledger_service,
            )
            self.frames["reports"] = ReportsFrame(
                self.app.main_content_frame,
                self.app,
                self.app.conn,
            )

        if permissions.get("can_manage_users", False) or role == "admin":
            self.frames["manage_users"] = UserManagementFrame(
                self.app.main_content_frame,
                self.app,
                self.app.user_service,
                self.app.current_user,
            )

        if permissions.get("can_manage_settings", False) or role == "admin":
            self.frames["backup"] = BackupFrame(
                self.app.main_content_frame,
                self.app,
                self.app.backup_service,
            )

    def show_frame(self, name: str, save_history: bool = True) -> None:
        if self.current_frame_name == name:
            return

        if self.current_frame and save_history and self.current_frame_name is not None:
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
            return

        logging.error(f"Error: Frame '{name}' not found.")
        if name != "manage_users" and "dashboard" in self.frames:
            self.frames["dashboard"].pack(fill="both", expand=True)
            self.current_frame = self.frames["dashboard"]
            self.current_frame_name = "dashboard"

    def go_back(self) -> None:
        if self.history:
            prev_frame = self.history.pop()
            self.show_frame(prev_frame, save_history=False)

    def go_home(self) -> None:
        self.history = []
        self.show_frame("dashboard", save_history=False)

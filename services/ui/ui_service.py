import customtkinter as ctk
import tkinter.messagebox as messagebox
from typing import Callable, Optional


class UIService:
    """
    Global UI helpers shared by multiple frames.

    Keep this module dependency-light:
    - no DB access
    - no business logic
    just reusable widgets + standard message/confirm dialogs
    """

    def __init__(self, app):
        self.app = app

    # ---------- Navigation helpers ----------
    def create_back_home_nav(
        self,
        parent,
        *,
        back_text: str = "Back",
        home_text: str = "Home",
        back_command: Optional[Callable] = None,
        home_command: Optional[Callable] = None,
        left_pad: int = 5,
    ):
        """
        Creates the common "Back" + "Home" button bar.
        Returns the nav bar frame (so caller can pack a title on the right).
        """
        nav_bar = ctk.CTkFrame(parent, fg_color="transparent")
        nav_bar.pack(side="top", fill="x", padx=10, pady=5)

        back_command = back_command or getattr(self.app, "go_back", None)
        home_command = home_command or getattr(self.app, "go_home", None)
        if back_command is None or home_command is None:
            raise RuntimeError("UIService: app.go_back/app.go_home not found")

        ctk.CTkButton(
            nav_bar,
            text=back_text,
            width=100,
            fg_color="#444444",
            hover_color="#555555",
            command=back_command,
            height=28,
            corner_radius=0,
        ).pack(side="left", padx=left_pad)

        ctk.CTkButton(
            nav_bar,
            text=home_text,
            width=100,
            command=home_command,
            height=28,
            corner_radius=0,
        ).pack(side="left", padx=left_pad)

        return nav_bar

    # ---------- Message helpers ----------
    def info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def warn(self, title: str, message: str) -> None:
        messagebox.showwarning(title, message)

    def error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def confirm(self, title: str, message: str) -> bool:
        return bool(messagebox.askyesno(title, message))

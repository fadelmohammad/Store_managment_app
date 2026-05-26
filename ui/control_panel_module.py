import customtkinter as ctk


class ControlPanelFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_nav()
        self._build_body()

    def _build_nav(self):
        nav = self.app.ui_service.create_back_home_nav(
            self,
            back_command=self.app.go_back,
            home_command=self.app.go_home,
        )
        ctk.CTkLabel(nav, text="Control Panel", font=ctk.CTkFont(size=15, weight="bold")).pack(
            side="right", padx=20
        )

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        permissions = (self.app.current_user or {}).get("permissions", {}) or {}
        role = (self.app.current_user or {}).get("role")

        # Restriction: keep reports & cashbox OUT of this panel.
        cards = []

        # Always include dashboard-related management if allowed.
        if permissions.get("can_manage_users", False) or role == "admin":
            cards.append(
                ("Manage Users", "manage_users", "#3498db", "#2980b9")
            )

        if permissions.get("can_manage_settings", False) or role == "admin":
            cards.append(
                ("Backup & Restore", "backup", "#e67e22", "#d35400")
            )

        # Fallback: if nothing is allowed, show a single disabled card.
        if not cards:
            card = ctk.CTkFrame(body, fg_color="#2f3640", corner_radius=15, height=160)
            card.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
            ctk.CTkLabel(
                card,
                text="No control-panel permissions",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#e74c3c",
            ).pack(pady=(55, 0))
            ctk.CTkLabel(
                card,
                text="Ask an admin to grant you control-panel access.",
                font=ctk.CTkFont(size=12),
                text_color="gray75",
            ).pack(pady=(10, 0))
            return

        # Render cards in a 2-column grid.
        for i, (title, frame_name, fg, hover) in enumerate(cards):
            r = i // 2
            c = i % 2

            card = ctk.CTkFrame(body, fg_color="#2f3640", corner_radius=15, height=160)
            card.grid(row=r, column=c, sticky="nsew", padx=10, pady=10)
            card.grid_propagate(False)

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=fg,
            ).pack(pady=(30, 8))

            ctk.CTkButton(
                card,
                text="Open",
                height=38,
                corner_radius=10,
                fg_color=fg,
                hover_color=hover,
                command=lambda fn=frame_name: self.app.show_frame(fn),
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(fill="x", padx=22, pady=(0, 22))


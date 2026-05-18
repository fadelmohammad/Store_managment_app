import customtkinter as ctk


def build_sidebar(app, container, user, *, on_show_profile, on_logout, on_show_frame, create_button):
    """
    Build the left sidebar UI.

    This is extracted from main.py to reduce the main StoreApp god object.

    Parameters
    - app: main StoreApp instance (used for theme/customtkinter widgets)
    - container: CTkFrame that will hold sidebar widgets
    - user: current_user dict
    - on_show_profile: callback for "My Profile"
    - on_logout: callback for Logout button
    - on_show_frame: callback to switch frames (eg app.show_frame)
    - create_button: callable(text, frame_name) which uses app.create_sidebar_button
    """
    # Logo
    logo_label = ctk.CTkLabel(
        container,
        text="OmniPOS",
        font=ctk.CTkFont(size=24, weight="bold"),
        pady=20,
    )
    logo_label.pack()

    user_info = ctk.CTkLabel(
        container,
        text=f"{user.get('full_name', user.get('username'))}\n{user.get('role')}",
        font=ctk.CTkFont(size=12),
        justify="center",
    )
    user_info.pack(pady=(0, 20))

    profile_btn = ctk.CTkButton(
        container,
        text=" My Profile",
        command=on_show_profile,
        fg_color="#3498db",
        hover_color="#2980b9",
        height=40,
        font=ctk.CTkFont(size=14, weight="bold"),
    )
    profile_btn.pack(fill="x", padx=20, pady=(0, 15))

    permissions = user.get("permissions", {}) or {}

    # Sidebar links
    create_button("Dashboard", "dashboard")

    if permissions.get("can_view_products", True) or user.get("role") == "admin":
        create_button("Inventory", "inventory")

    if permissions.get("can_create_invoices", True) or user.get("role") == "admin":
        create_button("POS", "pos")

    if permissions.get("can_view_invoices", True) or user.get("role") == "admin":
        create_button("Purchases", "purchase")

    if permissions.get("can_view_accounts", True) or user.get("role") == "admin":
        create_button("Accounts", "accounts")

    if permissions.get("can_view_reports", True) or user.get("role") == "admin":
        create_button("Cashbox", "cashbox")
        create_button("Reports", "reports")

    if permissions.get("can_manage_users", False) or user.get("role") == "admin":
        create_button("Manage Users", "manage_users")

    if permissions.get("can_manage_settings", False) or user.get("role") == "admin":
        create_button("Backup & Restore", "backup")

    # Logout at bottom
    ctk.CTkButton(
        container,
        text="Logout",
        command=on_logout,
        fg_color="red",
        hover_color="darkred",
        height=40,
    ).pack(side="bottom", pady=20, padx=20, fill="x")

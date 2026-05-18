# File: ui/backup_module.py

import os
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

_GREEN  = ("#27ae60", "#2ecc71")
_RED    = ("#c0392b", "#e74c3c")
_ORANGE = ("#e67e22", "#f39c12")
_DARK   = ("#2c2c2c", "#1a1a1a")
_MUTED  = ("gray55", "gray45")


class BackupFrame(ctk.CTkFrame):
    def __init__(self, parent, app, backup_service):
        super().__init__(parent)
        self.app            = app
        self.backup_service = backup_service

        self._build_nav()
        self._build_body()
        self.refresh_data()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_nav(self):
        nav = self.app.ui_service.create_back_home_nav(
            self,
            back_command=self.app.go_back,
            home_command=self.app.go_home,
        )
        ctk.CTkLabel(nav, text="Backup & Restore", font=ctk.CTkFont(size=15, weight="bold")).pack(side="right", padx=20)

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_actions_panel(body)
        self._build_list_panel(body)

    # ── left: actions ─────────────────────────────────────────────────────────

    def _build_actions_panel(self, parent):
        panel = ctk.CTkFrame(parent, width=280)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_propagate(False)

        ctk.CTkLabel(panel, text="Create Backup", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(16, 4), padx=12, anchor="w")

        ctk.CTkLabel(panel, text="Label (optional)", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(6, 0))
        self.label_entry = ctk.CTkEntry(panel, placeholder_text="e.g. before_update", height=32)
        self.label_entry.pack(fill="x", padx=10, pady=(2, 0))

        ctk.CTkButton(
            panel, text="💾  Create Backup Now",
            height=42, corner_radius=8,
            fg_color=_GREEN[0], hover_color=_GREEN[1],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._create_backup,
        ).pack(fill="x", padx=10, pady=14)

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=4)

        ctk.CTkLabel(panel, text="Restore", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(12, 4), padx=12, anchor="w")
        ctk.CTkLabel(
            panel,
            text="Select a backup from the list\nthen click Restore, or import\nan external .db file.",
            font=ctk.CTkFont(size=11),
            text_color=_MUTED[0],
            justify="left",
        ).pack(anchor="w", padx=12)

        ctk.CTkButton(
            panel, text="⟳  Restore Selected",
            height=38, corner_radius=8,
            fg_color=_ORANGE[0], hover_color=_ORANGE[1],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._restore_selected,
        ).pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkButton(
            panel, text="📂  Import External .db",
            height=38, corner_radius=8,
            fg_color="transparent", border_width=1,
            font=ctk.CTkFont(size=12),
            command=self._import_external,
        ).pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkFrame(panel, height=1, fg_color=("gray70", "gray30")).pack(fill="x", padx=10, pady=8)

        ctk.CTkButton(
            panel, text="🗑  Delete Selected",
            height=34, corner_radius=8,
            fg_color=_RED[0], hover_color=_RED[1],
            font=ctk.CTkFont(size=12),
            command=self._delete_selected,
        ).pack(fill="x", padx=10, pady=(0, 12))

        # info card
        info_card = ctk.CTkFrame(panel, fg_color=_DARK[0], corner_radius=8)
        info_card.pack(fill="x", padx=10, pady=(4, 12))
        ctk.CTkLabel(
            info_card,
            text="ℹ  Backups are stored in\nthe /backups folder.\nA daily auto-backup runs\non each app startup.",
            font=ctk.CTkFont(size=10),
            text_color=_MUTED[0],
            justify="left",
        ).pack(padx=10, pady=10, anchor="w")

    # ── right: backup list ────────────────────────────────────────────────────

    def _build_list_panel(self, parent):
        panel = ctk.CTkFrame(parent)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.rowconfigure(1, weight=1)
        panel.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        ctk.CTkLabel(hdr, text="Available Backups", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(
            hdr, text="↻  Refresh", height=28, width=90,
            fg_color="transparent", border_width=1,
            command=self.refresh_data,
        ).pack(side="right")

        tree_frame = ctk.CTkFrame(panel, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "BAK.Treeview",
            background="#1e1e1e", foreground="white",
            fieldbackground="#1e1e1e", rowheight=30,
            font=("Roboto", 11),
        )
        style.configure("BAK.Treeview.Heading", background="#2c2c2c", foreground="#aaaaaa", font=("Roboto", 10, "bold"))
        style.map("BAK.Treeview", background=[("selected", "#2d6a4f")])

        cols = ("File Name", "Created At", "Schema", "Size (KB)")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="BAK.Treeview")
        widths = {"File Name": 300, "Created At": 160, "Schema": 65, "Size (KB)": 90}
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths[c], anchor="w" if c == "File Name" else "center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("auto",    foreground="#aaaaaa")
        self.tree.tag_configure("restore", foreground=_ORANGE[1])
        self.tree.tag_configure("manual",  foreground="white")

    # ── actions ───────────────────────────────────────────────────────────────

    def _create_backup(self):
        label = self.label_entry.get().strip().replace(" ", "_")
        try:
            path = self.backup_service.create_backup(label=label)
            self.label_entry.delete(0, "end")
            self.refresh_data()
            messagebox.showinfo("Backup Created", f"Backup saved:\n{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def _restore_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a backup from the list first.")
            return
        backup_path = self.tree.item(sel[0])["values"][0]
        # resolve full path from name
        backup_path = self._resolve_path(backup_path)
        if not backup_path:
            return

        b_info = next((b for b in self.backup_service.list_backups() if b["path"] == backup_path), {})
        schema_note = f"  Schema: {b_info.get('schema_version', '?')}\n" if b_info else ""

        if not messagebox.askyesno(
            "Confirm Restore",
            f"Restore from:\n{os.path.basename(backup_path)}\n{schema_note}"
            "The app will need to restart after restore.\n"
            "A safety backup of the current data will be created first.\n\n"
            "Continue?",
        ):
            return
        self._do_restore(backup_path)

    def _import_external(self):
        path = filedialog.askopenfilename(
            title="Select backup .db file",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
        )
        if not path:
            return
        if not messagebox.askyesno(
            "Confirm Restore",
            f"Restore from external file:\n{path}\n\n"
            "A safety backup of the current data will be created first.\n\n"
            "Continue?",
        ):
            return
        self._do_restore(path)

    def _do_restore(self, backup_path: str):
        try:
            self.backup_service.restore_backup(backup_path)
            messagebox.showinfo(
                "Restore Complete",
                "Data restored successfully.\n\nPlease restart the application to load the restored data.",
            )
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a backup to delete.")
            return
        name = self.tree.item(sel[0])["values"][0]
        backup_path = self._resolve_path(name)
        if not backup_path:
            return
        if not messagebox.askyesno("Confirm Delete", f"Permanently delete:\n{name}?"):
            return
        try:
            self.backup_service.delete_backup(backup_path)
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Delete Failed", str(e))

    def _resolve_path(self, name: str) -> str | None:
        for b in self.backup_service.list_backups():
            if b["name"] == name:
                return b["path"]
        messagebox.showerror("Not Found", f"Could not locate backup file: {name}")
        return None

    # ── data ──────────────────────────────────────────────────────────────────

    def refresh_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for b in self.backup_service.list_backups():
            if "pre_restore" in b["name"]:
                tag = "restore"
            elif "auto" in b["name"]:
                tag = "auto"
            else:
                tag = "manual"
            self.tree.insert("", "end", tags=(tag,), values=(b["name"], b["created_at"], b["schema_version"], b["size_kb"]))

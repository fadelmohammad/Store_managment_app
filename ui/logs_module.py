# logs_module.py

import customtkinter as ctk
from tkinter import ttk

class LogsModuleWindow(ctk.CTkToplevel):
    def __init__(self, parent, conn):
        super().__init__(parent)
        self.conn = conn
        
        self.title("User Activity Logs")
        self.geometry("1000x600")
        
        self.create_widgets()
        self.load_logs()
    
    def create_widgets(self):
        title = ctk.CTkLabel(self, text="User Activity Logs", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20)
        
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Filter by user:").pack(side="left", padx=5)
        
        self.user_filter = ctk.CTkComboBox(filter_frame, values=self.get_users(), width=200)
        self.user_filter.pack(side="left", padx=5)
        self.user_filter.set("All Users")
        
        filter_btn = ctk.CTkButton(filter_frame, text="Apply Filter", command=self.load_logs)
        filter_btn.pack(side="left", padx=10)
        
        refresh_btn = ctk.CTkButton(filter_frame, text="Refresh", command=self.load_logs, fg_color="green")
        refresh_btn.pack(side="left", padx=5)
        
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.create_treeview()
    
    def get_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users ORDER BY username")
        users = ["All Users"] + [row[0] for row in cursor.fetchall()]
        return users
    
    def create_treeview(self):
        columns = ('ID', 'Username', 'Action', 'Details', 'IP Address', 'Timestamp')
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings', height=20)
        
        self.tree.heading('ID', text='ID')
        self.tree.heading('Username', text='Username')
        self.tree.heading('Action', text='Action')
        self.tree.heading('Details', text='Details')
        self.tree.heading('IP Address', text='IP Address')
        self.tree.heading('Timestamp', text='Timestamp')
        
        self.tree.column('ID', width=50)
        self.tree.column('Username', width=150)
        self.tree.column('Action', width=150)
        self.tree.column('Details', width=300)
        self.tree.column('IP Address', width=120)
        self.tree.column('Timestamp', width=180)
        
        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def load_logs(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        selected_user = self.user_filter.get()
        cursor = self.conn.cursor()
        
        if selected_user == "All Users":
            cursor.execute("""
                SELECT l.id, u.username, l.action, l.details, l.ip_address, l.timestamp
                FROM user_logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.timestamp DESC
                LIMIT 500
            """)
        else:
            cursor.execute("""
                SELECT l.id, u.username, l.action, l.details, l.ip_address, l.timestamp
                FROM user_logs l
                LEFT JOIN users u ON l.user_id = u.id
                WHERE u.username = ?
                ORDER BY l.timestamp DESC
                LIMIT 500
            """, (selected_user,))
        
        for row in cursor.fetchall():
            self.tree.insert('', 'end', values=row)
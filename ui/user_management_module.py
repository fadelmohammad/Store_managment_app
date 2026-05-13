# user_management_module.py

import customtkinter as ctk
import tkinter.messagebox as messagebox
from tkinter import ttk

class UserManagementFrame(ctk.CTkFrame):
    def __init__(self, parent, app, user_service, current_user):
        super().__init__(parent)
        self.app = app
        self.user_service = user_service
        self.current_user = current_user
        self.selected_user_id = None
        
        self.create_widgets()
        self.load_users()
    
    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Back to Dashboard",
            command=lambda: self.app.show_frame("dashboard"),
            fg_color="transparent",
            hover_color="#3a3a3a",
            width=140,
            height=35,
            font=ctk.CTkFont(size=12)
        )
        back_btn.pack(side="left")
        
        title = ctk.CTkLabel(
            header_frame,
            text="User Management",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(side="left", padx=20)
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        self.create_add_panel(content_frame, 0)
        self.create_users_panel(content_frame, 1)
    
    def create_add_panel(self, parent, col):
        add_frame = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15)
        add_frame.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(add_frame, text="Add New User", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color="#2ecc71").pack(anchor="w", padx=20, pady=(20, 15))
        
        form_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="Username:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.username_entry = ctk.CTkEntry(form_frame, height=40, font=ctk.CTkFont(size=14))
        self.username_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Password:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.password_entry = ctk.CTkEntry(form_frame, show="*", height=40, font=ctk.CTkFont(size=14))
        self.password_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Full Name:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.fullname_entry = ctk.CTkEntry(form_frame, height=40, font=ctk.CTkFont(size=14))
        self.fullname_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Role:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.role_combo = ctk.CTkComboBox(form_frame, values=['user', 'viewer', 'accountant', 'manager', 'admin'], 
                                          height=40, font=ctk.CTkFont(size=14))
        self.role_combo.set('user')
        self.role_combo.pack(fill="x", pady=(0, 20))
        
        add_btn = ctk.CTkButton(
            form_frame, 
            text="Add User", 
            command=self.add_user,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        add_btn.pack(fill="x", pady=10)
        
        clear_btn = ctk.CTkButton(
            form_frame, 
            text="Clear Fields", 
            command=self.clear_form,
            fg_color="#e67e22",
            hover_color="#d35400",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        clear_btn.pack(fill="x", pady=5)
    
    def create_users_panel(self, parent, col):
        users_frame = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15)
        users_frame.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(users_frame, text="Existing Users", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color="#3498db").pack(anchor="w", padx=20, pady=(20, 15))
        
        self.create_user_table(users_frame)
        
        button_frame = ctk.CTkFrame(users_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="Refresh",
            command=self.load_users,
            fg_color="#3498db",
            hover_color="#2980b9",
            height=35,
            font=ctk.CTkFont(size=13)
        )
        refresh_btn.pack(side="left", padx=5)
        
        view_logs_btn = ctk.CTkButton(
            button_frame,
            text="View User Logs",
            command=self.view_user_logs,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            height=35,
            font=ctk.CTkFont(size=13)
        )
        view_logs_btn.pack(side="left", padx=5)
    
    def create_user_table(self, parent):
        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ('ID', 'Username', 'Full Name', 'Role', 'Status', 'Actions')
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        
        self.tree.heading('ID', text='ID')
        self.tree.heading('Username', text='Username')
        self.tree.heading('Full Name', text='Full Name')
        self.tree.heading('Role', text='Role')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Actions', text='Actions')
        
        self.tree.column('ID', width=50, anchor='center')
        self.tree.column('Username', width=120)
        self.tree.column('Full Name', width=150)
        self.tree.column('Role', width=100, anchor='center')
        self.tree.column('Status', width=80, anchor='center')
        self.tree.column('Actions', width=150, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind('<ButtonRelease-1>', self.on_user_select)
    
    def load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        users = self.user_service.get_all_users()
        
        for user in users:
            status = "Active" if user['is_active'] else "Inactive"
            status_color = "green" if user['is_active'] else "red"
            
            self.tree.insert('', 'end', values=(
                user['id'],
                user['username'],
                user['full_name'] or 'N/A',
                user['role'].capitalize(),
                status,
                'Edit | Delete'
            ), tags=(user['id'],))
    
    def on_user_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            user_id = item['values'][0]
            self.show_user_actions(user_id)
    
    def show_user_actions(self, user_id):
        user = self.user_service.get_user_by_id(user_id)
        
        if not user:
            return
        
        action_window = ctk.CTkToplevel(self)
        action_window.title(f"Manage User: {user['username']}")
        action_window.geometry("500x600")
        action_window.resizable(False, False)
        action_window.grab_set()
        
        main_frame = ctk.CTkFrame(action_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(main_frame, text=f"User: {user['username']}", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 20))
        
        info_frame = ctk.CTkFrame(main_frame, fg_color="#2f3640", corner_radius=15)
        info_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(info_frame, text=f"ID: {user['id']}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=f"Full Name: {user['full_name'] or 'N/A'}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=f"Role: {user['role'].capitalize()}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=f"Status: {'Active' if user['is_active'] else 'Inactive'}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=f"Last Login: {user['last_login'] or 'Never'}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text=f"Member Since: {user['created_at'] or 'Unknown'}").pack(anchor="w", padx=20, pady=5)
        
        edit_frame = ctk.CTkFrame(main_frame, fg_color="#2f3640", corner_radius=15)
        edit_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(edit_frame, text="Edit User", font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color="#2ecc71").pack(anchor="w", padx=20, pady=(15, 10))
        
        if user['username'] != "admin" or self.current_user['username'] == "admin":
            ctk.CTkLabel(edit_frame, text="Change Role:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20)
            role_combo = ctk.CTkComboBox(edit_frame, values=['user', 'viewer', 'accountant', 'manager', 'admin'], width=200)
            role_combo.set(user['role'])
            role_combo.pack(anchor="w", padx=20, pady=(5, 15))
            
            ctk.CTkLabel(edit_frame, text="Change Status:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20)
            status_var = ctk.StringVar(value="Active" if user['is_active'] else "Inactive")
            status_combo = ctk.CTkComboBox(edit_frame, values=['Active', 'Inactive'], variable=status_var, width=200)
            status_combo.pack(anchor="w", padx=20, pady=(5, 15))
            
            ctk.CTkLabel(edit_frame, text="Reset Password:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=20)
            new_password_entry = ctk.CTkEntry(edit_frame, width=200, show="*", placeholder_text="New password")
            new_password_entry.pack(anchor="w", padx=20, pady=(5, 15))
            
            def update_user():
                new_role = role_combo.get()
                new_status = 1 if status_var.get() == "Active" else 0
                new_password = new_password_entry.get()
                
                try:
                    if new_role != user['role']:
                        self.user_service.update_user_role(user['id'], new_role)
                    
                    if new_status != user['is_active']:
                        self.user_service.update_user_status(user['id'], new_status)
                    
                    if new_password:
                        if len(new_password) < 4:
                            messagebox.showwarning("Warning", "Password must be at least 4 characters")
                            return
                        self.user_service.update_user_password(user['id'], new_password)
                    
                    messagebox.showinfo("Success", "User updated successfully")
                    action_window.destroy()
                    self.load_users()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update user: {str(e)}")
            
            update_btn = ctk.CTkButton(edit_frame, text="Update User", command=update_user, fg_color="#2ecc71", height=40)
            update_btn.pack(fill="x", padx=20, pady=10)
            
            if user['username'] != "admin":
                def delete_user():
                    if messagebox.askyesno("Confirm", f"Are you sure you want to delete user '{user['username']}'?"):
                        try:
                            self.user_service.delete_user(user['id'])
                            messagebox.showinfo("Success", "User deleted successfully")
                            action_window.destroy()
                            self.load_users()
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to delete user: {str(e)}")
                
                delete_btn = ctk.CTkButton(edit_frame, text="Delete User", command=delete_user, fg_color="#e74c3c", hover_color="#c0392b", height=40)
                delete_btn.pack(fill="x", padx=20, pady=(5, 20))
    
    def view_user_logs(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user first")
            return
        
        item = self.tree.item(selected[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        logs_window = ctk.CTkToplevel(self)
        logs_window.title(f"User Activity Logs - {username}")
        logs_window.geometry("900x500")
        logs_window.grab_set()
        
        main_frame = ctk.CTkFrame(logs_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(main_frame, text=f"Activity Logs for: {username}", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        columns = ('ID', 'Action', 'Details', 'IP Address', 'Timestamp')
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        tree.heading('ID', text='ID')
        tree.heading('Action', text='Action')
        tree.heading('Details', text='Details')
        tree.heading('IP Address', text='IP Address')
        tree.heading('Timestamp', text='Timestamp')
        
        tree.column('ID', width=50)
        tree.column('Action', width=120)
        tree.column('Details', width=350)
        tree.column('IP Address', width=120)
        tree.column('Timestamp', width=180)
        
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        logs = self.user_service.get_user_logs(user_id, limit=100)
        
        for log in logs:
            tree.insert('', 'end', values=(
                log['id'],
                log['action'],
                log['details'],
                log['ip_address'],
                log['timestamp']
            ))
    
    def add_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        fullname = self.fullname_entry.get().strip()
        role = self.role_combo.get()
        
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter username and password")
            return
        
        if len(password) < 4:
            messagebox.showwarning("Warning", "Password must be at least 4 characters")
            return
        
        try:
            self.user_service.create_user(username, password, fullname, role)
            messagebox.showinfo("Success", "User added successfully")
            self.clear_form()
            self.load_users()
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                messagebox.showerror("Error", "Username already exists")
            else:
                messagebox.showerror("Error", f"Failed to add user: {str(e)}")
    
    def clear_form(self):
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.fullname_entry.delete(0, 'end')
        self.role_combo.set('user')
    
    def refresh_data(self):
        self.load_users()
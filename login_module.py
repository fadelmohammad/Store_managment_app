# login_module.py

import customtkinter as ctk
import tkinter.messagebox as messagebox
import hashlib
import logging

class LoginFrame(ctk.CTkFrame):
    def __init__(self, container, app, on_login_success):
        super().__init__(container)
        self.app = app
        self.on_login_success = on_login_success
        self.db_connection = app.db_connection
        
        self.configure(fg_color=("#2b2b2b", "#1a1a1a"))
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(expand=True, fill="both")
        
        self.login_card = ctk.CTkFrame(
            self.main_frame, 
            width=400, 
            height=500,
            corner_radius=20,
            fg_color=("#3a3a3a", "#2d2d2d")
        )
        self.login_card.pack(expand=True, pady=50)
        self.login_card.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(
            self.login_card,
            text="🏪 OmniPOS",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#1f538d", "#3a7eb6")
        )
        self.title_label.pack(pady=(40, 10))
        
        self.subtitle_label = ctk.CTkLabel(
            self.login_card,
            text="Store Management System",
            font=ctk.CTkFont(size=14)
        )
        self.subtitle_label.pack(pady=(0, 30))
        
        self.username_entry = ctk.CTkEntry(
            self.login_card,
            placeholder_text="Username",
            width=300,
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.username_entry.pack(pady=10)
        
        self.password_entry = ctk.CTkEntry(
            self.login_card,
            placeholder_text="Password",
            show="*",
            width=300,
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.password_entry.pack(pady=10)
        
        self.remember_var = ctk.BooleanVar()
        self.remember_check = ctk.CTkCheckBox(
            self.login_card,
            text="Remember me",
            variable=self.remember_var,
            font=ctk.CTkFont(size=12)
        )
        self.remember_check.pack(pady=5)
        
        self.login_button = ctk.CTkButton(
            self.login_card,
            text="Login",
            command=self.login,
            width=300,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f538d",
            hover_color="#2a6bb3"
        )
        self.login_button.pack(pady=20)
        
        self.error_label = ctk.CTkLabel(
            self.login_card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        self.error_label.pack(pady=5)
        
        self.info_label = ctk.CTkLabel(
            self.login_card,
            text="Default user: admin\nPassword: admin123",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.info_label.pack(pady=(20, 10))
        
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        self.load_saved_user()
    
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            self.error_label.configure(text="Please enter username and password")
            return
        
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            hashed_pass = self.hash_password(password)
            cursor.execute("""
                SELECT id, username, full_name, role, is_active 
                FROM users 
                WHERE username = ? AND password = ?
            """, (username, hashed_pass))
            
            user = cursor.fetchone()
            
            if user:
                user_id, username, full_name, role, is_active = user
                
                if not is_active:
                    self.error_label.configure(text="This account is inactive. Please contact administrator.")
                    return
                
                cursor.execute("SELECT * FROM permissions WHERE role = ?", (role,))
                permissions_row = cursor.fetchone()
                
                if permissions_row:
                    permission_keys = [
                        'can_view_products', 'can_edit_products', 'can_delete_products',
                        'can_view_invoices', 'can_create_invoices', 'can_edit_invoices', 
                        'can_delete_invoices', 'can_view_accounts', 'can_edit_accounts',
                        'can_view_reports', 'can_manage_users', 'can_manage_settings'
                    ]
                    permissions = dict(zip(permission_keys, permissions_row[2:]))
                else:
                    permissions = {}
                
                cursor.execute("""
                    INSERT INTO user_logs (user_id, action, details, ip_address)
                    VALUES (?, ?, ?, ?)
                """, (user_id, "login", "Successful login", "localhost"))
                
                cursor.execute("""
                    UPDATE users SET last_login = datetime('now') WHERE id = ?
                """, (user_id,))
                
                conn.commit()
                
                self.app.current_user = {
                    'id': user_id,
                    'username': username,
                    'full_name': full_name,
                    'role': role,
                    'permissions': permissions
                }
                
                if self.remember_var.get():
                    self.save_user_session(username)
                
                messagebox.showinfo("Success", f"Welcome {full_name or username}!")
                self.on_login_success()
                
            else:
                self.error_label.configure(text="Invalid username or password")
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO user_logs (user_id, action, details, ip_address)
                        VALUES (?, ?, ?, ?)
                    """, (None, "login_failed", f"Failed attempt for user: {username}", "localhost"))
                    conn.commit()
                except:
                    pass
                
        except Exception as e:
            self.error_label.configure(text=f"Database error: {str(e)}")
            logging.error(f"Login error: {e}")

    def save_user_session(self, username):
        import json
        import os
        session_file = "session.json"
        with open(session_file, "w") as f:
            json.dump({"username": username}, f)
    
    def load_saved_user(self):
        import json
        import os
        session_file = "session.json"
        if os.path.exists(session_file):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                    if "username" in data:
                        self.username_entry.insert(0, data["username"])
                        self.remember_var.set(True)
            except:
                pass
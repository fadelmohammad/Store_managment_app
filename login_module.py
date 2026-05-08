# login_module.py

import json
import os
import customtkinter as ctk
import tkinter.messagebox as messagebox
import logging

class LoginFrame(ctk.CTkFrame):
    def __init__(self, container, app, login_service, on_login_success):
        super().__init__(container)
        self.app = app
        self.login_service = login_service
        self.on_login_success = on_login_success
        
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

        self.forgot_btn = ctk.CTkButton(
            self.login_card,
            text="Forgot Password?",
            command=self.open_reset_dialog,
            width=300,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color="#3a7eb6",
        )
        self.forgot_btn.pack(pady=(0, 5))

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
    
    
    def open_reset_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Reset Password")
        dialog.geometry("380x320")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Reset Password", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(25, 15))

        username_entry = ctk.CTkEntry(dialog, placeholder_text="Username", width=300, height=40)
        username_entry.pack(pady=8)

        new_pass_entry = ctk.CTkEntry(dialog, placeholder_text="New Password", show="*", width=300, height=40)
        new_pass_entry.pack(pady=8)

        confirm_pass_entry = ctk.CTkEntry(dialog, placeholder_text="Confirm New Password", show="*", width=300, height=40)
        confirm_pass_entry.pack(pady=8)

        status_label = ctk.CTkLabel(dialog, text="", font=ctk.CTkFont(size=12), text_color="red")
        status_label.pack(pady=4)

        def do_reset():
            try:
                self.app.user_service.reset_password(
                    username_entry.get().strip(),
                    new_pass_entry.get(),
                    confirm_pass_entry.get(),
                )
                dialog.destroy()
                messagebox.showinfo("Success", "Password reset successfully. You can now log in.")
            except ValueError as e:
                status_label.configure(text=str(e))

        ctk.CTkButton(
            dialog, text="Reset Password", command=do_reset,
            width=300, height=40, fg_color="#1f538d", hover_color="#2a6bb3"
        ).pack(pady=8)

    def show_welcome_toast(self, name, callback, duration=2500):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(fg_color="#1f538d")

        ctk.CTkLabel(
            toast,
            text=f"👋  Welcome, {name}!",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white",
        ).pack(padx=40, pady=25)

        toast.update_idletasks()
        w, h = toast.winfo_width(), toast.winfo_height()
        sw, sh = toast.winfo_screenwidth(), toast.winfo_screenheight()
        toast.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

        def close():
            toast.destroy()
            callback()

        toast.after(duration, close)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.configure(text="Please enter username and password")
            return

        try:
            user = self.login_service.login(username, password)
            self.app.current_user = user

            if self.remember_var.get():
                self.save_user_session(user["username"])

            self.show_welcome_toast(user["full_name"] or user["username"], self.on_login_success)

        except ValueError as e:
            self.error_label.configure(text=str(e))
        except Exception as e:
            self.error_label.configure(text=f"Error: {str(e)}")
            logging.error(f"Login error: {e}")

    def save_user_session(self, username):
        with open("session.json", "w") as f:
            json.dump({"username": username}, f)

    def load_saved_user(self):
        if os.path.exists("session.json"):
            try:
                with open("session.json", "r") as f:
                    data = json.load(f)
                    if "username" in data:
                        self.username_entry.insert(0, data["username"])
                        self.remember_var.set(True)
            except Exception as e:
                # Don't block UI startup if session.json is corrupt/unreadable
                logging.warning("Failed to load session.json: %s", e)

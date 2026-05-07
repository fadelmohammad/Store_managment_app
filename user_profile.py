# user_profile.py

import customtkinter as ctk
import tkinter.messagebox as messagebox


class UserProfileFrame(ctk.CTkFrame):
    def __init__(self, parent, app, user_service, current_user, on_update_callback):
        super().__init__(parent)
        self.app = app
        self.user_service = user_service
        self.current_user = current_user
        self.on_update_callback = on_update_callback
        
        self.create_widgets()
        self.load_user_data()
    
    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Back to Dashboard",
            command=lambda: self.app.show_frame("dashboard"),
            fg_color="transparent",
            hover_color="#3a3a3a",
            width=120,
            height=30,
            font=ctk.CTkFont(size=12)
        )
        back_btn.pack(side="left")
        
        profile_icon = ctk.CTkLabel(
            main_frame, 
            text="👤", 
            font=ctk.CTkFont(size=80)
        )
        profile_icon.pack(pady=(0, 10))
        
        title = ctk.CTkLabel(
            main_frame, 
            text="My Profile", 
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(0, 30))
        
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        self.create_info_panel(content_frame, 0)
        self.create_edit_panel(content_frame, 1)
    
    def create_info_panel(self, parent, col):
        info_frame = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15)
        info_frame.grid(row=0, column=col, sticky="nsew", padx=15, pady=10)
        
        ctk.CTkLabel(info_frame, text="Account Information", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color="#3498db").pack(anchor="w", padx=25, pady=(20, 15))
        
        info_container = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        row = 0
        fields = [
            ("Username:", "username_label"),
            ("Full Name:", "fullname_display"),
            ("Role:", "role_label"),
            ("Status:", "status_label"),
            ("Last Login:", "last_login_label"),
            ("Member Since:", "created_label")
        ]
        
        for label, attr in fields:
            ctk.CTkLabel(info_container, text=label, font=ctk.CTkFont(size=14, weight="bold"), 
                        width=120).grid(row=row, column=0, sticky="w", pady=8)
            setattr(self, attr, ctk.CTkLabel(info_container, text="", font=ctk.CTkFont(size=14)))
            getattr(self, attr).grid(row=row, column=1, sticky="w", pady=8, padx=(10, 0))
            row += 1
    
    def create_edit_panel(self, parent, col):
        edit_frame = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15)
        edit_frame.grid(row=0, column=col, sticky="nsew", padx=15, pady=10)
        
        ctk.CTkLabel(edit_frame, text="Edit Profile", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color="#2ecc71").pack(anchor="w", padx=25, pady=(20, 15))
        
        edit_container = ctk.CTkFrame(edit_frame, fg_color="transparent")
        edit_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        ctk.CTkLabel(edit_container, text="Full Name:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.name_entry = ctk.CTkEntry(edit_container, height=40, font=ctk.CTkFont(size=14))
        self.name_entry.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(edit_container, text="Current Password:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.current_password_entry = ctk.CTkEntry(edit_container, show="*", height=40, font=ctk.CTkFont(size=14))
        self.current_password_entry.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(edit_container, text="New Password:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.new_password_entry = ctk.CTkEntry(edit_container, show="*", height=40, font=ctk.CTkFont(size=14))
        self.new_password_entry.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(edit_container, text="Confirm New Password:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.confirm_password_entry = ctk.CTkEntry(edit_container, show="*", height=40, font=ctk.CTkFont(size=14))
        self.confirm_password_entry.pack(fill="x", pady=(0, 30))
        
        button_frame = ctk.CTkFrame(edit_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)
        
        save_btn = ctk.CTkButton(
            button_frame, 
            text="Save Changes", 
            command=self.save_profile,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        save_btn.pack(fill="x", pady=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame, 
            text="Reset Fields", 
            command=self.reset_fields,
            fg_color="#e67e22",
            hover_color="#d35400",
            height=40,
            font=ctk.CTkFont(size=13)
        )
        cancel_btn.pack(fill="x", pady=5)
    
    def load_user_data(self):
        try:
            user = self.user_service.get_user_profile(self.current_user['id'])

            if user:
                self.username_label.configure(text=user['username'])

                current_name = user['full_name'] or ""
                self.name_entry.delete(0, 'end')
                self.name_entry.insert(0, current_name)
                self.fullname_display.configure(text=current_name or "Not set")

                self.role_label.configure(text=user['role'].capitalize())

                status = "Active" if user['is_active'] else "Inactive"
                status_color = "#2ecc71" if user['is_active'] else "#e74c3c"
                self.status_label.configure(text=status, text_color=status_color)

                self.last_login_label.configure(text=user['last_login'])
                self.created_label.configure(text=user['created_at'])

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load user data: {str(e)}")
    
    def reset_fields(self):
        self.name_entry.delete(0, 'end')
        user = self.user_service.get_user_profile(self.current_user['id'])
        if user and user['full_name']:
            self.name_entry.insert(0, user['full_name'])

        self.current_password_entry.delete(0, 'end')
        self.new_password_entry.delete(0, 'end')
        self.confirm_password_entry.delete(0, 'end')
    
    
    def save_profile(self):
        try:
            result = self.user_service.update_own_profile(
                self.current_user['id'],
                self.name_entry.get(),
                self.current_password_entry.get(),
                self.new_password_entry.get(),
                self.confirm_password_entry.get(),
            )

            self.current_user['full_name'] = result['full_name']
            self.fullname_display.configure(text=result['full_name'])

            self.current_password_entry.delete(0, 'end')
            self.new_password_entry.delete(0, 'end')
            self.confirm_password_entry.delete(0, 'end')

            if result['password_changed']:
                messagebox.showinfo("Success", "Profile updated successfully!\nPlease login again with your new password.")
                if messagebox.askyesno("Logout", "Do you want to logout now?"):
                    self.app.logout()
            else:
                messagebox.showinfo("Success", "Profile updated successfully!")
                if self.on_update_callback:
                    self.on_update_callback(self.current_user)
                    self.app.show_frame("dashboard")
                    self.app.update_user_info(self.current_user)

        except ValueError as e:
            messagebox.showwarning("Warning", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update profile: {str(e)}")
    
    def refresh_data(self):
        self.load_user_data()
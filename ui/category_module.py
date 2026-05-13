# category_module.py

import customtkinter as ctk
import logging
from tkinter import messagebox
import sqlite3


class CategoryManagementWindow(ctk.CTkToplevel):
    """Professional category management window"""

    def __init__(self, parent, category_service, inventory_service=None, refresh_callback=None):
        super().__init__(parent)

        self.category_service = category_service
        self.inventory_service = inventory_service
        self.refresh_callback = refresh_callback
        self.cat_map = {}  # Store {category_path: category_id}


        self.title("Category Manager")
        self.geometry("800x600")
        self.minsize(700, 500)
        self.attributes("-topmost", True)
        self.resizable(True, True)


        self._setup_ui()
        self.refresh_category_list()
        self._center_window()

    
    def _show_warning(self, title, message):
        """Show warning message correctly"""
        self.attributes("-topmost", False)
        messagebox.showwarning(title, message)
        self.attributes("-topmost", True)

    def _show_info(self, title, message):
        """Show info message correctly"""
        self.attributes("-topmost", False)
        messagebox.showinfo(title, message)
        self.attributes("-topmost", True)

    def _show_error(self, title, message):
        """Show error message correctly"""
        self.attributes("-topmost", False)
        messagebox.showerror(title, message)
        self.attributes("-topmost", True)

    def _ask_yesno(self, title, message):
        """Show confirmation dialog correctly"""
        self.attributes("-topmost", False)
        result = messagebox.askyesno(title, message)
        self.attributes("-topmost", True)
        return result



    def _setup_ui(self):
        """Build the entire UI"""


        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)


        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header_frame,
            text="🏷️ Category Manager",
            font=("Arial", 22, "bold"),
            text_color="#2ecc71"
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="✕ Close",
            width=80,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.destroy
        ).pack(side="right")

        
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(10, 10))


        header_grid = ctk.CTkFrame(list_frame, fg_color="#2c3e50", height=40)
        header_grid.pack(fill="x", pady=(0, 2))
        header_grid.pack_propagate(False)

        ctk.CTkLabel(header_grid, text="#", font=("Arial", 13, "bold"), width=50).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(header_grid, text="Category Name", font=("Arial", 13, "bold"), width=300).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(header_grid, text="Parent Category", font=("Arial", 13, "bold"), width=200).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkLabel(header_grid, text="Products Count", font=("Arial", 13, "bold"), width=120).grid(row=0, column=3, padx=5, pady=5)

        self.categories_container = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="#1e1e1e",
            border_width=1,
            border_color="#34495e"
        )
        self.categories_container.pack(fill="both", expand=True)

        add_frame = ctk.CTkFrame(main_frame, fg_color="#2c3e50", corner_radius=10)
        add_frame.pack(fill="x", pady=(5, 0))

        ctk.CTkLabel(
            add_frame,
            text=" Add New Category",
            font=("Arial", 14, "bold"),
            text_color="#f1c40f"
        ).pack(anchor="w", padx=15, pady=(10, 5))


        input_row = ctk.CTkFrame(add_frame, fg_color="#2c3e50")
        input_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(input_row, text="Name:", font=("Arial", 12)).pack(side="left", padx=(0, 5))
        self.new_cat_name = ctk.CTkEntry(
            input_row,
            placeholder_text="Example: Electronics",
            width=180,
            font=("Arial", 12)
        )
        self.new_cat_name.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(input_row, text="Parent Category:", font=("Arial", 12)).pack(side="left", padx=(0, 5))
        self.parent_var = ctk.StringVar(value="None (Root)")
        self.parent_dropdown = ctk.CTkOptionMenu(
            input_row,
            variable=self.parent_var,
            values=[],
            width=180,
            font=("Arial", 12),
            fg_color="#34495e",
            button_color="#2c3e50"
        )
        self.parent_dropdown.pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            input_row,
            text="Add",
            width=100,
            fg_color="#27ae60",
            hover_color="#219a52",
            command=self._add_category,
            font=("Arial", 12, "bold")
        ).pack(side="left")

   
        delete_frame = ctk.CTkFrame(main_frame, fg_color="#3d1a1a", corner_radius=10)
        delete_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            delete_frame,
            text="🗑️ Delete Category",
            font=("Arial", 14, "bold"),
            text_color="#e74c3c"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        delete_row = ctk.CTkFrame(delete_frame, fg_color="#3d1a1a")
        delete_row.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(delete_row, text="Select category to delete:", font=("Arial", 12)).pack(side="left", padx=(0, 10))
        self.delete_var = ctk.StringVar(value="Select category...")
        self.delete_dropdown = ctk.CTkOptionMenu(
            delete_row,
            variable=self.delete_var,
            values=[],
            width=250,
            font=("Arial", 12),
            fg_color="#c0392b",
            button_color="#e74c3c"
        )
        self.delete_dropdown.pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            delete_row,
            text="Delete",
            width=120,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self._delete_category,
            font=("Arial", 12, "bold")
        ).pack(side="left")

        ctk.CTkLabel(
            delete_frame,
            text=" Warning: Deleting a category will move all products to the parent category (or root)",
            font=("Arial", 10),
            text_color="#f39c12"
        ).pack(anchor="w", padx=15, pady=(0, 10))

    def _center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 600) // 2
        self.geometry(f"800x600+{x}+{y}")



    def refresh_category_list(self):
        """Update category dropdowns and display"""
        try:
            logging.debug("Refreshing category list...")
            cats = self.category_service.get_categories()
            logging.debug(f"Received {len(cats)} categories")
            
            if not cats:
                logging.info("No categories found")
                self.parent_dropdown.configure(values=["None (Root)"])
                self.delete_dropdown.configure(values=["No categories"])
                self._display_categories([])
                return
            
            self.cat_map = {}
            for cat in cats:
                path = cat.get("path", cat.get("name", "Unknown"))
                cat_id = cat.get("id")
                self.cat_map[path] = cat_id
                logging.debug(f"Mapped: {path} -> ID: {cat_id}")
            
            paths = list(self.cat_map.keys())
            logging.debug(f"Paths: {paths}")
            
            # Update dropdowns
            dropdown_values = ["None (Root)"] + paths
            self.parent_dropdown.configure(values=dropdown_values)
            self.delete_dropdown.configure(values=paths if paths else ["No categories"])

            # Display categories in table
            self._display_categories(cats)
            
        except Exception as e:
            logging.error(f"Error in refresh_category_list: {e}")
            import traceback
            traceback.print_exc()

    def _display_categories(self, categories):
        """Display categories in scrollable table"""
        # Clear old content
        for widget in self.categories_container.winfo_children():
            widget.destroy()

        if not categories:
            ctk.CTkLabel(
                self.categories_container,
                text=" No categories found. Add a new category below.",
                font=("Arial", 14),
                text_color="#7f8c8d"
            ).pack(pady=40)
            return

        # Display each category in a row
        for idx, cat in enumerate(categories, 1):
            self._create_category_row(cat, idx)

    def _create_category_row(self, category, index):
        """Create a single category row"""
        row_frame = ctk.CTkFrame(
            self.categories_container,
            fg_color="#2d2d2d" if index % 2 == 0 else "#252525",
            corner_radius=6,
            height=40
        )
        row_frame.pack(fill="x", pady=1, padx=3)
        row_frame.pack_propagate(False)

        # Index number
        ctk.CTkLabel(
            row_frame, 
            text=str(index), 
            font=("Arial", 12), 
            width=50,
            anchor="center"
        ).grid(row=0, column=0, padx=5, pady=5)

        # Category name (path)
        cat_name = category.get("path", category.get("name", "Unknown"))
        ctk.CTkLabel(
            row_frame, 
            text=cat_name, 
            font=("Arial", 12), 
            width=300,
            anchor="w"
        ).grid(row=0, column=1, padx=5, pady=5)

        # Parent category name
        parent = category.get("parent_name", "Root")
        ctk.CTkLabel(
            row_frame, 
            text=parent if parent else "Root", 
            font=("Arial", 11), 
            width=200,
            text_color="#95a5a6",
            anchor="w"
        ).grid(row=0, column=2, padx=5, pady=5)

        # Product count
        try:
            product_count = self.category_service.count_products_in_category(category["id"])
        except sqlite3.Error as e:
            logging.error(f"DB error counting products for category {category.get('id', 'unknown')}: {e}")
            product_count = 0
        except Exception as e:
            logging.error(f"Unexpected error counting products: {e}")
            product_count = 0

        count_color = "#2ecc71" if product_count > 0 else "#7f8c8d"
        ctk.CTkLabel(
            row_frame, 
            text=str(product_count), 
            font=("Arial", 12, "bold"), 
            width=120,
            text_color=count_color,
            anchor="center"
        ).grid(row=0, column=3, padx=5, pady=5)


    def _add_category(self):
        """Add a new category"""
        name = self.new_cat_name.get().strip()
        if not name:
            self._show_warning("Warning", "Please enter a category name")
            return

        parent_path = self.parent_var.get()
        parent_id = None
        if parent_path != "None (Root)":
            parent_id = self.cat_map.get(parent_path)

        try:
            self.category_service.add_category(name, parent_id)
            self.refresh_category_list()
            self.new_cat_name.delete(0, "end")
            self.parent_var.set("None (Root)")

            if self.refresh_callback:
                self.refresh_callback()

            logging.info(f"Category '{name}' added successfully")
            self._show_info("Success", f"Category '{name}' added successfully")
        except Exception as e:
            self._show_error("Error", f"Failed to add category:\n{str(e)}")

    def _delete_category(self):
        """Delete selected category"""
        selected = self.delete_var.get()
        
        if not selected or selected == "Select category..." or selected == "No categories":
            self._show_warning("Warning", "Please select a category to delete")
            return

        cat_id = self.cat_map.get(selected)
        
        if not cat_id:
            self._show_error("Error", f"Could not find ID for category '{selected}'")
            return

        confirm = self._ask_yesno(
            "Confirm Delete",
            f" Are you sure you want to delete '{selected}'?\n\n"
            "Note: Products in this category will be moved to the parent category (or root)."
        )
        
        if not confirm:
            return

        try:
            self.category_service.delete_category(cat_id)
            self.refresh_category_list()
            self.delete_var.set("Select category...")

            if self.refresh_callback:
                self.refresh_callback()

            self._show_info("Success", f" Category '{selected}' deleted successfully")
        except Exception as e:
            self._show_error("Error", f"Failed to delete category:\n{str(e)}")
# dashboard.py

import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from safe_eval import safe_eval
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from collections import Counter
from ui.print_dialog import PrintDialog  # Import the print dialog

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.current_exchange_rate = getattr(self.app, "exchange_rate", 15000)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.setup_main_area()
        self.refresh_stats()

    def setup_main_area(self):
        # Create navigation bar first
        nav_bar = ctk.CTkFrame(self, fg_color="transparent")
        nav_bar.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkButton(
            nav_bar,
            text="Back",
            width=100,
            fg_color="#444444",
            hover_color="#555555",
            command=self.app.go_back,
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(nav_bar, text="Home", width=100, command=self.app.go_home).pack(
            side="left", padx=5
        )
        
        # Add Print button
        ctk.CTkButton(
            nav_bar,
            text="Print",
            width=100,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.open_print_dialog
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            nav_bar, text="Dashboard", font=("Arial", 16, "bold")
        ).pack(side="right", padx=20)

        self.main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.main_container.grid_columnconfigure((0, 1), weight=1)

        self.create_top_cards()
        self.create_charts_section()
        self.create_bottom_section()

    def create_top_cards(self):
        cards_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        cards_frame.grid(
            row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 20)
        )
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.rev_card = self.create_card(cards_frame, 0, "Daily Sales Revenue", "#f1c40f", 0)
        self.rev_label = ctk.CTkLabel(
            self.rev_card, text="$0.00", font=ctk.CTkFont(size=36, weight="bold")
        )
        self.rev_label.pack(expand=True)

        self.syp_card = self.create_card(cards_frame, 1, "Daily Sales (SYP)", "#2ecc71", 1)
        self.syp_label = ctk.CTkLabel(
            self.syp_card, text="0 SYP", font=ctk.CTkFont(size=36, weight="bold")
        )
        self.syp_label.pack(expand=True)

        self.trans_card = self.create_card(cards_frame, 2, "Today's Transactions", "#3498db", 2)
        self.trans_label = ctk.CTkLabel(
            self.trans_card, text="0", font=ctk.CTkFont(size=36, weight="bold")
        )
        self.trans_label.pack(expand=True)

        self.ex_card = self.create_card(cards_frame, 3, "USD Exchange Rate", "#9b59b6", 3)
        self.ex_lbl = ctk.CTkLabel(
            self.ex_card,
            text=f"1 USD = {self.current_exchange_rate:,} SYP",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.ex_lbl.pack(pady=10)

        ex_frame = ctk.CTkFrame(self.ex_card, fg_color="transparent")
        ex_frame.pack(fill="x", padx=10, pady=5)
        self.ex_ent = ctk.CTkEntry(ex_frame, placeholder_text="New Rate...", width=100)
        self.ex_ent.pack(side="left", padx=5)
        ctk.CTkButton(ex_frame, text="Set", width=50, command=self.update_ex_rate).pack(
            side="right"
        )

        refresh_btn = ctk.CTkButton(
            cards_frame,
            text="Refresh All",
            command=self.refresh_stats,
            fg_color="#e67e22",
            height=35,
            font=ctk.CTkFont(size=12),
        )
        refresh_btn.grid(row=1, column=0, columnspan=4, pady=10)

    def create_card(self, parent, col, title, color, col_index):
        card = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15, height=140)
        card.grid(row=0, column=col_index, sticky="nsew", padx=10, pady=10)
        card.grid_propagate(False)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=color,
        ).pack(pady=(15, 5))
        return card

    def create_charts_section(self):
        charts_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        charts_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=20)
        charts_frame.grid_columnconfigure((0, 1), weight=1)

        self.create_best_selling_chart(charts_frame, 0)
        self.create_top_stock_chart(charts_frame, 1)

    def create_best_selling_chart(self, parent, col):
        chart_card = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15)
        chart_card.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            chart_card,
            text="Best Selling Products (This Month)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f1c40f",
        ).pack(pady=10)

        self.best_selling_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        self.best_selling_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_best_selling_data()

    def create_top_stock_chart(self, parent, col):
        chart_card = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15)
        chart_card.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            chart_card,
            text="Top Stock Items (Warehouse)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2ecc71",
        ).pack(pady=10)

        self.top_stock_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        self.top_stock_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_top_stock_data()

    def create_bottom_section(self):
        bottom_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=20)
        bottom_frame.grid_columnconfigure((0, 1), weight=1)

        self.create_sales_timing_chart(bottom_frame, 0)
        self.create_calculator_widget(bottom_frame, 1)

    def create_sales_timing_chart(self, parent, col):
        chart_card = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15)
        chart_card.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            chart_card,
            text="Best Selling Hours (This Month)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#3498db",
        ).pack(pady=10)

        self.timing_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        self.timing_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_sales_timing_data()

    def create_calculator_widget(self, parent, col):
        calc_card = ctk.CTkFrame(parent, fg_color="#2f3640", corner_radius=15)
        calc_card.grid(row=0, column=col, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            calc_card,
            text="Quick Calculator",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#e74c3c",
        ).pack(pady=10)

        self.calc_ent = ctk.CTkEntry(
            calc_card,
            font=ctk.CTkFont(size=20),
            justify="right",
            height=50,
        )
        self.calc_ent.pack(fill="x", padx=20, pady=10)
        self.calc_ent.bind("<Return>", self.calculate)

        self.calc_res = ctk.CTkLabel(
            calc_card, text="= 0.00", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.calc_res.pack(pady=10)

        btn_frame = ctk.CTkFrame(calc_card, fg_color="transparent")
        btn_frame.pack(pady=10)

        buttons = [
            "7",
            "8",
            "9",
            "/",
            "4",
            "5",
            "6",
            "*",
            "1",
            "2",
            "3",
            "-",
            "0",
            ".",
            "=",
            "+",
        ]
        row, col_btn = 0, 0
        for btn in buttons:
            if btn == "=":
                ctk.CTkButton(
                    btn_frame,
                    text=btn,
                    width=60,
                    height=40,
                    command=lambda: self.calculate(),
                ).grid(row=row, column=col_btn, padx=2, pady=2)
            else:
                ctk.CTkButton(
                    btn_frame,
                    text=btn,
                    width=60,
                    height=40,
                    command=lambda b=btn: self.calc_ent.insert("end", b),
                ).grid(row=row, column=col_btn, padx=2, pady=2)

            col_btn += 1
            if col_btn > 3:
                col_btn = 0
                row += 1

        ctk.CTkButton(
            btn_frame,
            text="C",
            width=60,
            height=40,
            fg_color="red",
            command=lambda: self.calc_ent.delete(0, "end"),
        ).grid(row=row, column=0, columnspan=4, sticky="we", padx=2, pady=2)

    # ==========================================
    # Dashboard data (UI -> report_service)
    # ==========================================
    def load_best_selling_data(self):
        try:
            for widget in self.best_selling_frame.winfo_children():
                widget.destroy()

            rows = self.app.report_service.get_best_selling_products_this_month(limit=5) or []
            if rows:
                # rows: [(name, total_qty), ...]
                products = [
                    (r[0][:20] + "...") if len(r[0]) > 20 else r[0]
                    for r in rows
                ]
                quantities = [r[1] for r in rows]
                max_qty = max(quantities) if quantities else 1

                for i, (product, qty) in enumerate(zip(products, quantities)):
                    frame = ctk.CTkFrame(self.best_selling_frame, fg_color="transparent")
                    frame.pack(fill="x", pady=5)

                    percentage = (qty / max_qty) * 100 if max_qty > 0 else 0

                    ctk.CTkLabel(
                        frame, text=f"{i+1}.", width=30, font=ctk.CTkFont(size=12, weight="bold")
                    ).pack(side="left")
                    ctk.CTkLabel(frame, text=product, width=150, anchor="w").pack(
                        side="left", padx=5
                    )

                    progress = ctk.CTkProgressBar(frame, width=200, height=20)
                    progress.pack(side="left", padx=10)
                    progress.set(percentage / 100)

                    ctk.CTkLabel(
                        frame, text=str(qty), width=50, font=ctk.CTkFont(size=12, weight="bold")
                    ).pack(side="left")
            else:
                ctk.CTkLabel(
                    self.best_selling_frame,
                    text="No sales data available for this month",
                    font=ctk.CTkFont(size=14),
                ).pack(expand=True)

        except Exception as e:
            ctk.CTkLabel(
                self.best_selling_frame,
                text=f"Error loading data: {str(e)[:50]}",
                font=ctk.CTkFont(size=12),
                text_color="red",
            ).pack(expand=True)

    def load_top_stock_data(self):
        try:
            for widget in self.top_stock_frame.winfo_children():
                widget.destroy()

            rows = self.app.report_service.get_top_stock_items(limit=5) or []
            if rows:
                products = [
                    (r[0][:20] + "...") if len(r[0]) > 20 else r[0]
                    for r in rows
                ]
                quantities = [r[1] for r in rows]
                max_qty = max(quantities) if quantities else 1

                for i, (product, qty) in enumerate(zip(products, quantities)):
                    frame = ctk.CTkFrame(self.top_stock_frame, fg_color="transparent")
                    frame.pack(fill="x", pady=5)

                    percentage = (qty / max_qty) * 100 if max_qty > 0 else 0

                    ctk.CTkLabel(
                        frame, text=f"{i+1}.", width=30, font=ctk.CTkFont(size=12, weight="bold")
                    ).pack(side="left")
                    ctk.CTkLabel(frame, text=product, width=150, anchor="w").pack(
                        side="left", padx=5
                    )

                    progress = ctk.CTkProgressBar(
                        frame, width=200, height=20, progress_color="#2ecc71"
                    )
                    progress.pack(side="left", padx=10)
                    progress.set(percentage / 100)

                    ctk.CTkLabel(
                        frame, text=str(qty), width=50, font=ctk.CTkFont(size=12, weight="bold")
                    ).pack(side="left")
            else:
                ctk.CTkLabel(
                    self.top_stock_frame,
                    text="No products available",
                    font=ctk.CTkFont(size=14),
                ).pack(expand=True)

        except Exception as e:
            ctk.CTkLabel(
                self.top_stock_frame,
                text=f"Error loading data: {str(e)[:50]}",
                font=ctk.CTkFont(size=12),
                text_color="red",
            ).pack(expand=True)

    def load_sales_timing_data(self):
        try:
            for widget in self.timing_frame.winfo_children():
                widget.destroy()

            rows = self.app.report_service.get_best_selling_hours_this_month() or []
            if rows:
                # rows: [(hour_int, sales_count), ...]
                hours = [f"{int(r[0]):02d}:00" for r in rows]
                counts = [r[1] for r in rows]
                max_count = max(counts) if counts else 1

                for i, (hour, count) in enumerate(zip(hours, counts)):
                    frame = ctk.CTkFrame(self.timing_frame, fg_color="transparent")
                    frame.pack(fill="x", pady=3)

                    percentage = (count / max_count) * 100 if max_count > 0 else 0

                    ctk.CTkLabel(
                        frame, text=hour, width=60, font=ctk.CTkFont(size=11, weight="bold")
                    ).pack(side="left")

                    progress = ctk.CTkProgressBar(
                        frame, width=250, height=15, progress_color="#3498db"
                    )
                    progress.pack(side="left", padx=10)
                    progress.set(percentage / 100)

                    ctk.CTkLabel(
                        frame, text=str(count), width=40, font=ctk.CTkFont(size=11)
                    ).pack(side="left")

                total = sum(counts)
                avg = total / len(counts) if counts else 0

                info_frame = ctk.CTkFrame(self.timing_frame, fg_color="transparent")
                info_frame.pack(fill="x", pady=(10, 0))
                ctk.CTkLabel(
                    info_frame,
                    text=f"Total Sales: {total} | Avg per hour: {avg:.1f}",
                    font=ctk.CTkFont(size=11),
                    text_color="#3498db",
                ).pack()
            else:
                ctk.CTkLabel(
                    self.timing_frame,
                    text="No sales data available for this month",
                    font=ctk.CTkFont(size=14),
                ).pack(expand=True)

        except Exception as e:
            ctk.CTkLabel(
                self.timing_frame,
                text=f"Error loading data: {str(e)[:50]}",
                font=ctk.CTkFont(size=12),
                text_color="red",
            ).pack(expand=True)

    def refresh_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            # today_like_prefix used by repo query
            today_like_prefix = f"{today}%"
            sales_usd, sales_syp, trans_count = self.app.report_service.get_today_dashboard_metrics(
                today_like_prefix
            )

            self.rev_label.configure(text=f"${sales_usd:,.2f}")
            self.syp_label.configure(text=f"{sales_syp:,.0f} SYP")
            self.trans_label.configure(text=str(trans_count))

            self.load_best_selling_data()
            self.load_top_stock_data()
            self.load_sales_timing_data()

        except Exception:
            self.rev_label.configure(text="Error", text_color="#e74c3c")
            self.syp_label.configure(text="Error", text_color="#e74c3c")

    # ==========================================
    # Calculator & Exchange Rate (no UI SQL)
    # ==========================================
    def calculate(self, event=None):
        try:
            expr = self.calc_ent.get().strip()
            if not expr:
                return
            if "/" in expr and expr.count("/") > 1:
                raise ValueError("Invalid expression")

            res = safe_eval(expr)
            self.calc_res.configure(text=f"= {res:,.2f}")
            self.calc_ent.delete(0, "end")
        except Exception:
            self.calc_res.configure(text="Error", text_color="#e74c3c")
            self.calc_ent.after(
                2000,
                lambda: self.calc_res.configure(text="= 0.00", text_color="white"),
            )

    def update_ex_rate(self):
        try:
            val = float(self.ex_ent.get())
            if val <= 0:
                raise ValueError

            self.app.exchange_rate = val
            self.current_exchange_rate = val

            # Persist through SettingRepository
            self.app.setting_repo.set("exchange_rate", val)

            self.ex_lbl.configure(text=f"1 USD = {val:,.2f} SYP")
            self.ex_ent.delete(0, "end")

            messagebox.showinfo("Success", f"Exchange rate saved: {val:,.0f} SYP")

        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid positive number.")

    def open_print_dialog(self):
        """Open print dialog"""
        PrintDialog(self, self.app)

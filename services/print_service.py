# print_service.py

import tkinter as tk
from tkinter import messagebox, filedialog
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os


class PrintService:
    def __init__(self, app):
        self.app = app
        self.styles = getSampleStyleSheet()
        
        # Define custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            fontWeight='bold'
        )

    def print_inventory_report(self, products, include_costs=False, include_prices=True, include_stock=True):
        """
        Generate and print an inventory report
        
        Args:
            products: List of product dictionaries
            include_costs: Whether to include cost information
            include_prices: Whether to include price information
            include_stock: Whether to include stock information
        """
        try:
            # Prepare the file dialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Inventory Report As"
            )
            
            if not filename:
                return  # User cancelled
            
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            
            # Title
            title = Paragraph("Inventory Report", self.title_style)
            elements.append(title)
            
            # Report date
            date_paragraph = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal'])
            elements.append(date_paragraph)
            elements.append(Spacer(1, 12))
            
            # Prepare table data
            headers = ["ID", "Name"]
            if include_stock:
                headers.extend(["Stock", "Min Threshold"])
            if include_costs:
                headers.append("Cost ($)")
            if include_prices:
                headers.append("Price ($)")
            headers.append("Category")
            
            table_data = [headers]
            
            for product in products:
                row = [
                    str(product.get('id', '')),
                    product.get('name', '')
                ]
                
                if include_stock:
                    row.extend([
                        str(product.get('quantity', '')),
                        str(product.get('min_threshold', ''))
                    ])
                
                if include_costs:
                    row.append(f"${product.get('cost', 0):.2f}")
                
                if include_prices:
                    row.append(f"${product.get('price', 0):.2f}")
                
                row.append(product.get('category', ''))
                
                table_data.append(row)
            
            # Create table
            table = Table(table_data)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            messagebox.showinfo("Success", f"Inventory report saved to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate inventory report: {str(e)}")

    def print_sales_report(self, sales_data, period="All Time"):
        """
        Generate and print a sales report
        
        Args:
            sales_data: List of sales records
            period: Time period for the report
        """
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Sales Report As"
            )
            
            if not filename:
                return  # User cancelled
            
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            
            # Title
            title = Paragraph("Sales Report", self.title_style)
            elements.append(title)
            
            # Report details
            details = [
                f"Period: {period}",
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            for detail in details:
                elements.append(Paragraph(detail, self.styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Prepare table data
            headers = ["Invoice ID", "Date", "Customer", "Total ($)", "Method", "Status"]
            table_data = [headers]
            
            for sale in sales_data:
                if hasattr(sale, 'keys'):
                    # Dictionary format
                    table_data.append([
                        str(sale.get('id', '')),
                        sale.get('date', ''),
                        sale.get('partner_name', 'Walk-in'),
                        f"${sale.get('total', 0):.2f}",
                        sale.get('payment_method', ''),
                        sale.get('status', '')
                    ])
                else:
                    # Tuple format
                    table_data.append([
                        str(sale[0]),
                        sale[2],
                        sale[3] if sale[3] else "Walk-in",
                        f"${sale[4]:.2f}",
                        sale[5],
                        sale[6]
                    ])
            
            # Create table
            table = Table(table_data)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            messagebox.showinfo("Success", f"Sales report saved to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate sales report: {str(e)}")

    def print_purchase_report(self, purchase_data, period="All Time"):
        """
        Generate and print a purchase report
        
        Args:
            purchase_data: List of purchase records
            period: Time period for the report
        """
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Purchase Report As"
            )
            
            if not filename:
                return  # User cancelled
            
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            
            # Title
            title = Paragraph("Purchase Report", self.title_style)
            elements.append(title)
            
            # Report details
            details = [
                f"Period: {period}",
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ]
            
            for detail in details:
                elements.append(Paragraph(detail, self.styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Prepare table data
            headers = ["Invoice ID", "Date", "Supplier", "Total ($)", "Method", "Status"]
            table_data = [headers]
            
            for purchase in purchase_data:
                if hasattr(purchase, 'keys'):
                    # Dictionary format
                    table_data.append([
                        str(purchase.get('id', '')),
                        purchase.get('date', ''),
                        purchase.get('partner_name', 'Walk-in'),
                        f"${purchase.get('total', 0):.2f}",
                        purchase.get('payment_method', ''),
                        purchase.get('status', '')
                    ])
                else:
                    # Tuple format
                    table_data.append([
                        str(purchase[0]),
                        purchase[2],
                        purchase[3] if purchase[3] else "Walk-in",
                        f"${purchase[4]:.2f}",
                        purchase[5],
                        purchase[6]
                    ])
            
            # Create table
            table = Table(table_data)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            messagebox.showinfo("Success", f"Purchase report saved to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate purchase report: {str(e)}")

    def print_accounts_report(self, accounts, account_type="All"):
        """
        Generate and print an accounts report
        
        Args:
            accounts: List of account dictionaries
            account_type: Type of accounts (All, Customers, Suppliers)
        """
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Accounts Report As"
            )
            
            if not filename:
                return  # User cancelled
            
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            
            # Title
            title = Paragraph(f"{account_type} Report", self.title_style)
            elements.append(title)
            
            # Report details
            details = [
                f"Account Type: {account_type}",
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total Accounts: {len(accounts)}"
            ]
            
            for detail in details:
                elements.append(Paragraph(detail, self.styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Prepare table data
            headers = ["ID", "Name", "Phone", "Email", "Address", "Role", "Balance ($)"]
            table_data = [headers]
            
            for account in accounts:
                if hasattr(account, 'keys'):
                    # Dictionary format
                    table_data.append([
                        str(account.get('id', '')),
                        account.get('name', ''),
                        account.get('phone', ''),
                        account.get('email', ''),
                        account.get('address', ''),
                        account.get('role', ''),
                        f"${account.get('balance', 0):.2f}"
                    ])
                else:
                    # Tuple format (assuming the same order as in the database)
                    table_data.append([
                        str(account[0]),  # ID
                        account[1],       # Name
                        account[2] or '', # Phone
                        account[3] or '', # Email
                        account[4] or '', # Address
                        account[5],       # Role
                        f"${account[6]:.2f}" # Balance
                    ])
            
            # Create table
            table = Table(table_data)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            messagebox.showinfo("Success", f"Accounts report saved to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate accounts report: {str(e)}")

    def print_categories_report(self, categories, include_subcategories=True):
        """
        Generate and print a categories report
        
        Args:
            categories: List of category dictionaries
            include_subcategories: Whether to include subcategory hierarchy
        """
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Categories Report As"
            )
            
            if not filename:
                return  # User cancelled
            
            doc = SimpleDocTemplate(filename, pagesize=A4)
            elements = []
            
            # Title
            title = Paragraph("Categories Report", self.title_style)
            elements.append(title)
            
            # Report details
            details = [
                f"Include Subcategories: {include_subcategories}",
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total Categories: {len(categories)}"
            ]
            
            for detail in details:
                elements.append(Paragraph(detail, self.styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Prepare table data
            headers = ["ID", "Name", "Parent Category", "Path"]
            table_data = [headers]
            
            for category in categories:
                if hasattr(category, 'keys'):
                    # Dictionary format
                    parent_name = ""
                    if category.get('parent_id'):
                        # Try to find parent name in the categories list
                        parent_cat = next((cat for cat in categories if cat.get('id') == category['parent_id']), {})
                        parent_name = parent_cat.get('name', 'Unknown')
                    
                    table_data.append([
                        str(category.get('id', '')),
                        category.get('name', ''),
                        parent_name,
                        category.get('path', category.get('name', ''))
                    ])
                else:
                    # Tuple format
                    table_data.append([
                        str(category[0]),  # ID
                        category[1],       # Name
                        category[2] if category[2] else "",  # Parent ID (would need lookup)
                        category[3] if len(category) > 3 else category[1]  # Path
                    ])
            
            # Create table
            table = Table(table_data)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            messagebox.showinfo("Success", f"Categories report saved to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate categories report: {str(e)}")
# invoice_repo.py

import logging
from typing import Any, Dict, List, Optional, Sequence


class InvoiceRepository:
    """
    Repository for invoices + invoice_items.

    Design intent:
    - SQL only (no business rules)
    - Service/UI layers should handle validation and shape normalization
    """

    def __init__(self, conn):
        self.conn = conn

    # =========================
    # Writes
    # =========================
    def create_invoice(
        self,
        inv_type: str,
        partner_id: int,
        total_usd: float,
        total_syp: float = 0.0,
        exchange_rate: float = 1.0,
        tax: float = 0.0,
        discount: float = 0.0,
        payment_method: str = "Cash",
        status: str = "Completed",
    ) -> int:
        """
        Insert invoice row and return generated invoice id.

        Note: schema columns:
        - type, date, partner_id, total, total_syp, rate_at_time, tax, discount, payment_method, status
        """
        cursor = self.conn.execute(
            """
            INSERT INTO invoices
                (type, partner_id, total, total_syp, rate_at_time, tax, discount, payment_method, status)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inv_type,
                partner_id,
                total_usd,
                total_syp,
                exchange_rate,
                tax,
                discount,
                payment_method,
                status,
            ),
        )
        return cursor.lastrowid

    def add_invoice_item(
        self,
        invoice_id: int,
        product_id: int,
        quantity: int,
        price: float,
        item_discount: float = 0.0,
        price_syp: float = 0.0,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO invoice_items
                (invoice_id, product_id, quantity, price, item_discount, price_syp)
            VALUES
                (?, ?, ?, ?, ?, ?)
            """,
            (invoice_id, product_id, quantity, price, item_discount, price_syp),
        )

    # =========================
    # Reads
    # =========================
    def get_invoice_by_id(self, invoice_id: int):
        """
        Returns:
        - sqlite3.Row (dict-like if row_factory is configured)
        - or None if not found
        """
        return self.conn.execute(
            """
            SELECT i.*,
                   a.name AS partner_name
            FROM invoices i
            LEFT JOIN accounts a ON i.partner_id = a.id
            WHERE i.id = ?
            """,
            (invoice_id,),
        ).fetchone()

    def get_invoice_items(self, invoice_id: int):
        """
        Returns all items with product name + computed subtotal.
        """
        return self.conn.execute(
            """
            SELECT
                p.name AS name,
                ii.quantity,
                ii.price,
                (ii.quantity * ii.price) AS subtotal,
                ii.item_discount,
                ii.price_syp
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = ?
            """,
            (invoice_id,),
        ).fetchall()

    def get_all_invoices(
        self,
        where_clause: str = "",
        params: Sequence[Any] = (),
    ):
        """
        Generic invoice listing with optional WHERE clause.

        `where_clause` should include the leading keyword (e.g. "WHERE ...").
        """
        query = f"""
            SELECT i.*,
                   a.name AS partner_name
            FROM invoices i
            LEFT JOIN accounts a ON i.partner_id = a.id
            {where_clause}
            ORDER BY i.id DESC
        """
        return self.conn.execute(query, params).fetchall()

    def get_invoice_count(self, where_clause: str = "") -> int:
        """Count invoices matching the where clause."""
        query = f"SELECT COUNT(*) as count FROM invoices i {where_clause}"
        result = self.conn.execute(query).fetchone()
        return int(result[0]) if result and result[0] is not None else 0

    def get_invoice_total_sum(self, where_clause: str = "") -> float:
        """Sum invoices.total matching the where clause."""
        query = f"SELECT SUM(total) as total FROM invoices i {where_clause}"
        result = self.conn.execute(query).fetchone()
        if not result:
            return 0.0
        return float(result[0] or 0.0)

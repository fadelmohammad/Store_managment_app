# invoices_service.py
#
# Purpose:
# - Service layer wrapper around InvoiceRepository
# - Keeps UI/business logic away from raw SQL
#
# Notes:
# - This service is used by ReportingService for invoice reads.
# - ReportingService expects:
#   - get_invoices(period)
#   - get_invoice_details(invoice_id)
#   - get_invoice_summary(period)
#
# - POS/Sales/Purchases may use:
#   - create_invoice(data)
#   - add_invoice_item(...)

from __future__ import annotations

from typing import Any, Dict

from database.repositories.invoice_repo import InvoiceRepository


class InvoiceService:
    def __init__(self, conn):
        self.repo = InvoiceRepository(conn)

    # =========================
    # Writes (used by POS/Sales/Purchases)
    # =========================
    def create_invoice(self, data: Dict[str, Any]) -> int:
        """
        Backwards-compatible service method.

        Expected `data` keys:
        - type
        - partner_id
        - total_usd
        - total_syp (optional)
        - exchange_rate (optional)
        - tax (optional)
        - discount (optional)
        - payment_method (optional)
        - status (optional)
        """
        inv_type = data["type"]
        partner_id = int(data["partner_id"])
        total_usd = float(data["total_usd"])

        return self.repo.create_invoice(
            inv_type=inv_type,
            partner_id=partner_id,
            total_usd=total_usd,
            total_syp=float(data.get("total_syp", 0.0)),
            exchange_rate=float(data.get("exchange_rate", 1.0)),
            tax=float(data.get("tax", 0.0)),
            discount=float(data.get("discount", 0.0)),
            payment_method=str(data.get("payment_method", "Cash")),
            status=str(data.get("status", "Completed")),
        )

    def add_invoice_item(
        self,
        invoice_id: int,
        product_id: int,
        quantity: int,
        price: float,
        item_discount: float = 0.0,
        price_syp: float = 0.0,
    ) -> None:
        self.repo.add_invoice_item(
            invoice_id=invoice_id,
            product_id=product_id,
            quantity=quantity,
            price=price,
            item_discount=item_discount,
            price_syp=price_syp,
        )

    # =========================
    # Reads (used by ReportingService/UI)
    # =========================
    def _get_where_clause_from_period(self, period: str) -> str:
        """
        Must match InvoiceRepository#get_all_invoices expects a SQL fragment
        beginning with WHERE (or empty string for All Time).
        """
        if period == "Today":
            return "WHERE date >= date('now')"
        if period == "Last 7 Days":
            return "WHERE date >= date('now', '-7 days')"
        if period == "This Month":
            return "WHERE date >= date('now', 'start of month')"
        return ""

    def get_invoices(self, period: str = "All Time"):
        """
        Returns list[dict] of invoices for the UI.
        Normalizing to dict avoids UI dict-vs-tuple branching.
        """
        where_clause = self._get_where_clause_from_period(period)
        rows = self.repo.get_all_invoices(where_clause=where_clause) or []
        return [dict(r) if hasattr(r, "keys") else dict(zip(range(len(r)), r)) for r in rows]

    def get_invoice_details(self, invoice_id: int):
        """
        Returns (invoice_dict_or_None, items_list_of_dicts).
        Normalizing to dict avoids UI dict-vs-tuple branching.
        """
        invoice = self.repo.get_invoice_by_id(invoice_id)
        if not invoice:
            return None, None

        items = self.repo.get_invoice_items(invoice_id) or []

        invoice_dict = dict(invoice) if hasattr(invoice, "keys") else dict(zip(range(len(invoice)), invoice))
        items_dicts = [
            dict(item) if hasattr(item, "keys") else dict(zip(range(len(item)), item))
            for item in items
        ]
        return invoice_dict, items_dicts

    def get_invoice_summary(self, period: str = "All Time") -> Dict[str, Any]:
        """
        Returns dict:
        - count
        - total
        """
        where_clause = self._get_where_clause_from_period(period)
        return {
            "count": self.repo.get_invoice_count(where_clause=where_clause),
            "total": self.repo.get_invoice_total_sum(where_clause=where_clause),
        }

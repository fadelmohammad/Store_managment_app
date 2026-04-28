# invoices_service.py

class InvoiceService:

    def __init__(self, conn):

        self.conn = conn

    def create_invoice(self, data):

import logging
from typing import Dict, List, Optional


class PaymentService:
    def __init__(self, payment_repo, account_repo):
        self.payment_repo = payment_repo
        self.account_repo = account_repo

    def add_payment(self, account_id: int, amount: float, payment_type: str, 
                   payment_method: str = None, reference_number: str = None, 
                   notes: str = None, created_by: int = None) -> int:
        """Add a payment and update the account balance accordingly."""
        # Validate inputs
        if not account_id:
            raise ValueError("Account ID is required")
        
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
            
        if payment_type not in ["Payment In", "Payment Out", "Adjustment"]:
            raise ValueError("Payment type must be 'Payment In', 'Payment Out', or 'Adjustment'")
        
        # Get the current account to validate it exists
        account = self.account_repo.get_by_id(account_id)
        if not account:
            raise ValueError("Account not found")
        account = dict(account)

        # Add the payment record
        payment_id = self.payment_repo.add_payment(
            account_id, amount, payment_type, payment_method, reference_number, notes, created_by
        )
        
        # Update account balance based on payment type
        current_balance = float(account.get("balance", 0.0))
        if payment_type == "Payment In":
            new_balance = current_balance + amount
        elif payment_type == "Payment Out":
            new_balance = current_balance - amount
        elif payment_type == "Adjustment":
            # For adjustments, amount can be positive or negative
            new_balance = current_balance + amount
        
        # Update the account balance
        self.account_repo.update(account_id, {
            'name': account['name'],
            'role': account['role'],
            'phone': account['phone'],
            'email': account['email'],
            'address': account['address'],
            'balance': new_balance
        })
        
        return payment_id

    def get_payments_for_account(self, account_id: int, limit: int = None) -> List[Dict]:
        """Get all payments for a specific account."""
        if not account_id:
            raise ValueError("Account ID is required")
            
        return self.payment_repo.get_payments_by_account(account_id, limit)

    def get_payment_history(self, account_id: int, limit: int = 50) -> List[Dict]:
        """Get payment history for an account with both payments and invoice records."""
        if not account_id:
            raise ValueError("Account ID is required")
        
        # Get payments for this account
        payments = self.payment_repo.get_payments_by_account(account_id, limit)
        
        # Get invoices for this account (for complete transaction history)
        from .invoices_service import InvoiceService  # Import here to avoid circular dependency
        # We'll get invoices separately since they're stored in a different repository
        
        # Format the payments with additional info
        for payment in payments:
            payment['transaction_type'] = 'Payment'
            payment['formatted_amount'] = f"${payment['amount']:,.2f}"
            if payment['payment_type'] == 'Payment In':
                payment['direction'] = '+'
            elif payment['payment_type'] == 'Payment Out':
                payment['direction'] = '-'
            else:
                payment['direction'] = '+' if payment['amount'] >= 0 else '-'
        
        return payments

    def get_payment_by_id(self, payment_id: int) -> Optional[Dict]:
        """Get a specific payment by ID."""
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if payment:
            payment = dict(payment)
            payment['formatted_amount'] = f"${payment['amount']:,.2f}"
        return payment

    def delete_payment(self, payment_id: int, account_id: int) -> None:
        """Delete a payment and adjust account balance accordingly."""
        payment = self.payment_repo.get_payment_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        if payment['account_id'] != account_id:
            raise ValueError("Payment does not belong to the specified account")
        
        # Get the account to revert the balance
        account = self.account_repo.get_by_id(account_id)
        if not account:
            raise ValueError("Account not found")
        account = dict(account)
        
        # Revert the account balance based on the payment type
        current_balance = float(account.get("balance", 0.0))
        amount = float(payment['amount'])
        
        if payment['payment_type'] == 'Payment In':
            new_balance = current_balance - amount
        elif payment['payment_type'] == 'Payment Out':
            new_balance = current_balance + amount
        elif payment['payment_type'] == 'Adjustment':
            # For adjustments, we subtract the amount to reverse the adjustment
            new_balance = current_balance - amount
        
        # Update the account balance
        self.account_repo.update(account_id, {
            'name': account['name'],
            'role': account['role'],
            'phone': account['phone'],
            'email': account['email'],
            'address': account['address'],
            'balance': new_balance
        })
        
        # Delete the payment record
        self.payment_repo.delete_payment(payment_id)
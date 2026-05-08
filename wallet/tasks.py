from celery import shared_task
from django.db import transaction
import time
from .models import Transaction

@shared_task
def send_transfer_receipt(transaction_id):
    """
    Simulates sending an email receipt
    """
    try:
        tx = Transaction.objects.get(id=transaction_id)
        print(f"Async Task: Sending receipt for {tx.amount} to {tx.receiver}")
        return True
    except Transaction.DoesNotExist:
        return False

@shared_task
def process_bank_withdrawal(transaction_id):
    """
    Simulates communication with a banking network (ACH/Swift)
    """
    time.sleep(3)
    try:
        with transaction.atomic():
            # Lock the transaction to update its status safely
            tx = Transaction.objects.select_for_update().get(id=transaction_id)

            if tx.status == Transaction.TransactionStatus.PENDING:
                tx.status = Transaction.TransactionStatus.COMPLETED
                tx.save()
                print(f"Async task: Withdrawal {transaction_id} Completed successfully")
        
        return True

    except Transaction.DoesNotExist:
        return False
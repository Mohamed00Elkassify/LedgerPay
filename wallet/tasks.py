from celery import shared_task
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


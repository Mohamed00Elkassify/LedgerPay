import stripe
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from users.models import User
from .models import Wallet, Transaction, LedgerEntry
from .tasks import send_transfer_receipt

stripe.api_key = settings.STRIPE_SECRET_KEY

class WalletService:
    @staticmethod
    @transaction.atomic
    def transfer_funds(sender_user, receiver_username, amount, idempotency_key=None):
        # Idempotency Check
        if idempotency_key:
            existing_tx = Transaction.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            if existing_tx:
                return existing_tx
        
        try:
            receiver_user = User.objects.get(username=receiver_username)
        except User.DoesNotExist:
            raise ValidationError("Receiver user does not exist")
        
        if sender_user == receiver_user:
            raise ValidationError("Cannot transfer funds to yourself")
        
        # Deadlock prevention : Lock wallets in a consistent order(UUID)
        wallets = Wallet.objects.filter(
            user__in=[sender_user, receiver_user]
        ).select_for_update()

        wallet_dict = {w.user_id : w for w in wallets}
        sender_wallet = wallet_dict.get(sender_user.id)
        receiver_wallet = wallet_dict.get(receiver_user.id)

        if not sender_wallet or not receiver_wallet:
            raise ValidationError("One or both users do not have a wallet")
        
        # check balance
        if sender_wallet.balance < amount:
            raise ValidationError("Insufficient funds")

        # create transaction record
        tx = Transaction.objects.create(
            sender=sender_user, 
            receiver=receiver_user,
            amount=amount,
            transaction_type=Transaction.TransactionType.TRANSFER,
            status=Transaction.TransactionStatus.COMPLETED,
            idempotency_key=idempotency_key
        )

        # create Ledger Entries
        LedgerEntry.objects.create(
            transaction=tx,
            wallet=sender_wallet,
            amount=-amount
        )
        LedgerEntry.objects.create(
            transaction=tx,
            wallet=receiver_wallet,
            amount=amount
        )

        # update balances
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount
        sender_wallet.save()
        receiver_wallet.save()

        # Trigger async receipt sending
        send_transfer_receipt.delay(tx.id)

        return tx
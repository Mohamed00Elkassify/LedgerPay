from rest_framework import serializers
from .models import Wallet, Transaction

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'currency']

class TransactionSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()
    receiver = serializers.StringRelatedField()

    class Meta:
        model = Transaction
        fields = ['id', 'sender', 'receiver', 'amount', 'transaction_type', 'status', 'created_at']

class TransferInputSerializer(serializers.Serializer):
    receiver_name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    idempotency_key = serializers.CharField(required=False)

class DepositInputSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1.00)

class WithdrawalInputSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=5.00)
    bank_account_id = serializers.CharField(max_length=255) # the id of the user's bank account where the money should be sent 

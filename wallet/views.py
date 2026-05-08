from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .serializers import WalletSerializer, TransactionSerializer, TransferInputSerializer, DepositInputSerializer
from .models import LedgerEntry
from .services import WalletService

class WalletBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Endpoint: /api/wallet/balance/
        Purpose: Get current available funds.
        Focus: Aggregating ledger entries securely.
        """
        #serializer = WalletSerializer(request.user.wallet)
        #return Response(serializer.data)

        wallet = request.user.wallet
        # Aggregating ledger entries for security and audit integrity
        ledger_balance = LedgerEntry.objects.filter(
            wallet=wallet
        ).aggregate(
            total_balance=Sum('amount')
        )['total_balance'] or 0

        return Response({
            "balance": f"{ledger_balance:.2f}",
            "currency": wallet.currency,
            "wallet_id": wallet.id
        })

class TransferView(APIView):
    """
    Endpoint: /api/transfers/
    Purpose: P2P money transfer
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tx = WalletService.transfer_funds(
                sender_user=request.user,
                receiver_username=serializer.validated_data['receiver_name'],
                amount=serializer.validated_data['amount'],
                idempotency_key=serializer.validated_data.get('idempotency_key')
            )
            return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({"error" : str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DepositView(APIView):
    """
    Endpoint: /api/funding/deposit/
    Purpose: Create StripeIntent
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            intent = WalletService.create_stripe_payment_intent(
                user = request.user,
                amount = serializer.validated_data['amount']
            )
            return Response({
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error" : str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StripeWebhookView(APIView):
    """
    Endpoint: /api/webhooks/stripe/
    Purpose: Stripe async success fallback
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            WalletService.handle_stripe_webhook(payload, sig_header)
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error" : str(e)}, status=status.HTTP_400_BAD_REQUEST)


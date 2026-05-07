from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum
from .serializers import WalletSerializer
from .models import LedgerEntry

class WalletBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Endpoint: /api/wallet/balance/
        Purpose: Get current available funds.
        Senior Engineering Focus: Aggregating ledger entries securely.
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
from django.urls import path
from .views import WalletBalanceView, TransferView, DepositView, StripeWebhookView, WithdrawalView, TransactionDetailView, TransactionHistoryView

urlpatterns = [
    path('wallet/balance/', WalletBalanceView.as_view(), name='wallet-balance'),
    path('wallet/history/', TransactionHistoryView.as_view(), name='transaction-history'),
    path('transaction/<uuid:id>/', TransactionDetailView.as_view(), name='transaction-detail'),
    path('transfers/', TransferView.as_view(), name='transfer-funds'),
    path('funding/deposit/', DepositView.as_view(), name='deposit-funds'),
    path('webhooks/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('wallet/withdraw/', WithdrawalView.as_view(), name='withdraw-funds'),
]
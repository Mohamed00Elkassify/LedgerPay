from django.urls import path
from .views import WalletBalanceView, TransferView, DepositView, StripeWebhookView

urlpatterns = [
    path('wallet/balance/', WalletBalanceView.as_view(), name='wallet-balance'),
    path('transfers/', TransferView.as_view(), name='transfer-funds'),
    path('funding/deposit/', DepositView.as_view(), name='deposit-funds'),
    path('webhooks/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
]
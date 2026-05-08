from django.urls import path
from .views import WalletBalanceView, TransferView

urlpatterns = [
    path('wallet/balance/', WalletBalanceView.as_view(), name='wallet-balance'),
    path('transfers/', TransferView.as_view(), name='transfer-funds'),
]
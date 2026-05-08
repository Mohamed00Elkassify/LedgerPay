from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User
from .models import Wallet, LedgerEntry, Transaction

class WalletTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password123')
        
        self.wallet1 = Wallet.objects.create(user=self.user1, balance=Decimal('100.00'), currency='USD')
        self.wallet2 = Wallet.objects.create(user=self.user2, balance=Decimal('50.00'), currency='USD')
        
        # Add initial ledger entry for user1 to match balance (since BalanceView aggregates ledger)
        self.tx_init = Transaction.objects.create(
            receiver=self.user1,
            amount=Decimal('100.00'),
            transaction_type=Transaction.TransactionType.DEPOSIT,
            status=Transaction.TransactionStatus.COMPLETED
        )
        LedgerEntry.objects.create(transaction=self.tx_init, wallet=self.wallet1, amount=Decimal('100.00'))

    def test_wallet_balance_view(self):
        """Test that authenticated user can retrieve their balance aggregated from ledger."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('wallet-balance')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], '100.00')
        # Convert UUID to string for comparison as response data might contain UUID object in test client
        self.assertEqual(str(response.data['wallet_id']), str(self.wallet1.id))

    def test_wallet_balance_view_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        url = reverse('wallet-balance')
        response = self.client.get(url)
        # DRF returns 401 Unauthorized for IsAuthenticated if no authentication is provided
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_transfer_funds_success(self):
        """Test a successful P2P transfer between two users."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('transfer-funds')
        data = {
            'receiver_name': 'user2',
            'amount': '30.00'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed with: {response.data}")
        self.wallet1.refresh_from_db()
        self.wallet2.refresh_from_db()
        self.assertEqual(self.wallet1.balance, Decimal('70.00'))
        self.assertEqual(self.wallet2.balance, Decimal('80.00'))

    def test_transfer_funds_insufficient_balance(self):
        """Test that transfer fails when sender has insufficient funds."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('transfer-funds')
        data = {
            'receiver_name': 'user2',
            'amount': '150.00'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient funds', str(response.data['error']))

    def test_transfer_funds_to_self(self):
        """Test that users cannot transfer funds to themselves."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('transfer-funds')
        data = {
            'receiver_name': 'user1',
            'amount': '10.00'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot transfer funds to yourself', str(response.data['error']))

    def test_transfer_funds_receiver_not_found(self):
        """Test that transfer fails when receiver username does not exist."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('transfer-funds')
        data = {
            'receiver_name': 'nonexistent',
            'amount': '10.00'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Receiver user does not exist', str(response.data['error']))

    def test_transfer_funds_idempotency(self):
        """Test that duplicate requests with the same idempotency key do not cause double spending."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('transfer-funds')
        data = {
            'receiver_name': 'user2',
            'amount': '10.00',
            'idempotency_key': 'unique-key-123'
        }
        # First call
        response1 = self.client.post(url, data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED, f"First call failed: {response1.data}")
        
        # Second call with same key
        response2 = self.client.post(url, data)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED, f"Second call failed: {response2.data}")
        self.assertEqual(response1.data['id'], response2.data['id'])
        
        self.wallet1.refresh_from_db()
        self.assertEqual(self.wallet1.balance, Decimal('90.00')) # Only one transfer should have been processed

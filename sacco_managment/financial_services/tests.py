from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from financial_services.models import CryptoWallet, CryptoTransaction
from django.contrib.auth import get_user_model

User = get_user_model()

class FinancialServicesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_password = 'testpass123'
        self.user = User.objects.create_user(
            username='testuser', 
            email='testuser@example.com',
            password=self.user_password
        )
        # Now login correctly using the created credentials
        login_success = self.client.login(username='testuser', password=self.user_password)
        self.assertTrue(login_success, "Login failed in test setup")

        self.wallet = CryptoWallet.objects.create(
            user=self.user,
            wallet_type='BTC',
            balance=Decimal('1.00000000')
        )

        self.transaction = CryptoTransaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('0.50000000'),
            transaction_type='DEPOSIT',
            status='COMPLETED',
            timestamp=timezone.now(),
            description="Initial deposit"
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('financial_services:crypto_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Initial deposit")

    def test_create_transaction_get(self):
        response = self.client.get(reverse('financial_services:create_transaction'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_transaction_detail(self):
        response = self.client.get(reverse('financial_services:transaction_detail', args=[self.transaction.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Initial deposit")

    def test_transaction_history_no_filters(self):
        response = self.client.get(reverse('financial_services:transaction_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Initial deposit")

    def test_generate_report(self):
        response = self.client.get(reverse('financial_services:generate_report'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="crypto_report', response['Content-Disposition'])
        self.assertIn("Initial deposit", response.content.decode())

    def test_wallet_detail(self):
        response = self.client.get(reverse('financial_services:wallet_detail', args=[self.wallet.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Initial deposit")

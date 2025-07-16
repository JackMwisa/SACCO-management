from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Transaction
from account.models import Account

User = get_user_model()

class BasicViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_dashboard_redirects_logged_user(self):
        response = self.client.get(reverse('account:dashboard'))
        self.assertEqual(response.status_code, 200)


class PaymentRequestTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='jack', password='pass1234')
        self.account = self.user.account
        self.account.account_number = '12345678'
        self.account.pin_number = '1234'
        self.account.save()
        self.client.login(username='jack', password='pass1234')

    def test_payment_request_flow(self):
        response = self.client.post(
            reverse('core:amount-request-process', args=[self.account.account_number]),
            {
                'amount-request': '5000',
                'description': 'Test payment',
            }
        )
        self.assertEqual(response.status_code, 302)
        transaction = Transaction.objects.last()

        response = self.client.post(
            reverse('core:amount-request-final-process', args=[self.account.account_number, transaction.transaction_id]),
            {'pin-number': '1234'}
        )
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'request_sent')

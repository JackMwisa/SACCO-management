from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from account.models import (
    Account, KYC, StaffPermission, AuditLog, LoginHistory
)

import tempfile

User = get_user_model()

class AccountModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='member', password='pass1234', role='MEMBER')
        self.staff = User.objects.create_user(username='staff', password='staffpass', role='STAFF')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com', role='ADMIN')

    def test_account_created_with_user(self):
        self.assertTrue(hasattr(self.user, 'account'))
        self.assertIsInstance(self.user.account, Account)

    def test_available_balance_calculation(self):
        account = self.user.account
        account.account_balance = 1000
        account.mobile_money_balance = 500
        account.locked_funds = 300
        account.save()
        self.assertEqual(account.available_balance, 1200)

    def test_staff_permission_created_for_staff_user(self):
        self.assertTrue(hasattr(self.staff, 'staff_permissions'))
        self.assertEqual(self.staff.staff_permissions.role, 'SUPPORT')

    def test_kyc_submission(self):
        account = self.user.account
        file = SimpleUploadedFile("id.jpg", b"dummyimagecontent")
        kyc = KYC.objects.create(
            user=self.user,
            account=account,
            full_name="Test User",
            image=file,
            marrital_status="single",
            gender="male",
            identity_type="national_id_card",
            identity_image=file,
            date_of_birth="1995-01-01",
            signature=file,
            country="Uganda",
            state="Central",
            city="Kampala",
            mobile="0700000000",
            fax="N/A",
            kyc_confirmed=True
        )
        self.assertEqual(str(kyc), f"KYC for {self.user.username}")

    def test_audit_log_creation(self):
        AuditLog.objects.create(
            user=self.user,
            action='LOGIN',
            details='User logged in',
            ip_address='127.0.0.1'
        )
        log = AuditLog.objects.last()
        self.assertEqual(log.action, 'LOGIN')
        self.assertEqual(str(log), f"User Login by {self.user} at {log.timestamp}")

    def test_login_history_log(self):
        LoginHistory.objects.create(
            user=self.user,
            action='LOGIN',
            ip_address='127.0.0.1',
            user_agent='TestAgent',
            successful=True,
            location='Kampala'
        )
        history = LoginHistory.objects.last()
        self.assertEqual(history.action, 'LOGIN')
        self.assertEqual(history.user, self.user)

class AccountViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='member', password='pass1234', role='MEMBER')
        self.staff = User.objects.create_user(username='staff', password='staffpass', role='STAFF')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass', email='admin@example.com', role='ADMIN')

        # Confirm KYC
        account = self.user.account
        account.kyc_submitted = True
        account.kyc_confirmed = True
        account.save()

    def test_dashboard_redirect_for_anonymous(self):
        response = self.client.get(reverse("account:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_access_with_kyc(self):
        self.client.login(username='member', password='pass1234')
        response = self.client.get(reverse("account:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/dashboard.html")

    def test_staff_dashboard_access(self):
        self.client.login(username='staff', password='staffpass')
        response = self.client.get(reverse("account:staff_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_admin_dashboard_access(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse("account:admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_member_access_to_admin_dashboard_forbidden(self):
        self.client.login(username='member', password='pass1234')
        response = self.client.get(reverse("account:admin_dashboard"))
        self.assertEqual(response.status_code, 403)

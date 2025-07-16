from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from user_auths.models import User
from core.models import Transaction
from reports.models import FinancialReport

class ReportGenerationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", email="tester@example.com", password="pass12345")
        self.client.login(username="tester", password="pass12345")
        self.url = reverse("reports:generate_report")

        self.transaction = Transaction.objects.create(
            user=self.user,
            transaction_type="deposit",
            amount=100000,
            status="successful",
            date=timezone.now(),
            description="Test deposit"
        )

    def test_generate_report_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/generate_report.html")

    def test_generate_pdf_report(self):
        response = self.client.post(self.url, {
            "start_date": timezone.now().date(),
            "end_date": timezone.now().date(),
            "format": "PDF"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment; filename=", response["Content-Disposition"])
        self.assertTrue(FinancialReport.objects.filter(user=self.user, format="PDF").exists())

    def test_generate_excel_report(self):
        response = self.client.post(self.url, {
            "start_date": timezone.now().date(),
            "end_date": timezone.now().date(),
            "format": "EXCEL"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertTrue(FinancialReport.objects.filter(user=self.user, format="EXCEL").exists())

    def test_generate_csv_report(self):
        response = self.client.post(self.url, {
            "start_date": timezone.now().date(),
            "end_date": timezone.now().date(),
            "format": "CSV"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertTrue(FinancialReport.objects.filter(user=self.user, format="CSV").exists())

    def test_report_history_view(self):
        FinancialReport.objects.create(
            user=self.user,
            report_type="Transaction Report",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            format="PDF"
        )
        response = self.client.get(reverse("reports:report_history"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/history.html")

    def test_delete_report(self):
        report = FinancialReport.objects.create(
            user=self.user,
            report_type="Transaction Report",
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            format="PDF"
        )
        response = self.client.post(reverse("reports:delete_report", args=[report.id]))
        self.assertRedirects(response, reverse("reports:report_history"))
        self.assertFalse(FinancialReport.objects.filter(id=report.id).exists())

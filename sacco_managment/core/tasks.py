from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import LoanApplication
from core.models import Notification

@shared_task
def create_repayment_reminders(loan_id):
    loan = LoanApplication.objects.get(id=loan_id)
    today = timezone.now().date()
    
    for month in range(1, loan.duration_months + 1):
        due_date = loan.date_disbursed + timedelta(days=30*month)
        
        # Create notification 3 days before due date
        reminder_date = due_date - timedelta(days=3)
        if reminder_date > today:
            Notification.objects.create(
                user=loan.user,
                notification_type="Repayment Reminder",
                amount=loan.monthly_repayment,
                message=f"Your loan payment of UGX {loan.monthly_repayment:,.0f} is due on {due_date.strftime('%d %b %Y')}",
                scheduled_date=reminder_date
            )
        
        # Create overdue notification if payment not made
        overdue_date = due_date + timedelta(days=7)
        if overdue_date > today:
            Notification.objects.create(
                user=loan.user,
                notification_type="Payment Overdue",
                amount=loan.monthly_repayment,
                message=f"Your loan payment of UGX {loan.monthly_repayment:,.0f} is overdue",
                scheduled_date=overdue_date
            )
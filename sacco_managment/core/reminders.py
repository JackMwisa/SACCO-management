from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import LoanApplication, Notification

def send_payment_reminders():
    """
    Send payment reminders for upcoming and overdue payments
    Runs daily via cron job or celery task
    """
    today = timezone.now().date()
    
    # Get all active loans
    active_loans = LoanApplication.objects.filter(
        status__in=['approved', 'disbursed']
    ).select_related('user')
    
    for loan in active_loans:
        next_payment_date = calculate_next_payment_date(loan)
        if not next_payment_date:
            continue
            
        days_until_due = (next_payment_date - today).days
        total_paid = loan.repayments.aggregate(Sum('amount'))['amount__sum'] or 0
        remaining_balance = loan.total_repayment - total_paid
        
        # Skip if loan is already paid
        if remaining_balance <= 0:
            continue
            
        # Determine reminder type based on days until due
        if days_until_due == 3:
            send_reminder(loan, 'upcoming', days_until_due)
        elif days_until_due == 1:
            send_reminder(loan, 'due_tomorrow', days_until_due)
        elif days_until_due == 0:
            send_reminder(loan, 'due_today', days_until_due)
        elif days_until_due < 0:
            send_reminder(loan, 'overdue', abs(days_until_due))

def send_reminder(loan, reminder_type, days):
    """
    Send a reminder notification and email
    """
    context = {
        'loan': loan,
        'days': days,
        'next_payment_date': calculate_next_payment_date(loan),
        'amount_due': loan.monthly_repayment,
        'user': loan.user
    }
    
    # Create notification
    if reminder_type == 'upcoming':
        message = f"Reminder: Your loan payment of UGX {loan.monthly_repayment:,.2f} is due in {days} days"
    elif reminder_type == 'due_tomorrow':
        message = f"Reminder: Your loan payment of UGX {loan.monthly_repayment:,.2f} is due tomorrow"
    elif reminder_type == 'due_today':
        message = f"Reminder: Your loan payment of UGX {loan.monthly_repayment:,.2f} is due today"
    else:  # overdue
        message = f"Urgent: Your loan payment of UGX {loan.monthly_repayment:,.2f} is {days} days overdue"
    
    Notification.objects.create(
        user=loan.user,
        notification_type="Payment Reminder",
        amount=loan.monthly_repayment,
        message=message
    )
    
    # Send email
    subject = f"Loan Payment Reminder - {reminder_type.replace('_', ' ').title()}"
    html_message = render_to_string('emails/payment_reminder.html', context)
    send_mail(
        subject=subject,
        message="",  # Text version will be auto-generated from HTML
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[loan.user.email],
        fail_silently=True
    )
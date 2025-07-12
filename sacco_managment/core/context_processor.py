from core.models import Notification, LoanApplication, Transaction
from .models import Loan
from django.db.models import Q


def default(request):
    notifications = None

    if request.user.is_authenticated:  # ✅ Check if user is logged in
        if Notification.objects.filter(user=request.user).exists():  # ✅ Avoid errors if no notifications exist
            notifications = Notification.objects.filter(user=request.user).order_by("-date")[:10]

    return {
        "notifications": notifications,  
    }

def active_loan(request):
    if request.user.is_authenticated:
        active_loan = Loan.objects.filter(user=request.user, status='active').first()
        return {'active_loan': LoanApplication.objects.filter(
            user=request.user, 
            status='active'
        ).first()}
    return {}



def unprocessed_withdrawals(request):
    if request.user.is_authenticated and request.user.is_staff:
        count = Transaction.objects.filter(
            transaction_type='mobile_money_withdrawal',
            status='pending'
        ).count()
        return {'withdrawal_requests_count': count}
    return {}



def default(request):
    context = {}
    if request.user.is_authenticated:
        # Notifications
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by("-date")[:10]
        context["notifications"] = notifications if notifications.exists() else None
        
        # Active Loan (for authenticated users)
        active_loan = LoanApplication.objects.filter(
            user=request.user,
            status__in=['approved', 'disbursed', 'active']  # Include all possible "active" statuses
        ).first()
        context["active_loan"] = active_loan
        
    return context

def unprocessed_withdrawals(request):
    context = {}
    if request.user.is_authenticated and request.user.is_staff:
        count = Transaction.objects.filter(
            transaction_type='mobile_money_withdrawal',
            status='pending'
        ).count()
        context['withdrawal_requests_count'] = count
    return context



def loan_context(request):
    context = {}
    if request.user.is_authenticated:
        # Active Loan (using Q objects for complex queries)
        active_loan = LoanApplication.objects.filter(
            Q(user=request.user),
            Q(status='approved') | Q(status='disbursed') | Q(status='active')
        ).select_related('user', 'account').first()
        
        context['active_loan'] = active_loan
        
        # Notifications (optimized query)
        context['notifications'] = Notification.objects.filter(
            user=request.user
        ).order_by("-date")[:10]
        
        # Staff-specific data
        if request.user.is_staff:
            context['withdrawal_requests_count'] = Transaction.objects.filter(
                transaction_type='mobile_money_withdrawal',
                status='pending'
            ).count()
            
    return context
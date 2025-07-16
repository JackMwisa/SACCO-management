from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.http.response import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from .models import LoanApplication, LoanRepayment, Notification, Transaction, LOAN_TYPES, LOAN_STATUS
from account.models import Account
from .forms import LoanApplicationForm
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from .models import MobileMoneyTransaction
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
import json
from .forms import MobileMoneyDepositForm, MobileMoneyWithdrawalForm
from core.models import MobileMoneyTransaction
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from django import forms
from django.urls import reverse
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from django.db import transaction


def index(request):
    if request.user.is_authenticated:
        return redirect("account:account")
    return render(request, "core/index.html")

def contact(request):
    return render(request, "core/contact.html")

def about(request):
    return render(request, "core/about.html")

@login_required
def apply_for_loan(request):
    account = request.user.account

    # Check eligibility
    eligibility = {
        'has_min_savings': account.account_balance >= 50000,
        'is_member_long_enough': (timezone.now() - request.user.date_joined).days > 90,
        'has_no_defaulted_loans': not LoanApplication.objects.filter(
            user=request.user, status='defaulted').exists(),
        'active_loans': LoanApplication.objects.filter(
            user=request.user, status__in=['approved', 'disbursed']).count()
    }

    if request.method == 'POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    loan = form.save(commit=False)
                    loan.user = request.user
                    loan.account = account
                    loan.interest_rate = 10.0  # Flat 10% interest
                    # Removed: loan.calculate_repayments()

                    # Auto-approve small loans (up to 3x savings)
                    if loan.amount <= account.account_balance * 3 and all(eligibility.values()):
                        loan.status = 'approved'
                        loan.date_approved = timezone.now()
                        messages.success(request, "Loan pre-approved pending final review!")
                    else:
                        loan.status = 'pending'
                        messages.success(request, "Loan application submitted for review!")

                    loan.save()

                    # Notify admin
                    Notification.objects.create(
                        user=request.user,
                        notification_type="Loan Application",
                        amount=loan.amount,
                        message=f"New loan application for UGX {loan.amount:,}"
                    )

                    return redirect('core:loan-status')
            except Exception as e:
                messages.error(request, f"Error submitting application: {str(e)}")
    else:
        form = LoanApplicationForm()

    context = {
        'form': form,
        'eligibility': eligibility,
        'savings_balance': account.account_balance,
        'max_auto_approval': account.account_balance * 3,
    }
    return render(request, 'loan/apply.html', context)

@login_required
def loan_status(request):
    loans = LoanApplication.objects.filter(user=request.user).order_by('-date_applied')

    # Calculate repayment progress for each loan
    for loan in loans:
        loan.total_paid = loan.repayments.aggregate(Sum('amount'))['amount__sum'] or 0
        loan.remaining_balance = loan.total_repayment - loan.total_paid
        loan.progress = min(100, (loan.total_paid / loan.total_repayment * 100)) if loan.total_repayment else 0

    context = {
        'loans': loans,
        'active_loan': loans.filter(status__in=['approved', 'disbursed']).first()
    }
    return render(request, 'loan/status.html', context)

@login_required
def loan_detail(request, loan_id):
    loan = get_object_or_404(LoanApplication, id=loan_id, user=request.user)
    repayments = loan.repayments.all().order_by('-payment_date')[:5]  # Get last 5 payments
    total_paid = repayments.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = round(loan.total_repayment - total_paid, 2)  # Round to 2 decimal places

    context = {
        'loan': loan,
        'repayments': repayments,
        'total_paid': total_paid,
        'balance': balance,
        'next_payment': calculate_next_payment_date(loan),
        'suggested_amount': min(loan.monthly_repayment, balance) if balance > 0 else 0
    }
    return render(request, 'loan/detail.html', context)

@login_required
def repay_loan(request, loan_id):
    loan = get_object_or_404(LoanApplication, id=loan_id, user=request.user)
    account = request.user.account  # Get the user's account

    if loan.status not in ['approved', 'disbursed']:
        messages.error(request, "This loan is not currently active for repayment")
        return redirect('core:loan-status')

    total_paid = loan.repayments.aggregate(Sum('amount'))['amount__sum'] or 0
    remaining_balance = round(loan.total_repayment - total_paid, 2)

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
            payment_method = request.POST.get('payment_method')

            if amount <= 0:
                raise ValidationError("Amount must be greater than zero")

            if amount > remaining_balance:
                raise ValidationError(f"Amount cannot exceed remaining balance of UGX {remaining_balance:,.2f}")

            with db_transaction.atomic():  # Ensure all operations succeed or fail together
                # Process payment based on method
                if payment_method == 'wallet':
                    if account.account_balance < amount:
                        raise ValidationError("Insufficient funds in your wallet")

                    # DEDUCT FROM ACCOUNT - THIS WAS MISSING
                    account.account_balance -= amount
                    account.save()  # MUST save the changes
                    payment_status = 'completed'
                else:
                    payment_status = 'pending'

                # Create transaction record
                transaction = Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transaction_type="loan_repayment",
                    status=payment_status,
                    description=f"Loan repayment via {payment_method}",
                    sender=request.user,
                    receiver=None,  # System account
                    sender_account=account,
                    receiver_account=None  # System account
                )

                # Create repayment record
                repayment = LoanRepayment.objects.create(
                    loan=loan,
                    amount=amount,
                    payment_method=payment_method,
                    transaction=transaction,
                    is_paid=(payment_status == 'completed')
                )

                # Create notification
                Notification.objects.create(
                    user=request.user,
                    notification_type="Loan Payment",
                    amount=amount,
                    message=f"Payment of UGX {amount:,.2f} received for your {loan.get_loan_type_display()} loan"
                )

                # Check if loan is fully paid
                new_total_paid = loan.repayments.aggregate(Sum('amount'))['amount__sum'] or 0
                if new_total_paid >= loan.total_repayment:
                    loan.status = 'completed'
                    loan.date_completed = timezone.now()
                    loan.save()
                    messages.success(request, "Congratulations! Your loan has been fully repaid!")
                else:
                    messages.success(request, f"Payment of UGX {amount:,.2f} received successfully")

                return redirect('core:loan-detail', loan_id=loan.id)

        except Exception as e:
            messages.error(request, f"Payment failed: {str(e)}")

    # Calculate suggested amount (either monthly payment or remaining balance)
    suggested_amount = min(loan.monthly_repayment, remaining_balance) if remaining_balance > 0 else 0

    return render(request, 'loan/repay.html', {
        'loan': loan,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'suggested_amount': suggested_amount,
        'next_payment': calculate_next_payment_date(loan),
        'payment_percentage': round((total_paid / loan.total_repayment * 100), 2) if loan.total_repayment > 0 else 0,
        'current_date': timezone.now().date()
    })


def process_loan_repayment(loan, amount, account, payment_method):
    """
    Helper function to process loan repayment and create all necessary records
    """
    # Create repayment record
    repayment = LoanRepayment.objects.create(
        loan=loan,
        amount=amount,
        payment_method=payment_method,
        is_paid=True
    )

    # Create transaction record
    transaction = Transaction.objects.create(
        user=loan.user,
        amount=amount,
        transaction_type="loan_repayment",
        status="completed",
        sender=loan.user,
        receiver=loan.user,  # Or set to system account if you have one
        sender_account=account,
        receiver_account=account,  # Or system account
        description=f"Loan repayment for {loan.loan_type} loan via {payment_method}"
    )

    repayment.transaction = transaction
    repayment.save()

    # Check if loan is fully paid
    total_paid = loan.repayments.aggregate(Sum('amount'))['amount__sum'] or 0
    if total_paid >= loan.total_repayment:
        loan.status = 'completed'
        loan.is_active = False
        loan.save()

        Notification.objects.create(
            user=loan.user,
            notification_type="Loan Completion",
            amount=loan.amount,
            message=f"Your {loan.loan_type} loan has been fully repaid"
        )

    return repayment


@login_required
def payment_reminders(request):
    active_loans = LoanApplication.objects.filter(
        user=request.user,
        status__in=['approved', 'disbursed']
    )

    reminders = []
    for loan in active_loans:
        next_payment_date = calculate_next_payment_date(loan)
        if next_payment_date:
            days_until_due = (next_payment_date - timezone.now().date()).days
            reminders.append({
                'loan': loan,
                'next_payment_date': next_payment_date,
                'days_until_due': days_until_due,
                'amount_due': loan.monthly_repayment,
                'is_overdue': days_until_due < 0
            })

    return render(request, 'loan/reminders.html', {'reminders': reminders})



def calculate_next_payment_date(loan):
    """
    Calculate the next payment due date based on loan terms
    """
    if loan.status != 'disbursed':
        return None

    last_payment = loan.repayments.order_by('-payment_date').first()

    if last_payment:
        # Next payment is one month after last payment
        return last_payment.payment_date + relativedelta(months=1)
    else:
        # First payment is one month after disbursement
        return loan.date_disbursed + relativedelta(months=1)

class LoanRepaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount to pay',
            'min': '1000',
            'step': '1000'
        })
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('wallet', 'Wallet Balance'),
            ('mobile_money', 'Mobile Money'),
            ('card', 'Credit/Debit Card')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )



@login_required
def loan_history(request):
    loans = LoanApplication.objects.filter(user=request.user).order_by('-date_applied')
    return render(request, 'loan/history.html', {'loans': loans})

#  All repayments (across all loans)
@login_required
def repayment_history(request, loan_id=None):
    if loan_id:
        # Specific loan repayment history
        loan = get_object_or_404(LoanApplication, id=loan_id, user=request.user)
        repayments = loan.repayments.all().order_by('-payment_date')
    else:
        # All repayments across all loans
        repayments = LoanRepayment.objects.filter(
            loan__user=request.user
        ).order_by('-payment_date')

    return render(request, 'loan/repayment_history.html', {
        'repayments': repayments,
        'specific_loan': loan if loan_id else None
    })



@login_required
def mobile_money_transactions(request):
    deposits = Transaction.objects.filter(
        user=request.user,
        transaction_type='mobile_money_deposit'
    ).order_by('-date')

    withdrawals = Transaction.objects.filter(
        user=request.user,
        transaction_type='mobile_money_withdrawal'
    ).order_by('-date')

    return render(request, 'mobile_money/transactions.html', {
        'deposits': deposits,
        'withdrawals': withdrawals
    })


@login_required
def mobile_money_deposit(request):
    account = request.user.account
    deposit_limit = settings.MOBILE_MONEY_CONFIG['DEPOSIT_LIMITS']['single']

    if request.method == 'POST':
        form = MobileMoneyDepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            provider = form.cleaned_data['provider']
            phone_number = form.cleaned_data['phone_number']


            # Validate amount against limits
            if amount < settings.MOBILE_MONEY_CONFIG['DEPOSIT_LIMITS']['min']:
                messages.error(request, f"Amount must be at least UGX {settings.MOBILE_MONEY_CONFIG['DEPOSIT_LIMITS']['min']}")
                return redirect('core:mobile-money-deposit')

            if amount > deposit_limit:
                messages.error(request, f"Amount exceeds single deposit limit of UGX {deposit_limit}")
                return redirect('core:mobile-money-deposit')

            # Check daily deposit limit
            today = timezone.now().date()
            today_deposits = Transaction.objects.filter(
                user=request.user,
                transaction_type='mobile_money_deposit',
                date__date=today,
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            if today_deposits + amount > settings.MOBILE_MONEY_CONFIG['DEPOSIT_LIMITS']['daily']:
                messages.error(request, 
                    f"This deposit would exceed your daily limit of UGX {settings.MOBILE_MONEY_CONFIG['DEPOSIT_LIMITS']['daily']}")
                return redirect('core:mobile-money-deposit')

            # Generate unique reference
            ref = f"MMD-{request.user.id}-{timezone.now().timestamp()}"

            # Create pending transaction
            transaction = Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type="mobile_money_deposit",
                status="pending",
                description=f"Mobile Money Deposit from {phone_number} ({provider})"
            )

            MobileMoneyTransaction.objects.create(
                transaction=transaction,
                provider=provider,
                phone_number=phone_number,
                transaction_ref=ref
            )

            # For real implementation, you would call the payment gateway API here
            # For simulation, we'll redirect to a payment prompt
            return render(request, 'mobile_money/payment_prompt.html', {
                'phone': phone_number,
                'amount': amount,
                'ref': ref,
                'provider': provider,
                'callback_url': reverse('core:mobile-money-callback')
            })
    else:
    # Pre-fill with user's registered phone if available
        initial = {}
        phone_number = getattr(request.user, 'phone_number', None)
        if phone_number:
            initial['phone_number'] = phone_number
        form = MobileMoneyDepositForm(initial=initial)


    return render(request, 'mobile_money/deposit.html', {
        'form': form,
        'account': account,
        'deposit_limits': settings.MOBILE_MONEY_CONFIG['DEPOSIT_LIMITS']
    })

@csrf_exempt
def mobile_money_callback(request):
    """
    This would be the endpoint that the payment provider calls with payment status
    """
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            ref = payload.get('tx_ref')
            status = payload.get('status')

            if not ref or not status:
                return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)

            mm_transaction = MobileMoneyTransaction.objects.get(transaction_ref=ref)
            transaction = mm_transaction.transaction

            if status.lower() == 'successful':
                # Update transaction status
                transaction.status = 'completed'
                transaction.save()

                # Credit user's account
                account = transaction.user.account
                account.account_balance += transaction.amount
                account.save()

                # Create notification
                Notification.objects.create(
                    user=transaction.user,
                    notification_type="Mobile Money Deposit",
                    amount=transaction.amount,
                    message=f"Mobile Money deposit of UGX {transaction.amount} from {mm_transaction.phone_number} received"
                )

                mm_transaction.is_reconciled = True
                mm_transaction.save()

                return JsonResponse({'status': 'success'})

            else:
                # Payment failed
                transaction.status = 'failed'
                transaction.save()

                Notification.objects.create(
                    user=transaction.user,
                    notification_type="Mobile Money Deposit Failed",
                    amount=transaction.amount,
                    message=f"Mobile Money deposit of UGX {transaction.amount} failed"
                )

                return JsonResponse({'status': 'failed', 'message': 'Payment failed'})

        except MobileMoneyTransaction.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


@login_required
def mobile_money_withdrawal(request):
    account = request.user.account

    if request.method == 'POST':
        form = MobileMoneyWithdrawalForm(request.POST, user=request.user)
        if form.is_valid():
            amount = form.cleaned_data['amount']

            # Check available balance (including locked funds)
            if account.available_balance < amount:
                messages.error(request, "Insufficient funds for this withdrawal")
                return redirect('core:mobile-money-withdrawal')

            # Lock the funds immediately
            account.locked_funds += amount
            account.save()

            # Create transaction record
            transaction = Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type="mobile_money_withdrawal",
                status="pending_approval",  # New status
                description=f"Withdrawal request to {form.cleaned_data['phone_number']}"
            )

            MobileMoneyTransaction.objects.create(
                transaction=transaction,
                provider=form.cleaned_data['provider'],
                phone_number=form.cleaned_data['phone_number'],
                transaction_ref=f"MMW-{timezone.now().timestamp()}"
            )

            # Notify admin
            Notification.objects.create(
                user=request.user,
                notification_type="Withdrawal Request",
                message=f"New withdrawal request of UGX {amount} needs approval"
            )

            messages.success(request, "Withdrawal request submitted for admin approval")
            return redirect('core:mobile-money-transactions')
    else:
        form = MobileMoneyWithdrawalForm(user=request.user)

    return render(request, 'mobile_money/withdrawal.html', {
        'form': form,
        'account': account
    })



@csrf_exempt
def mobile_money_webhook(request):
    # This would be called by Flutterwave/MTN/Airtel API
    payload = json.loads(request.body)
    ref = payload['tx_ref']

    try:
        mm_transaction = MobileMoneyTransaction.objects.get(transaction_ref=ref)
        transaction = mm_transaction.transaction

        if payload['status'] == 'successful':
            # Update transaction status
            transaction.status = 'completed'
            transaction.save()

            # Update account balance
            account = transaction.user.account

            if transaction.transaction_type == 'mobile_money_deposit':
                account.mobile_money_balance += transaction.amount
                Notification.objects.create(
                    user=transaction.user,
                    notification_type="Mobile Money Deposit",
                    amount=transaction.amount,
                    message=f"Mobile Money deposit of UGX {transaction.amount} received"
                )
            elif transaction.transaction_type == 'mobile_money_withdrawal':
                account.locked_funds -= transaction.amount
                Notification.objects.create(
                    user=transaction.user,
                    notification_type="Mobile Money Withdrawal",
                    amount=transaction.amount,
                    message=f"Mobile Money withdrawal of UGX {transaction.amount} processed"
                )

            account.save()
            mm_transaction.is_reconciled = True
            mm_transaction.save()

            return JsonResponse({'status': 'success'})

    except MobileMoneyTransaction.DoesNotExist:
        pass

    return JsonResponse({'status': 'failed'}, status=400)

@login_required
def verify_mobile_number(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        provider = request.POST.get('provider')
        
        momo_api = MTNMomoAPI()
        
        if provider == 'MTN':
            user_info = momo_api.verify_user(phone_number)
            if user_info:
                return JsonResponse({
                    'valid': True,
                    'name': user_info.get('name', 'Verified User'),
                    'provider': provider
                })
            else:
                return JsonResponse({
                    'valid': False,
                    'message': 'Could not verify MTN number'
                })
        else:
            # For other providers, implement similar verification
            return JsonResponse({
                'valid': True,
                'name': 'Verified User',
                'provider': provider
            })
    
    return JsonResponse({'valid': False, 'message': 'Invalid request'})
    
# In views.py
def all_credit_cards(request):
    credit_cards = CreditCard.objects.filter(user=request.user)
    return render(request, 'credit_card/all_credit_cards.html', {'credit_cards': credit_cards})
    # core/views.py
@staff_member_required
def reconciliation_dashboard(request):
    unreconciled = MobileMoneyTransaction.objects.filter(
        is_reconciled=False
    ).select_related('transaction')

    today = timezone.now().date()
    daily_deposits = Transaction.objects.filter(
        transaction_type='mobile_money_deposit',
        status='completed',
        date__date=today
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'admin/reconciliation.html', {
        'unreconciled': unreconciled,
        'daily_deposits': daily_deposits,
        'deposit_limits': settings.MOBILE_MONEY_CONFIG['DEPOSIT_LIMITS']
    })



@login_required
def check_payment_status(request, ref):
    try:
        mm_tx = MobileMoneyTransaction.objects.get(transaction_ref=ref)
        transaction = mm_tx.transaction
        return JsonResponse({'status': transaction.status})
    except MobileMoneyTransaction.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)

@staff_member_required
def process_withdrawals(request):
    pending_withdrawals = Transaction.objects.filter(
        transaction_type='mobile_money_withdrawal',
        status='pending'
    ).select_related('user', 'mobile_money')

    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        action = request.POST.get('action')

        transaction = get_object_or_404(Transaction, id=transaction_id)

        if action == 'approve':
            # Process the withdrawal with your mobile money API
            transaction.status = 'completed'
            transaction.save()

            # Unlock funds (they've been sent)
            account = transaction.user.account
            account.locked_funds -= transaction.amount
            account.save()

            messages.success(request, "Withdrawal processed successfully")
        elif action == 'reject':
            # Return funds to available balance
            account = transaction.user.account
            account.locked_funds -= transaction.amount
            account.account_balance += transaction.amount
            account.save()

            transaction.status = 'failed'
            transaction.save()

            messages.success(request, "Withdrawal rejected and funds returned")

        return redirect('core:process-withdrawals')

    return render(request, 'admin/process_withdrawals.html', {
        'pending_withdrawals': pending_withdrawals
    })
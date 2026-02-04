from django.shortcuts import render, redirect, get_object_or_404
from account.models import Account
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.contrib import messages
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from core.models import Transaction, Notification
from django.db import transaction as db_transaction
from django.conf import settings
from django.utils import timezone


def safe_decimal(value, default=Decimal('0.00')):
    """Safely convert value to Decimal with 2 decimal places."""
    try:
        if value is None or value == '':
            return default
        amount = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if amount < 0:
            return default
        return amount
    except (InvalidOperation, ValueError, TypeError):
        return default


def check_transfer_limits(user, amount):
    """
    Check if transfer amount is within allowed limits.
    Returns (is_valid, error_message)
    """
    limits = getattr(settings, 'TRANSFER_LIMITS', {
        'min': 1000,
        'single': 10000000,
        'daily': 50000000,
    })

    # Check minimum
    if amount < limits['min']:
        return False, f"Minimum transfer amount is UGX {limits['min']:,}"

    # Check single transaction limit
    if amount > limits['single']:
        return False, f"Maximum single transfer is UGX {limits['single']:,}"

    # Check daily limit
    today = timezone.now().date()
    today_transfers = Transaction.objects.filter(
        sender=user,
        transaction_type='transfer',
        status='completed',
        date__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    if today_transfers + amount > limits['daily']:
        remaining = limits['daily'] - today_transfers
        return False, f"Daily transfer limit exceeded. Remaining limit: UGX {remaining:,.2f}"

    return True, None


@login_required
def search_users_account_number(request):
    # account = Account.objects.filter(account_status="active")
    account = Account.objects.all()
    query = request.POST.get("account_number")  # 217703423324

    if query:
        account = account.filter(
            Q(account_number=query) |
            Q(account_id=query)
        ).distinct()

    context = {
        "account": account,
        "query": query,
    }
    return render(request, "transfer/search-user-by-account-number.html", context)


@login_required
def AmountTransfer(request, account_number):
    try:
        account = Account.objects.get(account_number=account_number)
    except Account.DoesNotExist:
        messages.warning(request, "Invalid account details.")
        return redirect("core:search-account")

    # Prevent self-transfer
    if account.user == request.user:
        messages.warning(request, "You cannot transfer to your own account.")
        return redirect("core:search-account")

    context = {
        "account": account,
    }
    return render(request, "transfer/amount-transfer.html", context)


@login_required
def AmountTransferProcess(request, account_number):
    try:
        account = Account.objects.get(account_number=account_number)
    except Account.DoesNotExist:
        messages.warning(request, "Invalid account details.")
        return redirect("core:search-account")

    sender = request.user
    receiver = account.user

    sender_account = request.user.account
    receiver_account = account

    if request.method == "POST":
        amount_str = request.POST.get("amount-send", "").strip()
        description = request.POST.get("description", "").strip()

        # Validate empty input
        if not amount_str:
            messages.error(request, "Please enter an amount.")
            return redirect("core:amount-transfer", account.account_number)

        # Use safe decimal conversion
        amount = safe_decimal(amount_str)

        if amount <= 0:
            messages.error(request, "Invalid amount. Please enter a valid positive number.")
            return redirect("core:amount-transfer", account.account_number)

        # Check transfer limits
        is_valid, error_msg = check_transfer_limits(request.user, amount)
        if not is_valid:
            messages.error(request, error_msg)
            return redirect("core:amount-transfer", account.account_number)

        if sender_account.account_balance >= amount:
            new_transaction = Transaction.objects.create(
                user=request.user,
                amount=amount,
                description=description,
                receiver=receiver,
                sender=sender,
                sender_account=sender_account,
                receiver_account=receiver_account,
                status="processing",
                transaction_type="transfer"
            )
            return redirect("core:transfer-confirmation", account.account_number, new_transaction.transaction_id)
        else:
            messages.warning(request, "Insufficient funds.")
            return redirect("core:amount-transfer", account.account_number)

    messages.warning(request, "An error occurred. Try again later.")
    return redirect("account:account")


@login_required
def TransferConfirmation(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        # Verify the transaction belongs to the current user (IDOR fix)
        transaction = Transaction.objects.get(
            transaction_id=transaction_id,
            sender=request.user  # Ownership verification
        )
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    context = {
        "account": account,
        "transaction": transaction
    }
    return render(request, "transfer/transfer-confirmation.html", context)


@login_required
def TransferProcess(request, account_number, transaction_id):
    # Verify ownership - user can only process their own transactions
    try:
        receiver_account = Account.objects.get(account_number=account_number)
        transaction = Transaction.objects.get(
            transaction_id=transaction_id,
            sender=request.user  # IDOR protection
        )
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    sender_account = request.user.account

    if request.method == "POST":
        pin_number = request.POST.get("pin-number")

        # Use secure PIN verification
        if sender_account.verify_pin(pin_number):
            # Use atomic transaction to prevent partial failures
            try:
                with db_transaction.atomic():
                    # Lock both accounts to prevent race conditions
                    sender_acc = Account.objects.select_for_update().get(id=sender_account.id)
                    receiver_acc = Account.objects.select_for_update().get(id=receiver_account.id)

                    # Verify sufficient balance (re-check inside transaction)
                    if sender_acc.account_balance < transaction.amount:
                        messages.warning(request, "Insufficient funds.")
                        return redirect('core:transfer-confirmation', receiver_account.account_number, transaction.transaction_id)

                    # Update balances atomically
                    sender_acc.account_balance -= transaction.amount
                    sender_acc.save()

                    receiver_acc.account_balance += transaction.amount
                    receiver_acc.save()

                    # Update transaction status
                    transaction.status = "completed"
                    transaction.save()

                    # Create notifications
                    Notification.objects.create(
                        amount=transaction.amount,
                        user=receiver_account.user,
                        notification_type="Credit Alert"
                    )

                    Notification.objects.create(
                        user=request.user,
                        notification_type="Debit Alert",
                        amount=transaction.amount
                    )

                messages.success(request, "Transfer successful.")
                return redirect("core:transfer-completed", receiver_account.account_number, transaction.transaction_id)

            except Exception as e:
                messages.error(request, "Transfer failed. Please try again.")
                return redirect('core:transfer-confirmation', receiver_account.account_number, transaction.transaction_id)
        else:
            messages.warning(request, "Incorrect PIN.")
            return redirect('core:transfer-confirmation', receiver_account.account_number, transaction.transaction_id)
    else:
        messages.warning(request, "Invalid request method.")
        return redirect('account:account')


@login_required
def TransferCompleted(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        # Verify user owns this transaction
        transaction = Transaction.objects.get(
            transaction_id=transaction_id,
            sender=request.user  # IDOR protection
        )
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    context = {
        "account": account,
        "transaction": transaction
    }
    return render(request, "transfer/transfer-completed.html", context)

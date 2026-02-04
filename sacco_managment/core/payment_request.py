from django.shortcuts import render, redirect, get_object_or_404
from account.models import Account
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from core.models import Notification, Transaction
from django.db import transaction as db_transaction


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


@login_required
def SearchUsersRequest(request):
    account = Account.objects.all()
    query = request.POST.get("account_number")

    if query:
        account = account.filter(
            Q(account_number=query) |
            Q(account_id=query)
        ).distinct()

    context = {
        "account": account,
        "query": query,
    }
    return render(request, "payment_request/search-users.html", context)


@login_required
def AmountRequest(request, account_number):
    try:
        account = Account.objects.get(account_number=account_number)
    except Account.DoesNotExist:
        messages.warning(request, "Account not found.")
        return redirect("core:search-users-request")

    # Prevent requesting from self
    if account.user == request.user:
        messages.warning(request, "You cannot request payment from yourself.")
        return redirect("core:search-users-request")

    context = {
        "account": account,
    }
    return render(request, "payment_request/amount-request.html", context)


@login_required
def AmountRequestProcess(request, account_number):
    try:
        account = Account.objects.get(account_number=account_number)
    except Account.DoesNotExist:
        messages.warning(request, "Account not found.")
        return redirect("core:search-users-request")

    # Prevent requesting from self
    if account.user == request.user:
        messages.warning(request, "You cannot request payment from yourself.")
        return redirect("core:search-users-request")

    sender = request.user
    receiver = account.user
    sender_account = request.user.account
    receiver_account = account

    if request.method == "POST":
        amount = safe_decimal(request.POST.get("amount-request"))
        description = request.POST.get("description", "").strip()

        # Validate amount
        if amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
            return redirect("core:amount-request", account.account_number)

        # Add reasonable limits
        if amount > Decimal('10000000'):  # 10 million UGX limit
            messages.error(request, "Amount exceeds maximum request limit.")
            return redirect("core:amount-request", account.account_number)

        new_request = Transaction.objects.create(
            user=request.user,
            amount=amount,
            description=description,
            sender=sender,
            receiver=receiver,
            sender_account=sender_account,
            receiver_account=receiver_account,
            status="request_processing",
            transaction_type="request"
        )
        transaction_id = new_request.transaction_id
        return redirect("core:amount-request-confirmation", account.account_number, transaction_id)
    else:
        messages.warning(request, "Error occurred, try again later.")
        return redirect("account:dashboard")


@login_required
def AmountRequestConfirmation(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        # IDOR protection: verify the current user owns this transaction
        transaction = Transaction.objects.get(
            transaction_id=transaction_id,
            user=request.user  # Must be owned by current user
        )
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    context = {
        "account": account,
        "transaction": transaction,
    }
    return render(request, "payment_request/amount-request-confirmation.html", context)


@login_required
def AmountRequestFinalProcess(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        # IDOR protection: verify the current user owns this transaction
        transaction = Transaction.objects.get(
            transaction_id=transaction_id,
            user=request.user
        )
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    if request.method == "POST":
        pin_number = request.POST.get("pin-number")

        # Use secure PIN verification
        if request.user.account.verify_pin(pin_number):
            transaction.status = "request_sent"
            transaction.save()

            Notification.objects.create(
                user=account.user,
                notification_type="Recieved Payment Request",
                amount=transaction.amount,
            )

            Notification.objects.create(
                user=request.user,
                amount=transaction.amount,
                notification_type="Sent Payment Request"
            )

            messages.success(request, "Your payment request has been sent successfully.")
            return redirect("core:amount-request-completed", account.account_number, transaction.transaction_id)
        else:
            messages.warning(request, "Incorrect PIN")
            return redirect("core:amount-request-confirmation", account.account_number, transaction.transaction_id)
    else:
        messages.warning(request, "An error occurred, try again later.")
        return redirect("account:dashboard")


@login_required
def RequestCompleted(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        # IDOR protection
        transaction = Transaction.objects.get(
            transaction_id=transaction_id,
            user=request.user
        )
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    context = {
        "account": account,
        "transaction": transaction,
    }
    return render(request, "payment_request/amount-request-completed.html", context)


@login_required
def settlement_confirmation(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        # Allow viewing if user is the receiver (person who will pay)
        transaction = Transaction.objects.get(
            transaction_id=transaction_id,
            receiver=request.user  # Current user is the one paying
        )
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    context = {
        "account": account,
        "transaction": transaction,
    }
    return render(request, "payment_request/settlement-confirmation.html", context)


@login_required
def settlement_processing(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        # IDOR protection: current user must be the receiver (payer)
        transaction = Transaction.objects.get(
            transaction_id=transaction_id,
            receiver=request.user
        )
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    sender_account = request.user.account

    if request.method == "POST":
        pin_number = request.POST.get("pin-number")

        # Use secure PIN verification
        if sender_account.verify_pin(pin_number):
            # Use atomic transaction to prevent race conditions
            try:
                with db_transaction.atomic():
                    # Lock accounts for update
                    sender_acc = Account.objects.select_for_update().get(id=sender_account.id)
                    receiver_acc = Account.objects.select_for_update().get(id=account.id)

                    if sender_acc.account_balance <= 0 or sender_acc.account_balance < transaction.amount:
                        messages.warning(request, "Insufficient Funds, fund your account and try again.")
                        return redirect("core:settlement-confirmation", account.account_number, transaction.transaction_id)

                    # Deduct from sender
                    sender_acc.account_balance -= transaction.amount
                    sender_acc.save()

                    # Credit receiver
                    receiver_acc.account_balance += transaction.amount
                    receiver_acc.save()

                    # Update transaction status
                    transaction.status = "request_settled"
                    transaction.save()

                    # Create notifications
                    Notification.objects.create(
                        user=account.user,
                        notification_type="Credit Alert",
                        amount=transaction.amount,
                        message=f"Payment request settled - received UGX {transaction.amount:,.2f}"
                    )

                    Notification.objects.create(
                        user=request.user,
                        notification_type="Debit Alert",
                        amount=transaction.amount,
                        message=f"Payment request settled - paid UGX {transaction.amount:,.2f}"
                    )

                    messages.success(request, f"Settlement was successful.")
                    return redirect("core:settlement-completed", account.account_number, transaction.transaction_id)

            except Exception as e:
                messages.error(request, "Settlement failed. Please try again.")
                return redirect("core:settlement-confirmation", account.account_number, transaction.transaction_id)
        else:
            messages.warning(request, "Incorrect PIN")
            return redirect("core:settlement-confirmation", account.account_number, transaction.transaction_id)
    else:
        messages.warning(request, "Error Occurred")
        return redirect("account:dashboard")


@login_required
def SettlementCompleted(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        # Allow both sender and receiver to view completed settlement
        transaction = Transaction.objects.get(
            transaction_id=transaction_id
        )
        # Verify user is either sender or receiver
        if transaction.sender != request.user and transaction.receiver != request.user:
            raise Transaction.DoesNotExist
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("account:account")

    context = {
        "account": account,
        "transaction": transaction,
    }
    return render(request, "payment_request/settlement-completed.html", context)


@login_required
def deletepaymentrequest(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        transaction = Transaction.objects.get(transaction_id=transaction_id)
    except (Account.DoesNotExist, Transaction.DoesNotExist):
        messages.warning(request, "Transaction not found.")
        return redirect("core:transactions")

    # Only the owner can delete their payment request
    if request.user == transaction.user:
        # Only allow deletion of pending requests
        if transaction.status in ['request_processing', 'request_sent']:
            transaction.delete()
            messages.success(request, "Payment Request Deleted Successfully")
        else:
            messages.warning(request, "Cannot delete a settled or completed request.")
    else:
        messages.warning(request, "You can only delete your own payment requests.")

    return redirect("core:transactions")

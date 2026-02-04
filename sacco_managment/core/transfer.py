from django.shortcuts import render, redirect, get_object_or_404
from account.models import Account
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from core.models import Transaction, Notification
from django.db import transaction as db_transaction


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

        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            messages.error(request, "Invalid amount. Please enter a valid number.")
            return redirect("core:amount-transfer", account.account_number)

        if amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
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

        if pin_number == sender_account.pin_number:
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

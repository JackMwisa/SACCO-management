from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
import csv
from io import StringIO
from datetime import datetime, timedelta
from .models import CryptoWallet, CryptoTransaction
from .forms import TransactionForm
from django.utils import timezone

@login_required
def dashboard(request):
    wallets = CryptoWallet.objects.filter(user=request.user).select_related('user')
    transactions = CryptoTransaction.objects.filter(
        wallet__user=request.user
    ).select_related('wallet').order_by('-timestamp')[:10]
    
    context = {
        'wallets': wallets,
        'transactions': transactions,
        'total_balance': sum(wallet.balance for wallet in wallets)
    }
    return render(request, 'financial_services/dashboard.html', context)

@login_required
@transaction.atomic
def create_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            crypto_transaction = form.save(commit=False)
            wallet = crypto_transaction.wallet
            
            try:
                if crypto_transaction.transaction_type == 'DEPOSIT':
                    wallet.balance += crypto_transaction.amount
                else:  # WITHDRAWAL or TRANSFER
                    wallet.balance -= crypto_transaction.amount
                
                wallet.save()
                crypto_transaction.status = 'COMPLETED'
                crypto_transaction.save()
                
                messages.success(request, 'Transaction completed successfully!')
                return redirect('financial_services:crypto_dashboard')
            
            except Exception as e:
                messages.error(request, f'Error processing transaction: {str(e)}')
    else:
        form = TransactionForm(user=request.user)
    
    return render(request, 'financial_services/create_transaction.html', {'form': form})

@login_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(
        CryptoTransaction.objects.select_related('wallet', 'wallet__user'),
        pk=pk
    )
    
    if transaction.wallet.user != request.user:
        raise PermissionDenied
    
    return render(request, 'financial_services/transaction_detail.html', {
        'transaction': transaction
    })

@login_required
def transaction_history(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    transaction_type = request.GET.get('type')
    
    transactions = CryptoTransaction.objects.filter(
        wallet__user=request.user
    ).select_related('wallet').order_by('-timestamp')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(timestamp__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(timestamp__date__lte=date_to)
        except ValueError:
            pass
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    context = {
        'transactions': transactions,
        'filter_date_from': date_from.strftime('%Y-%m-%d') if date_from else '',
        'filter_date_to': date_to.strftime('%Y-%m-%d') if date_to else '',
        'filter_type': transaction_type or ''
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'html': render(request, 'financial_services/includes/transaction_table.html', context).content.decode('utf-8')
        }
        return JsonResponse(data)
    
    return render(request, 'financial_services/transaction_history.html', context)

@login_required
def wallet_detail(request, wallet_id):
    wallet = get_object_or_404(CryptoWallet, id=wallet_id, user=request.user)
    transactions = CryptoTransaction.objects.filter(wallet=wallet).order_by('-timestamp')

    return render(request, 'financial_services/wallet_detail.html', {
        'wallet': wallet,
        'transactions': transactions,
    })



@login_required
def generate_report(request):
    transactions = CryptoTransaction.objects.filter(
        wallet__user=request.user
    ).select_related('wallet').order_by('-timestamp')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="crypto_report_{timezone.now().date()}.csv"'
    )
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Type', 'Amount', 'Currency', 'Status', 'Description'
    ])
    
    for tx in transactions:
        writer.writerow([
            tx.timestamp.strftime('%Y-%m-%d %H:%M'),
            tx.get_transaction_type_display(),
            f"{tx.amount:.8f}",
            tx.wallet.wallet_type,
            tx.get_status_display(),
            tx.description
        ])
    
    return response
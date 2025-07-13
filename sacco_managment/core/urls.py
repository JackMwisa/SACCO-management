from django.urls import path
from core import views, transfer, transaction, payment_request, credit_card
from django.conf import settings
from .views import (
    apply_for_loan,
    loan_status,
    loan_detail,
    repay_loan,
    loan_history,
    repayment_history,
)


app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),

    # Transfers
    path("search-account/", transfer.search_users_account_number,
         name="search-account"),
    path("amount-transfer/<account_number>/",
         transfer.AmountTransfer, name="amount-transfer"),
    path("amount-transfer-process/<account_number>/",
         transfer.AmountTransferProcess, name="amount-transfer-process"),
    path("transfer-confirmation/<account_number>/<transaction_id>/",
         transfer.TransferConfirmation, name="transfer-confirmation"),
    path("transfer-process/<account_number>/<transaction_id>/",
         transfer.TransferProcess, name="transfer-process"),
    path("transfer-completed/<account_number>/<transaction_id>/",
         transfer.TransferCompleted, name="transfer-completed"),


    # transactions
    path("transactions/", transaction.transaction_lists, name="transactions"),
    path("transaction-detail/<transaction_id>/",
         transaction.transaction_detail, name="transaction-detail"),
    # path('transactions/', views.transactions, name='transactions'),

    # Payment Request
    path("request-search-account/", payment_request.SearchUsersRequest,
         name="request-search-account"),
    path("amount-request/<account_number>/",
         payment_request.AmountRequest, name="amount-request"),
    path("amount-request-process/<account_number>/",
         payment_request.AmountRequestProcess, name="amount-request-process"),
    path("amount-request-confirmation/<account_number>/<transaction_id>/",
         payment_request.AmountRequestConfirmation, name="amount-request-confirmation"),
    path("amount-request-final-process/<account_number>/<transaction_id>/",
         payment_request.AmountRequestFinalProcess, name="amount-request-final-process"),
    path("amount-request-completed/<account_number>/<transaction_id>/",
         payment_request.RequestCompleted, name="amount-request-completed"),


    # Request Settlement
    path("settlement-confirmation/<account_number>/<transaction_id>/",
         payment_request.settlement_confirmation, name="settlement-confirmation"),
    path("settlement-processing/<account_number>/<transaction_id>/",
         payment_request.settlement_processing, name="settlement-processing"),
    path("settlement-completed/<account_number>/<transaction_id>/",
         payment_request.SettlementCompleted, name="settlement-completed"),
    path("delete-request/<account_number>/<transaction_id>/",
         payment_request.deletepaymentrequest, name="delete-request"),



    # Credit Card URLS
    path("card/<card_id>/", credit_card.card_detail, name="card-detail"),
    path("fund-credit-card/<card_id>/",
         credit_card.fund_credit_card, name="fund-credit-card"),
    path("withdraw_fund/<card_id>/",
         credit_card.withdraw_fund, name="withdraw_fund"),
    path("delete_card/<card_id>/", credit_card.delete_card, name="delete_card"),


    # Loan URLs
    path('loans/apply/', apply_for_loan, name='apply-loan'),
    path('loans/', loan_status, name='loan-status'),
    path('loans/history/', loan_history, name='loan-history'),
    path('loans/repayments/', repayment_history, name='repayment-history'),
    path('loans/<int:loan_id>/', loan_detail, name='loan-detail'),
    path('loans/<int:loan_id>/repay/', views.repay_loan, name='repay-loan'),
    path('loans/<int:loan_id>/repayments/', views.repayment_history, name='repayment-history'),
    path('loans/reminders/', views.payment_reminders, name='payment-reminders'),

    #mobile money
    path('mobile-money/deposit/', views.mobile_money_deposit, name='mobile-money-deposit'),
    path('mobile-money/withdrawal/', views.mobile_money_withdrawal, name='mobile-money-withdrawal'),
    path('mobile-money/status/<str:ref>/', views.check_payment_status, name='check-payment-status'),
    path('mobile-money/transactions/', views.mobile_money_transactions, name='mobile-money-transactions'),
    path('webhook/mobile-money/', views.mobile_money_webhook, name='mobile-money-webhook'),
    path('admin/reconciliation/', views.reconciliation_dashboard, name='reconciliation-dashboard'),
    path('mobile-money/callback/', views.mobile_money_callback, name='mobile-money-callback'),

]

from django.urls import path
from . import views

app_name = 'financial_services'

urlpatterns = [
    path('', views.dashboard, name='crypto_dashboard'),
    path('transaction/', views.create_transaction, name='create_transaction'),
    path('transaction/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),
    path('report/', views.generate_report, name='generate_report'),
    
    path('wallet/<int:wallet_id>/', views.wallet_detail, name='wallet_detail'),
    
    # API endpoints
    path('api/transactions/', views.transaction_history, name='transaction_history_api'),
]
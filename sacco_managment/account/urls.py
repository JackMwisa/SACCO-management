from django.urls import path
from account import views
from django.urls import include
from .views import all_credit_cards, calendar
from django.contrib.auth.views import LogoutView
from core.decorators import staff_required, admin_required

app_name = "account"

urlpatterns = [
    
    path("logout/", LogoutView.as_view(), name="logout"),
    # Member URLs
    path("dashboard/", views.dashboard, name="dashboard"),
    path("", views.account, name="account"),
    path("kyc-reg/", views.kyc_registration, name="kyc-reg"),
    path("reset-pin/", views.reset_pin, name="reset-pin"),
    path("change-password/", views.change_password, name="change-password"),
    path("search/", views.search, name="search"),
    path('credit-cards/', all_credit_cards, name='all-credit-cards'),
    path("calendar/", calendar, name="calendar"),

    # Authentication
    path('staff/login/', views.StaffLoginView.as_view(), name='staff_login'),
    path('logout/', LogoutView.as_view(next_page='account:staff_login'), name='logout'),
   
    # Staff URLs
    path('staff/dashboard/', staff_required(views.staff_dashboard), name='staff_dashboard'),
    path('staff/profiles/', staff_required(views.user_profiles), name='user_profiles'),
    path('staff/password-resets/', staff_required(views.password_resets), name='password_resets'),
    path('staff/kyc-review/', staff_required(views.kyc_review), name='kyc_review'),
    
    # Admin URLs
    path('admin/dashboard/', admin_required(views.admin_dashboard), name='admin_dashboard'),
    path('admin/manage-staff/', admin_required(views.manage_staff), name='manage_staff'),
    path('admin/financial-reports/', admin_required(views.financial_reports), name='financial_reports'),
    path('admin/audit-logs/', admin_required(views.audit_logs), name='audit_logs'),
    path('admin/add-staff/', admin_required(views.add_staff), name='add_staff'),
    path('admin/edit-staff/<int:staff_id>/', admin_required(views.edit_staff), name='edit_staff'),
    path('admin/activate-staff/<int:staff_id>/', admin_required(views.activate_staff), name='activate_staff'),
    path('admin/deactivate-staff/<int:staff_id>/', admin_required(views.deactivate_staff), name='deactivate_staff'),
     #   withdrawal management
    path('admin/withdrawals/pending/', admin_required(views.pending_withdrawals), name='pending_withdrawals'),
    path('admin/withdrawals/approve/<int:tx_id>/', admin_required(views.approve_withdrawal), name='approve_withdrawal'),
    path('admin/withdrawals/reject/<int:tx_id>/', admin_required(views.reject_withdrawal), name='reject_withdrawal'),
    
    
     # Staff Management URLs
    path('admin/manage-staff/', admin_required(views.manage_staff), name='manage_staff'),
    path('admin/add-staff/', admin_required(views.add_staff), name='add_staff'),
    path('admin/edit-staff/<int:staff_id>/', admin_required(views.edit_staff), name='edit_staff'),
    path('admin/activate-staff/<int:staff_id>/', admin_required(views.activate_staff), name='activate_staff'),
    path('admin/deactivate-staff/<int:staff_id>/', admin_required(views.deactivate_staff), name='deactivate_staff'),
    path('admin/delete-staff/<int:staff_id>/', admin_required(views.delete_staff), name='delete_staff'),
    path('admin/staff-activity/', admin_required(views.staff_activity), name='staff_activity'),
    path('admin/staff-action-logs/', admin_required(views.staff_action_logs), name='staff_action_logs'),
    
    # User Activity URLs
    path('admin/user-login-history/', admin_required(views.user_login_history), name='user_login_history'),
    path('admin/daily-logins/', admin_required(views.daily_logins), name='daily_logins'),
    
    
]
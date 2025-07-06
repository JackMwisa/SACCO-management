# account/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.urls import reverse, path
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from .models import AdminRequest  # or from account.models if needed
from .models import Account, KYC, StaffPermission, AuditLog
from user_auths.models import User
from .models import AdminRequest
# Unregister User if already registered
admin.site.unregister(User)

# --- StaffPermission Admin ---
@admin.register(StaffPermission)
class StaffPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'permissions_summary', 'is_active')
    list_filter = ('role', 'can_view_balances', 'can_approve_loans')
    search_fields = ('user__username', 'user__email')
    list_editable = ('role',)
    actions = ['activate_staff', 'deactivate_staff']

    def permissions_summary(self, obj):
        perms = []
        if obj.can_view_balances: perms.append("View Balances")
        if obj.can_reset_passwords: perms.append("Reset Passwords")
        if obj.can_approve_loans: perms.append("Approve Loans")
        if obj.can_edit_kyc: perms.append("Edit KYC")
        return ", ".join(perms) if perms else "No permissions"
    permissions_summary.short_description = "Permissions"

    def is_active(self, obj):
        return obj.user.is_active
    is_active.boolean = True

    def activate_staff(self, request, queryset):
        updated = queryset.update(user__is_active=True)
        self.message_user(request, f"{updated} staff members activated.")

    def deactivate_staff(self, request, queryset):
        updated = queryset.update(user__is_active=False)
        self.message_user(request, f"{updated} staff members deactivated.")

# --- Custom User Admin ---
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'last_login')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['make_staff', 'remove_staff']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f"{updated} users marked as staff.")

    def remove_staff(self, request, queryset):
        updated = queryset.update(is_staff=False)
        self.message_user(request, f"{updated} users removed from staff.")

# --- Account Admin ---
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'account_status', 'balance_summary', 'kyc_status')
    list_filter = ('account_status', 'kyc_submitted', 'kyc_confirmed')
    search_fields = ('user__username', 'account_number')
    readonly_fields = ('account_balance', 'mobile_money_balance')

    def balance_summary(self, obj):
        return f"Main: UGX {obj.account_balance} | Mobile: UGX {obj.mobile_money_balance}"
    balance_summary.short_description = "Balances"

    def kyc_status(self, obj):
        if obj.kyc_confirmed:
            return format_html('<span style="color: green;">&#10003; Approved</span>')
        elif obj.kyc_submitted:
            return format_html('<span style="color: orange;">Pending Review</span>')
        return format_html('<span style="color: red;">Not Submitted</span>')
    kyc_status.short_description = "KYC Status"

# --- KYC Admin ---
@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'identity_type', 'country', 'kyc_actions')
    list_filter = ('identity_type', 'country')
    search_fields = ('full_name', 'user__username')
    readonly_fields = ('user', 'account')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/approve/', self.admin_site.admin_view(self.approve_kyc), name='approve_kyc'),
        ]
        return custom_urls + urls

    def kyc_actions(self, obj):
        if not obj.account.kyc_confirmed:
            return format_html('<a class="button" href="{}">Approve</a>', reverse('admin:approve_kyc', args=[obj.pk]))
        return "Approved"
    kyc_actions.short_description = "Actions"

    def approve_kyc(self, request, object_id):
        kyc = KYC.objects.get(pk=object_id)
        kyc.account.kyc_confirmed = True
        kyc.account.save()
        messages.success(request, f"KYC for {kyc.user.username} approved successfully.")
        return HttpResponseRedirect(reverse('admin:account_kyc_changelist'))

# --- AuditLog Admin ---
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'details')
    readonly_fields = ('user', 'action', 'timestamp', 'ip_address')
    date_hierarchy = 'timestamp'

@admin.register(AdminRequest)
class AdminRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'request_type', 'status', 'created_at')
    list_filter = ('status', 'request_type')
    search_fields = ('user__username', 'user__email')

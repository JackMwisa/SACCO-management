# account/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Account, UserProfile, StaffPermission, LoginHistory

User = get_user_model()

# -----------------------------------------------------------------------------
# Account activity tracking
@receiver(post_save, sender=Account)
def handle_account_activity(sender, instance, **kwargs):
    """
    Update last_activity timestamp whenever the Account is saved.
    Uses update() to avoid infinite recursion.
    """
    Account.objects.filter(pk=instance.pk).update(last_activity=timezone.now())

# -----------------------------------------------------------------------------
# User profile signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile instance after a new User is created.
    Uses get_or_create to prevent duplicates.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the associated UserProfile when the User is saved.
    """
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

# -----------------------------------------------------------------------------
# Account creation signals - UPDATED TO PREVENT DUPLICATES
@receiver(post_save, sender=User, dispatch_uid="create_account_for_user")
def create_account(sender, instance, created, **kwargs):
    """
    Create an Account linked to the User when a new User is created.
    Uses get_or_create to prevent duplicate accounts.
    """
    if created:
        Account.objects.get_or_create(user=instance)

@receiver(post_save, sender=User, dispatch_uid="save_account_for_user")
def save_account(sender, instance, **kwargs):
    """
    Save the associated Account when the User is saved.
    """
    if hasattr(instance, 'account'):
        instance.account.save()

# -----------------------------------------------------------------------------
# Staff permission signals
@receiver(post_save, sender=User, dispatch_uid="create_staff_permission_for_user")
def create_staff_permission(sender, instance, created, **kwargs):
    """
    Create a StaffPermission for users with a staff/admin/super_admin role.
    """
    if created and hasattr(instance, 'role') and instance.role in ['STAFF', 'ADMIN', 'SUPER_ADMIN']:
        StaffPermission.objects.get_or_create(user=instance)

# -----------------------------------------------------------------------------
# Login history signals
def get_client_ip(request):
    if request is None or not hasattr(request, 'META'):
        return "0.0.0.0"

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip



@receiver(user_logged_in, dispatch_uid="log_user_login")
def log_user_login(sender, request, user, **kwargs):
    LoginHistory.objects.create(
        user=user,
        action='LOGIN',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        successful=True
    )

@receiver(user_logged_out, dispatch_uid="log_user_logout")
def log_user_logout(sender, request, user, **kwargs):
    LoginHistory.objects.create(
        user=user,
        action='LOGOUT',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        successful=True
    )

@receiver(user_login_failed, dispatch_uid="log_user_login_failed")
def log_user_login_failed(sender, credentials, request, **kwargs):
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''

    LoginHistory.objects.create(
        user=None,
        action='LOGIN_FAILED',
        ip_address=ip,
        user_agent=user_agent,
        successful=False,
        details=f"Failed login attempt for username: {credentials.get('username')}"
    )

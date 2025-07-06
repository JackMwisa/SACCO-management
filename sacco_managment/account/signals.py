from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model

from account.models import Account, UserProfile, StaffPermission

# Use the custom User model
User = get_user_model()

# -----------------------------------------------------------------------------
# Automatically update the account's last_activity field on save
@receiver(post_save, sender=Account)
def handle_account_activity(sender, instance, **kwargs):
    """
    Update last_activity timestamp whenever the Account is saved.
    Uses update() to avoid infinite recursion.
    """
    Account.objects.filter(pk=instance.pk).update(last_activity=timezone.now())

# -----------------------------------------------------------------------------
# Automatically create a UserProfile when a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile instance after a new User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)

# Automatically save UserProfile when the User is updated
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the associated UserProfile when the User is saved.
    """
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

# -----------------------------------------------------------------------------
# Automatically create an Account when a new User is created
@receiver(post_save, sender=User)
def create_account(sender, instance, created, **kwargs):
    """
    Create an Account linked to the User when a new User is created.
    """
    if created:
        Account.objects.create(user=instance)

# Automatically save Account when the User is updated
@receiver(post_save, sender=User)
def save_account(sender, instance, **kwargs):
    """
    Save the associated Account when the User is saved.
    """
    if hasattr(instance, 'account'):
        instance.account.save()

# -----------------------------------------------------------------------------
# Automatically create a StaffPermission if the user's role qualifies
@receiver(post_save, sender=User)
def create_staff_permission(sender, instance, created, **kwargs):
    """
    Create a StaffPermission for users with a staff/admin/super_admin role.
    """
    if created and hasattr(instance, 'role') and instance.role in ['STAFF', 'ADMIN', 'SUPER_ADMIN']:
        StaffPermission.objects.get_or_create(user=instance)

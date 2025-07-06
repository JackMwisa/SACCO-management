
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from shortuuid.django_fields import ShortUUIDField
import uuid
from django.db.models.signals import post_save
 

User = get_user_model()

ACCOUNT_STATUS = (
    ("active", "Active"),
    ("pending", "Pending"),
    ("in-active", "Inactive"),
)

MARITAL_STATUS = (
    ("married", "Married"),
    ("single", "Single"),
    ("other", "Other"),
)

GENDER = (
    ("male", "Male"),
    ("female", "Female"),
    ("other", "Other"),
)

IDENTITY_TYPE = (
    ("national_id_card", "National ID Card"),
    ("refugee_id_card", "Refugee ID Card"),
    ("drivers_license", "Driver’s License"),
    ("international_passport", "International Passport"),
)

STAFF_ROLES = (
    ('SUPPORT', 'Support Staff'),
    ('LOAN_OFFICER', 'Loan Officer'),
    ('ACCOUNT_MANAGER', 'Account Manager'),
    ('ADMIN', 'System Admin'),
)

class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_number = ShortUUIDField(unique=True, length=10, prefix="217", alphabet="1234567890")
    account_id = ShortUUIDField(unique=True, length=7, prefix="DEX", alphabet="1234567890")
    pin_number = ShortUUIDField(unique=True, length=4, alphabet="1234567890")
    red_code = ShortUUIDField(unique=True, length=10, alphabet="abcdefgh1234567890")
    account_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    mobile_money_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    locked_funds = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS, default="in-active")
    kyc_submitted = models.BooleanField(default=False)
    kyc_confirmed = models.BooleanField(default=False)
    last_activity = models.DateTimeField(default=timezone.now)
    recommended_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='recommended_accounts')
    review = models.CharField(max_length=100, null=True, blank=True, default="Review")
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f"{self.user.username}'s Account"

    @property
    def available_balance(self):
        return self.account_balance + self.mobile_money_balance - self.locked_funds

class KYC(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account = models.OneToOneField(Account, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=1000)
    image = models.ImageField(upload_to="kyc", default="default.jpg")
    marrital_status = models.CharField(choices=MARITAL_STATUS, max_length=40)
    gender = models.CharField(choices=GENDER, max_length=40)
    identity_type = models.CharField(choices=IDENTITY_TYPE, max_length=140)
    identity_image = models.ImageField(upload_to="kyc", null=True, blank=True)
    date_of_birth = models.DateField()
    signature = models.ImageField(upload_to="kyc")
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    mobile = models.CharField(max_length=100)
    fax = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)
    kyc_confirmed = models.BooleanField(default=False) 

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f"KYC for {self.user.username}"

class StaffPermission(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=STAFF_ROLES)
    can_view_balances = models.BooleanField(default=False)
    can_reset_passwords = models.BooleanField(default=False)
    can_approve_loans = models.BooleanField(default=False)
    can_edit_kyc = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)
    # Add other profile fields as needed

    def __str__(self):
        return f"{self.user.username}'s Profile"


class AdminRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"
    
    
class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('LOGIN', 'User Login'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('ACCOUNT_EDIT', 'Account Modified'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} at {self.timestamp}"

# SIGNALS

def create_account(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)

def save_account(sender, instance, **kwargs):
    if hasattr(instance, 'account'):
        instance.account.save()

def create_staff_permission(sender, instance, created, **kwargs):
    if created and instance.role in ['STAFF', 'ADMIN', 'SUPER_ADMIN']:
        StaffPermission.objects.get_or_create(user=instance)

post_save.connect(create_account, sender=User)
post_save.connect(save_account, sender=User)
post_save.connect(create_staff_permission, sender=User)
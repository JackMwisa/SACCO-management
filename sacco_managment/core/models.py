from django.db import models
from user_auths.models import User
from account.models import Account
from shortuuid.django_fields import ShortUUIDField

# User = get_user_model() 

TRANSACTION_TYPE = (
    ("transfer", "Transfer"),
    ("received", "Received"),
    ("withdraw", "withdraw"),        
    ("deposit", "Deposit"),   
    ("loan_disbursement", "Loan Disbursement"),  
    ("refund", "Refund"),
    ("request", "Payment Request"),
    ("mobile_money_deposit", "Mobile Money Deposit"),
    ("mobile_money_withdrawal", "Mobile Money Withdrawal"),
    ("none", "None")
)

TRANSACTION_STATUS = (
    ("failed", "failed"),
    ("completed", "completed"),
    ("pending", "pending"),
    ("processing", "processing"),
    ("request_sent", "request_sent"),
    ("request_settled", "request settled"),
    ("request_processing", "request processing"),

)


CARD_TYPE = (
    ("master", "master"),
    ("visa", "visa"),
    ("verve", "verve"),

)


NOTIFICATION_TYPE = (
    ("None", "None"),
    ("Transfer", "Transfer"),
    ("Credit Alert", "Credit Alert"),
    ("Debit Alert", "Debit Alert"),
    ("Sent Payment Request", "Sent Payment Request"),
    ("Recieved Payment Request", "Recieved Payment Request"),
    ("Funded Credit Card", "Funded Credit Card"),
    ("Withdrew Credit Card Funds", "Withdrew Credit Card Funds"),
    ("Deleted Credit Card", "Deleted Credit Card"),
    ("Added Credit Card", "Added Credit Card"),

)

PROVIDER_CHOICES = (
        ("MTN", "MTN"),
        ("Airtel", "Airtel"),
)

# loan model


LOAN_TYPES = (
    ('personal', 'Personal Loan'),
    ('business', 'Business Loan'),
    ('emergency', 'Emergency Loan'),
    ('education', 'Education Loan'),
)

LOAN_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('disbursed', 'Disbursed'),
    ('completed', 'Completed'),
)
class LoanApplication(models.Model):
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    purpose = models.TextField()
    date_applied = models.DateTimeField(auto_now_add=True)
    date_approved = models.DateTimeField(null=True, blank=True)
    date_disbursed = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.loan_type} - {self.amount}"
    
    @property
    def monthly_repayment(self):
        monthly_rate = self.interest_rate / 100 / 12
        numerator = monthly_rate * (1 + monthly_rate) ** self.duration_months
        denominator = (1 + monthly_rate) ** self.duration_months - 1
        return self.amount * (numerator / denominator)
    
    @property
    def total_repayment(self):
        return self.monthly_repayment * self.duration_months
    
    @property
    def total_interest(self):
        return self.total_repayment - self.amount


class LoanRepayment(models.Model):
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction = models.ForeignKey('Transaction', on_delete=models.SET_NULL, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Repayment for {self.loan} - {self.amount}"



# loan model

class Transaction(models.Model):
    transaction_id = ShortUUIDField(
        unique=True, length=15, max_length=20, prefix="TRN")

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="user")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    description = models.CharField(max_length=1000, null=True, blank=True)

    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="receiver")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sender")
    receiver_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name="receiver_account")
    
    
    sender_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, related_name="sender_account")

    status = models.CharField(
        choices=TRANSACTION_STATUS, max_length=100, default="pending")
    transaction_type = models.CharField(
        choices=TRANSACTION_TYPE, max_length=100, default="none")

    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=False, null=True, blank=True)

    def __str__(self):
        try:
            return f"{self.user}"
        except:
            return f"Transaction"


class CreditCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_id = ShortUUIDField(
        unique=True, length=5, max_length=20, prefix="CARD", alphabet="1234567890")

    name = models.CharField(max_length=100)
    number = models.IntegerField()
    month = models.IntegerField()
    year = models.IntegerField()
    cvv = models.IntegerField()

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    card_type = models.CharField(
        choices=CARD_TYPE, max_length=20, default="master")
    card_status = models.BooleanField(default=True)

    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notification_type = models.CharField(
        max_length=100, choices=NOTIFICATION_TYPE, default="none")
    amount = models.IntegerField(default=0)
    is_read = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    nid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")
    message = models.TextField(blank=True, null=True)  

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Notification"

    def __str__(self):
        return f"Notification({self.user if self.user else 'Unknown User'} - {self.notification_type} - {self.date})"



#MOBILE MONEY MODEL
class MobileMoneyTransaction(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='mobile_money')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    phone_number = models.CharField(max_length=15)
    transaction_ref = models.CharField(max_length=50, unique=True)
    is_reconciled = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider} - {self.phone_number} - {self.transaction.amount}"

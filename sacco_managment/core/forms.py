from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import CreditCard, LoanApplication, LoanRepayment, Transaction
from account.models import Account
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum
import re


class CreditCardForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Card Holder Name",
            "class": "form-control"
        }),
        max_length=100
    )
    number = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Card Number",
            "class": "form-control"
        }),
        max_length=19  # For spaces in card number
    )
    month = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            "placeholder": "MM",
            "class": "form-control",
            "min": 1,
            "max": 12
        }),
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    year = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            "placeholder": "YYYY",
            "class": "form-control",
            "min": datetime.now().year,
            "max": datetime.now().year + 10
        })
    )
    cvv = forms.CharField(
        widget=forms.NumberInput(attrs={
            "placeholder": "CVV",
            "class": "form-control",
            "maxlength": 4
        }),
        max_length=4
    )

    class Meta:
        model = CreditCard
        fields = ['name', 'number', 'month', 'year', 'cvv', 'card_type']
        widgets = {
            'card_type': forms.Select(attrs={'class': 'form-control'})
        }

    def clean_number(self):
        number = self.cleaned_data['number'].replace(" ", "")
        if not number.isdigit():
            raise forms.ValidationError("Card number should contain only digits")
        if len(number) < 13 or len(number) > 19:
            raise forms.ValidationError("Invalid card number length")
        return number

    def clean_year(self):
        year = self.cleaned_data['year']
        current_year = datetime.now().year
        if year < current_year or year > current_year + 10:
            raise forms.ValidationError("Invalid expiry year")
        return year

    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('month')
        year = cleaned_data.get('year')

        if month and year:
            current_month = datetime.now().month
            current_year = datetime.now().year

            if year == current_year and month < current_month:
                raise forms.ValidationError("Card has already expired")

        return cleaned_data


class LoanApplicationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add real-time calculation attributes
        self.fields['amount'].widget.attrs.update({
            'oninput': 'calculateLoan()',
            'id': 'loan-amount'
        })
        self.fields['duration_months'].widget.attrs.update({
            'oninput': 'calculateLoan()',
            'id': 'loan-duration'
        })
        self.fields['loan_type'].widget.attrs.update({
            'onchange': 'calculateLoan()',
            'id': 'loan-type'
        })

    class Meta:
        model = LoanApplication
        fields = ['loan_type', 'amount', 'duration_months', 'purpose']
        widgets = {
            'loan_type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Amount in UGX',
                'min': '10000'
            }),
            'duration_months': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '24'
            }),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Briefly explain the purpose of this loan (minimum 20 characters)',
                'minlength': '20'
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount < 10000:  # Minimum loan amount
            raise forms.ValidationError("Minimum loan amount is UGX 10,000")
        if amount > 10000000:  # Maximum loan amount
            raise forms.ValidationError("Maximum loan amount is UGX 10,000,000")
        return amount

    def clean_duration_months(self):
        duration = self.cleaned_data.get('duration_months')
        if duration < 1 or duration > 24:  # Max 2 years
            raise forms.ValidationError("Loan duration must be between 1 and 24 months")
        return duration

    def clean_purpose(self):
        purpose = self.cleaned_data.get('purpose')
        if len(purpose.strip()) < 20:
            raise forms.ValidationError("Please provide a meaningful purpose (at least 20 characters)")
        return purpose


class LoanRepaymentForm(forms.Form):
    PAYMENT_METHODS = [
        ('wallet', 'Wallet Balance'),
        ('mobile_money', 'Mobile Money'),
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer')
    ]

    amount = forms.DecimalField(
        label='Repayment Amount (UGX)',
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount to pay',
            'step': '1000',
            'id': 'repayment-amount'
        })
    )
    payment_method = forms.ChoiceField(
        label='Payment Method',
        choices=PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.loan = kwargs.pop('loan', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.loan:
            # Calculate remaining balance
            remaining_balance = self.loan.total_repayment - \
                (self.loan.repayments.aggregate(Sum('amount'))['amount__sum'] or 0)
            
            # Set max amount to remaining balance
            self.fields['amount'].widget.attrs['max'] = remaining_balance
            self.fields['amount'].initial = min(
                self.loan.monthly_repayment, remaining_balance)

            # Disable wallet option if insufficient balance
            if self.user and self.user.account.account_balance <= 0:
                self.fields['payment_method'].choices = [
                    m for m in self.PAYMENT_METHODS if m[0] != 'wallet']

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if not self.loan:
            return amount

        remaining_balance = self.loan.total_repayment - \
            (self.loan.repayments.aggregate(Sum('amount'))['amount__sum'] or 0)

        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero")
        if amount > remaining_balance:
            raise forms.ValidationError(
                f"Amount cannot exceed remaining balance of UGX {remaining_balance:,.0f}")
        if amount < 1000:
            raise forms.ValidationError("Minimum repayment amount is UGX 1,000")

        return amount


class MobileMoneyDepositForm(forms.Form):
    PROVIDER_CHOICES = [
        ('MTN', 'MTN Mobile Money'),
        ('AIRTEL', 'Airtel Money'),
    ]

    amount = forms.DecimalField(
        label='Amount to Deposit (UGX)',
        min_value=1000,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum UGX 1,000',
            'step': '1000'
        })
    )
    phone_number = forms.CharField(
        label='Mobile Money Number',
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '256XXXXXXXXX'
        })
    )
    provider = forms.ChoiceField(
        label='Mobile Network',
        choices=PROVIDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            # Try to get phone number from user profile
            phone_number = getattr(self.user, 'phone_number', None)
            if not phone_number and hasattr(self.user, 'userprofile'):
                phone_number = self.user.userprofile.phone_number
            
            if phone_number:
                self.fields['phone_number'].initial = phone_number

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()
        phone = re.sub(r'[^0-9]', '', phone)  # Remove non-digit characters

        # Validate Uganda phone numbers
        if not phone.startswith(('25677', '25678', '25676', '25675', '25670', '25671')):
            raise forms.ValidationError(
                "Please enter a valid Uganda mobile money number starting with 256")

        if len(phone) != 12:
            raise forms.ValidationError(
                "Phone number must be 12 digits including country code")

        return phone

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        # Check against deposit limits
        if amount < 1000:
            raise forms.ValidationError("Minimum deposit amount is UGX 1,000")
        if amount > 5000000:
            raise forms.ValidationError("Maximum single deposit is UGX 5,000,000")

        # Check daily limit if user is provided
        if self.user:
            today = timezone.now().date()
            today_deposits = Transaction.objects.filter(
                user=self.user,
                transaction_type='mobile_money_deposit',
                date__date=today,
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            if today_deposits + amount > 10000000:  # UGX 10M daily limit
                remaining = 10000000 - today_deposits
                raise forms.ValidationError(
                    f"This deposit would exceed your daily limit. You can deposit up to UGX {remaining:,.0f} today"
                )

        return amount


class MobileMoneyWithdrawalForm(forms.Form):
    amount = forms.DecimalField(
        label='Amount to Withdraw (UGX)',
        min_value=1000,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum UGX 1,000',
            'step': '1000'
        })
    )
    phone_number = forms.CharField(
        label='Mobile Money Number',
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '256XXXXXXXXX'
        })
    )
    provider = forms.ChoiceField(
        label='Mobile Network',
        choices=MobileMoneyDepositForm.PROVIDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)

        if self.user:
            # Try to get phone number from user profile
            phone_number = getattr(self.user, 'phone_number', None)
            if not phone_number and hasattr(self.user, 'userprofile'):
                phone_number = self.user.userprofile.phone_number
            
            if phone_number:
                self.fields['phone_number'].initial = phone_number

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if not self.account:
            return amount

        if amount < 1000:
            raise forms.ValidationError("Minimum withdrawal amount is UGX 1,000")
        if amount > 3000000:
            raise forms.ValidationError("Maximum single withdrawal is UGX 3,000,000")
        if amount > self.account.available_balance:
            raise forms.ValidationError("Insufficient funds for this withdrawal")

        # Check daily withdrawal limit
        today = timezone.now().date()
        today_withdrawals = Transaction.objects.filter(
            user=self.user,
            transaction_type='mobile_money_withdrawal',
            date__date=today,
            status='completed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        if today_withdrawals + amount > 5000000:  # UGX 5M daily limit
            remaining = 5000000 - today_withdrawals
            raise forms.ValidationError(
                f"This withdrawal would exceed your daily limit. You can withdraw up to UGX {remaining:,.0f} today"
            )

        return amount

    def clean_phone_number(self):
        return MobileMoneyDepositForm.clean_phone_number(self)
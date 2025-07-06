from django import forms
from account.models import KYC
from django.forms import ImageField, FileInput, DateInput, TextInput
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import StaffPermission


class DateInput(forms.DateInput):
    input_type = 'date'


class KYCForm(forms.ModelForm):
    identity_image = ImageField(widget=FileInput)
    image = ImageField(widget=FileInput)
    signature = ImageField(widget=FileInput)

    class Meta:
        model = KYC
        fields = ['full_name', 'image', 'marrital_status', 'gender', 'identity_type',
                  'identity_image', 'date_of_birth', 'signature', 'country', 'state', 'city', 'mobile', 'fax']
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Full Name"}),
            "mobile": forms.TextInput(attrs={"placeholder": "Mobile Number"}),
            "fax": forms.TextInput(attrs={"placeholder": "Fax Number"}),
            "country": forms.TextInput(attrs={"placeholder": "Country"}),
            "state": forms.TextInput(attrs={"placeholder": "State"}),
            "city": forms.TextInput(attrs={"placeholder": "City"}),
            'date_of_birth': DateInput
        }        
        
        
class StaffCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('SUPPORT', 'Support Staff'),
        ('LOAN_OFFICER', 'Loan Officer'),
        ('ACCOUNT_MANAGER', 'Account Manager'),
        ('ADMIN', 'System Admin'),
    )
    
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    can_view_balances = forms.BooleanField(
        required=False,
        help_text="Can view user account balances"
    )
    can_reset_passwords = forms.BooleanField(
        required=False,
        help_text="Can reset user passwords"
    )
    can_approve_loans = forms.BooleanField(
        required=False,
        help_text="Can approve loan applications"
    )
    can_approve_withdrawals = forms.BooleanField(
        required=False,
        help_text="Can approve withdrawal requests"
    )
    can_edit_kyc = forms.BooleanField(
        required=False,
        help_text="Can edit and approve KYC documents"
    )
    can_manage_staff = forms.BooleanField(
        required=False,
        help_text="Can manage other staff members (admin only)"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # Gives access to admin site if needed
        if commit:
            user.save()
            # Create staff permissions
            StaffPermission.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                can_view_balances=self.cleaned_data['can_view_balances'],
                can_reset_passwords=self.cleaned_data['can_reset_passwords'],
                can_approve_loans=self.cleaned_data['can_approve_loans'],
                can_approve_withdrawals=self.cleaned_data['can_approve_withdrawals'],
                can_edit_kyc=self.cleaned_data['can_edit_kyc'],
                can_manage_staff=self.cleaned_data['can_manage_staff']
            )
        return user

class StaffEditForm(UserChangeForm):
    ROLE_CHOICES = (
        ('SUPPORT', 'Support Staff'),
        ('LOAN_OFFICER', 'Loan Officer'),
        ('ACCOUNT_MANAGER', 'Account Manager'),
        ('ADMIN', 'System Admin'),
    )
    
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    can_view_balances = forms.BooleanField(required=False)
    can_reset_passwords = forms.BooleanField(required=False)
    can_approve_loans = forms.BooleanField(required=False)
    can_approve_withdrawals = forms.BooleanField(required=False)
    can_edit_kyc = forms.BooleanField(required=False)
    can_manage_staff = forms.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the password field from the form
        self.fields.pop('password', None)
        
        # Initialize permissions from staff_permissions if they exist
        if hasattr(self.instance, 'staff_permissions'):
            staff_perms = self.instance.staff_permissions
            self.fields['role'].initial = staff_perms.role
            self.fields['can_view_balances'].initial = staff_perms.can_view_balances
            self.fields['can_reset_passwords'].initial = staff_perms.can_reset_passwords
            self.fields['can_approve_loans'].initial = staff_perms.can_approve_loans
            self.fields['can_approve_withdrawals'].initial = staff_perms.can_approve_withdrawals
            self.fields['can_edit_kyc'].initial = staff_perms.can_edit_kyc
            self.fields['can_manage_staff'].initial = staff_perms.can_manage_staff

class StaffPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')